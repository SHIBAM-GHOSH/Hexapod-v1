import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import time
from ahrs.filters import Madgwick

# --------------------------------------------------
# MILITARY DARK MODE THEME
# --------------------------------------------------
plt.style.use('dark_background')

# Military color scheme: Dark olive, tactical green, combat gray
MILITARY_COLORS = {
    'bg': '#000000',      # Pure black background
    'grid': '#ffffff',    # White grid
    'text': '#00ff00',    # Parrot green
    'cube': '#ffff00',    # Yellow cube
}  
     
# Apply custom colors
plt.rcParams['figure.facecolor'] = MILITARY_COLORS['bg']
plt.rcParams['axes.facecolor'] = MILITARY_COLORS['bg']
plt.rcParams['axes.edgecolor'] = MILITARY_COLORS['text']
plt.rcParams['text.color'] = MILITARY_COLORS['text']
plt.rcParams['xtick.color'] = MILITARY_COLORS['text']
plt.rcParams['ytick.color'] = MILITARY_COLORS['text']
plt.rcParams['grid.color'] = MILITARY_COLORS['grid']
plt.rcParams['font.size'] = 10
plt.rcParams['font.weight'] = 'bold'

# --------------------------------------------------
# 1. LOAD CSV
# --------------------------------------------------
df = pd.read_csv("imu30_min.csv")

time_s = df["time_seconds"].values
dt = np.mean(np.diff(time_s))

# Accelerometer: g → m/s²
accel = df[["accel_x_g", "accel_y_g", "accel_z_g"]].values * 9.81

# GYRO BIAS CALIBRATION (use first 50 samples at rest to estimate bias)
gyro_raw_dps = df[["gyro_x_dps", "gyro_y_dps", "gyro_z_dps"]].values
gyro_bias = np.mean(gyro_raw_dps[:50], axis=0)  # Mean of first 50 samples
print(f"Detected gyro bias: X={gyro_bias[0]:.4f}, Y={gyro_bias[1]:.4f}, Z={gyro_bias[2]:.4f} deg/s")

# Remove bias and convert to rad/s
gyro = np.deg2rad(gyro_raw_dps - gyro_bias)

# Detect magnetometer columns (if present) and prepare array
mag_cols = [c for c in df.columns if c.lower().startswith('mag') or c.lower().startswith('magnet')]
has_mag = len(mag_cols) >= 3
if has_mag:
    mag = df[mag_cols[:3]].values

# --------------------------------------------------
# 2. MADGWICK FILTER (IMU MODE)
# --------------------------------------------------
madgwick = Madgwick(sampleperiod=dt, beta=0.04)  # Lower beta = trust accelerometer more, gyro less

Q = np.zeros((len(time_s), 4))
Q[0] = [1.0, 0.0, 0.0, 0.0]

for i in range(1, len(time_s)):
    Q[i] = madgwick.updateIMU(Q[i-1], gyr=gyro[i], acc=accel[i])

# --------------------------------------------------
# 3. QUATERNION → ROTATION MATRIX & EULER ANGLES
# --------------------------------------------------
def quat_to_rotmat(q):
    w, x, y, z = q
    return np.array([
        [1 - 2*(y*y + z*z), 2*(x*y - z*w),     2*(x*z + y*w)],
        [2*(x*y + z*w),     1 - 2*(x*x + z*z), 2*(y*z - x*w)],
        [2*(x*z - y*w),     2*(y*z + x*w),     1 - 2*(x*x + y*y)]
    ])
#kya hoga iss code ka 
def quat_to_euler(q):
    """Convert quaternion to Euler angles (roll, pitch, yaw) in degrees"""   
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
# 4. SETUP 3D WINDOW (MILITARY TACTICAL DISPLAY)
# --------------------------------------------------
plt.ion()                     #  enable interactive mode
fig = plt.figure(figsize=(12, 10), facecolor=MILITARY_COLORS['bg'])
fig.suptitle('BODY ORIENTATION - HEXAPOD IMU', 
             fontsize=14, color=MILITARY_COLORS['text'], fontweight='bold')
ax = fig.add_subplot(111, projection="3d", facecolor=MILITARY_COLORS['bg'])
ax.grid(True, color=MILITARY_COLORS['grid'], linestyle='-', linewidth=0.8, alpha=0.9)

# Set 3D pane colors to black
ax.xaxis.pane.set_facecolor(MILITARY_COLORS['bg'])
ax.yaxis.pane.set_facecolor(MILITARY_COLORS['bg'])
ax.zaxis.pane.set_facecolor(MILITARY_COLORS['bg'])
  
plt.show()                    # force window to appear

# Flat rectangular definition (like a board/plate) - hexapod body shape
cube = np.array([
    [-0.4, -0.6, -0.1],   # bottom front left
    [ 0.4, -0.6, -0.1],   # bottom front right
    [ 0.4,  0.6, -0.1],   # bottom back right
    [-0.4,  0.6, -0.1],   # bottom back left
    [-0.4, -0.6,  0.1],   # top front left
    [ 0.4, -0.6,  0.1],   # top front right
    [ 0.4,  0.6,  0.1],   # top back right
    [-0.4,  0.6,  0.1]    # top back left
])

# Define cube faces for filled surfaces with different colors
cube_faces = [
    [0, 1, 2, 3],  # bottom
    [4, 5, 6, 7],  # top
    [0, 1, 5, 4],  # front
    [2, 3, 7, 6],  # back
    [0, 3, 7, 4],  # left
    [1, 2, 6, 5]   # right
]

# Different colors for each face (RGB format)
face_colors = [
    '#ff0000',  # bottom - Red
    '#00ff00',  # top - Green
    '#0000ff',  # front - Blue
    '#ffff00',  # back - Yellow
    '#ff00ff',  # left - Magenta
    '#00ffff'   # right - Cyan
]

# --------------------------------------------------
# 5. ANIMATION LOOP (CSV PLAYBACK)
# --------------------------------------------------
# record wall-clock start time so we can show elapsed time while playing back
start_time = time.time()

for i in range(0, len(Q), 2):
    ax.cla()

    # elapsed wall-clock time since playback started
    elapsed = time.time() - start_time

    R = quat_to_rotmat(Q[i])
    rotated = cube @ R.T

    # Draw cube with filled transparent faces
    from mpl_toolkits.mplot3d.art3d import Poly3DCollection
    
    # Draw cube faces with different colors
    faces = []
    face_cols = []
    for idx, face in enumerate(cube_faces):
        face_vertices = [rotated[face]]
        faces.extend(face_vertices)
        face_cols.append(face_colors[idx])
    
    cube_collection = Poly3DCollection(faces, alpha=0.6, facecolors=face_cols, edgecolors='white', linewidth=1.5)
    ax.add_collection3d(cube_collection)

    # Draw body axes (multi-color: red, green, blue)
    ax.quiver(0,0,0, *R[:,0], color='#ff0000', linewidth=3, arrow_length_ratio=0.2)  # X (roll) - Red
    ax.quiver(0,0,0, *R[:,1], color='#00ff00', linewidth=3, arrow_length_ratio=0.2)  # Y (pitch) - Green
    ax.quiver(0,0,0, *R[:,2], color='#0000ff', linewidth=3, arrow_length_ratio=0.2)  # Z (yaw) - Blue

    ax.set_xlim([-1.2, 1.2])
    ax.set_ylim([-1.2, 1.2])
    ax.set_zlim([-1.2, 1.2])
    ax.set_box_aspect([1,1,1])
    
    # Calculate rotation angles
    euler_angles = quat_to_euler(Q[i])
    roll, pitch, yaw = euler_angles
    
    # Detailed body orientation display
    ax.set_title(f"BODY ORIENTATION | CSV_TIME: {time_s[i]:.2f}s | ELAPSED: {elapsed:.2f}s | FRAME: {i//2}\n" +
                 f"ROLL: {roll:.1f}° | PITCH: {pitch:.1f}° | YAW: {yaw:.1f}°",
                 color=MILITARY_COLORS['text'], fontsize=10, fontweight='bold', pad=20)
    
    # Axis labels with rotation amounts
    ax.set_xlabel(f'X-AXIS (ROLL: {roll:.1f}°)', color='#ff0000', fontweight='bold')
    ax.set_ylabel(f'Y-AXIS (PITCH: {pitch:.1f}°)', color='#00ff00', fontweight='bold')
    ax.set_zlabel(f'Z-AXIS (YAW: {yaw:.1f}°)', color='#0000ff', fontweight='bold')

    # Print current IMU row to console (updates in-place)
    acc_row = accel[i]
    gyro_row_dps = gyro_raw_dps[i]
    status = (f"CSV_TIME: {time_s[i]:.2f}s | ELAPSED: {elapsed:.2f}s | "
              f"Accel(m/s²): x={acc_row[0]:.2f}, y={acc_row[1]:.2f}, z={acc_row[2]:.2f} | "
              f"Gyro(deg/s): x={gyro_row_dps[0]:.2f}, y={gyro_row_dps[1]:.2f}, z={gyro_row_dps[2]:.2f}")
    if has_mag:
        mag_row = mag[i]
        status += f" | Mag: x={mag_row[0]:.2f}, y={mag_row[1]:.2f}, z={mag_row[2]:.2f}"
    print(status, end='\r', flush=True)
    plt.pause(dt)

# Keep window alive after animation
plt.ioff()
plt.show()
