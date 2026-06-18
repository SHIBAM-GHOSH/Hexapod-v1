import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.animation import FuncAnimation
import time

# -----------------------------
# Load IMU data
# -----------------------------
data = pd.read_csv("imu2.csv")

# -----------------------------
# Compute Roll & Pitch (radians)
# -----------------------------
def compute_orientation(ax, ay, az):
    roll = np.arctan2(ay, az)
    pitch = np.arctan2(-ax, np.sqrt(ay**2 + az**2))
    return roll, pitch

# -----------------------------
# Matplotlib setup
# -----------------------------
fig, ax = plt.subplots()
ax.set_xlim(-2, 2)
ax.set_ylim(-2, 2)
ax.set_aspect('equal')
ax.set_title("Real-Time IMU Orientation Visualization")

# Rectangle (centered at origin)
rect_width = 1.0
rect_height = 0.5
rectangle = plt.Rectangle(
    (-rect_width/2, -rect_height/2),
    rect_width,
    rect_height,
    fill=False,
    linewidth=2
)
ax.add_patch(rectangle)

# -----------------------------
# Update function for animation
# -----------------------------
index = 0

def update(frame):
    global index
    if index >= len(data):
        return rectangle,

    ax_g = data.loc[index, "accel_x_g"]
    ay_g = data.loc[index, "accel_y_g"]
    az_g = data.loc[index, "accel_z_g"]

    roll, pitch = compute_orientation(ax_g, ay_g, az_g)

    # Combine roll & pitch visually (2D simplification)
    angle_deg = np.degrees(roll + pitch)

    rectangle.set_angle(angle_deg)

    index += 1
    time.sleep(0.05)  # simulate real-time sensor delay

    return rectangle,

# -----------------------------
# Start animation
# -----------------------------
ani = FuncAnimation(fig, update, interval=50)
plt.show()
