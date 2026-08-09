import asyncio
import websockets
import json
import threading
import numpy as np
import lcm
from collections import deque
from ahrs.filters import EKF

import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from mpu.mpu_data_t import mpu_data_t

LCM_URL = "udpm://239.255.76.67:7667?ttl=2"
LCM_CHANNEL = "/shatapadi/imu"
WS_PORT = 8080

# --------------------------------------------------
# 1. IMU STATE (EKF + EULER OUTPUT)
# --------------------------------------------------
class IMUState:
    def __init__(self):
        self.ekf = EKF()
        self.quaternion = np.array([1.0, 0.0, 0.0, 0.0])
        self.roll = 0.0
        self.pitch = 0.0
        self.yaw = 0.0
        self.last_timestamp = None
        self.gyro_buffer = deque(maxlen=50)
        self.gyro_bias = np.zeros(3)
        self.bias_calibrated = False

state = IMUState()

def quat_to_euler(q):
    w, x, y, z = q
    sinr_cosp = 2 * (w * x + y * z)
    cosr_cosp = 1 - 2 * (x * x + y * y)
    roll = np.arctan2(sinr_cosp, cosr_cosp)
    sinp = 2 * (w * y - z * x)
    pitch = np.arcsin(np.clip(sinp, -1, 1))
    siny_cosp = 2 * (w * z + x * y)
    cosy_cosp = 1 - 2 * (y * y + z * z)
    yaw = np.arctan2(siny_cosp, cosy_cosp)
    return np.degrees([roll, pitch, yaw])

# --------------------------------------------------
# 2. LCM HANDLER
# --------------------------------------------------
def imu_handler(channel, data):
    msg = mpu_data_t.decode(data)

    if state.last_timestamp is None:
        state.last_timestamp = msg.timestamp
        return

    dt = (msg.timestamp - state.last_timestamp) / 1e6
    state.last_timestamp = msg.timestamp

    if dt <= 0 or dt > 1.0:
        return

    gyro_raw = np.array([msg.gyro_x, msg.gyro_y, msg.gyro_z])

    if not state.bias_calibrated:
        state.gyro_buffer.append(gyro_raw)
        if len(state.gyro_buffer) >= 50:
            state.gyro_bias = np.mean(list(state.gyro_buffer), axis=0)
            state.bias_calibrated = True
            print(f"Gyro bias calibrated: X={state.gyro_bias[0]:.4f}, Y={state.gyro_bias[1]:.4f}, Z={state.gyro_bias[2]:.4f} deg/s")
        return

    gyro = np.deg2rad(gyro_raw - state.gyro_bias)
    accel = np.array([msg.accel_x, msg.accel_y, msg.accel_z]) * 9.81

    state.ekf.Dt = dt
    state.quaternion = state.ekf.update(state.quaternion, gyro, accel, dt=dt)
    state.roll, state.pitch, state.yaw = quat_to_euler(state.quaternion)

# --------------------------------------------------
# 3. LCM THREAD
# --------------------------------------------------
def lcm_thread():
    lc = lcm.LCM(LCM_URL)
    lc.subscribe(LCM_CHANNEL, imu_handler)
    print(f"LCM subscribed to '{LCM_CHANNEL}'")
    print("Calibrating gyro bias (50 samples)...")
    while True:
        lc.handle()

# --------------------------------------------------
# 4. WEBSOCKET SERVER
# --------------------------------------------------
clients = set()

async def handler(websocket):
    clients.add(websocket)
    print(f"Client connected! ({len(clients)} total)")
    try:
        async for _ in websocket:
            pass
    except websockets.ConnectionClosed:
        pass
    finally:
        clients.discard(websocket)
        print(f"Client disconnected. ({len(clients)} remaining)")

async def publish_loop():
    """Broadcast current IMU state to all WebSocket clients at ~50 Hz."""
    while True:
        if clients and state.bias_calibrated:
            payload = json.dumps({
                "heading": 0,
                "altitude": 0,
                "pitch": round(float(state.pitch), 2),
                "roll": round(float(state.roll), 2),
                "yaw": round(float(state.yaw), 2),
                "lat": 0,
                "lng": 0,
                "status": "online"
            })
            websockets.broadcast(clients, payload)
        await asyncio.sleep(0.02)  # 50 Hz

async def main():
    # Start LCM subscriber in a background thread
    t = threading.Thread(target=lcm_thread, daemon=True)
    t.start()

    async with websockets.serve(handler, "0.0.0.0", WS_PORT):
        print(f"WebSocket server running on ws://0.0.0.0:{WS_PORT}")
        await publish_loop()

asyncio.run(main())
