"""
RPLiDAR A1M8 Viewer for Windows
Simple GUI application to visualize LiDAR data in real-time.
"""

import colorsys
import sys
import time
from typing import Optional

import numpy as np

from PySide6.QtCore import Qt, QTimer
from PySide6.QtWidgets import (
    QApplication,
    QComboBox,
    QDoubleSpinBox,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QMainWindow,
    QPushButton,
    QSpinBox,
    QStatusBar,
    QVBoxLayout,
    QWidget,
)

try:
    from rplidar import RPLidar
    from serial.tools import list_ports

    HAS_RPLIDAR = True
except ImportError:
    HAS_RPLIDAR = False
    print("Warning: rplidar library not installed. Install with: pip install rplidar-roboticia")

try:
    import pyqtgraph as pg
    import pyqtgraph.opengl as gl
    from OpenGL import GL  # noqa: F401

    pg.setConfigOption("background", "k")
    pg.setConfigOption("foreground", "w")
    HAS_PYQTGRAPH = True
    PYQTGRAPH_IMPORT_ERROR = ""
except Exception as e:
    HAS_PYQTGRAPH = False
    PYQTGRAPH_IMPORT_ERROR = str(e)
    print(f"Warning: 3D libraries not available ({e}). 3D view will not be available.")


if HAS_PYQTGRAPH:
    class LidarCanvas3D(gl.GLViewWidget):
        """3D canvas for LiDAR point cloud rendering."""

        def __init__(self, parent=None):
            super().__init__(parent=parent)
            self.setBackgroundColor((0, 0, 0, 255))
            self.setCameraPosition(distance=20, elevation=30, azimuth=45)

            self.grid = gl.GLGridItem()
            self.grid.setSize(x=24, y=24)
            self.grid.setSpacing(x=1, y=1)
            self.addItem(self.grid)

            # LiDAR body marker at origin
            lidar_mesh = gl.MeshData.cylinder(rows=24, cols=48, radius=[0.12, 0.12], length=0.25)
            self.lidar_body = gl.GLMeshItem(
                meshdata=lidar_mesh,
                smooth=True,
                color=(0.75, 0.75, 0.75, 1.0),
                shader="shaded",
                drawEdges=False,
            )
            self.lidar_body.translate(0.0, 0.0, 0.125)
            self.addItem(self.lidar_body)

            self.scatter = gl.GLScatterPlotItem(size=6, color=(0, 1, 1, 1), pxMode=True)
            self.addItem(self.scatter)

        def set_points(self, points: np.ndarray, colors: np.ndarray):
            self.scatter.setData(pos=points, color=colors)

        def set_point_size(self, size: int):
            self.scatter.setSize(size)


class LidarViewer(QMainWindow):
    """Main application window for RPLiDAR viewer."""

    def __init__(self):
        super().__init__()

        self.lidar: Optional[RPLidar] = None
        self.connected = False
        self.scanning = False

        self.current_scan_xy = np.empty((0, 2), dtype=np.float32)
        self.height_layers = 80
        # Reduced by ~60% from prior default total wall height (~3.12m -> ~1.25m).
        self.wall_height_m = 1.25
        self.point_cloud = np.empty((0, 3), dtype=np.float32)
        self.point_colors = np.empty((0, 4), dtype=np.float32)

        self.scan_count = 0
        self.point_count = 0
        self.total_points = 0
        self.scan_rate = 0.0
        self.last_scan_time = 0.0

        self.setWindowTitle("RPLiDAR A1M8 Viewer")
        self.setGeometry(100, 100, 1100, 760)
        self._create_ui()

        self.update_timer = QTimer()
        self.update_timer.timeout.connect(self._update_stats_labels)
        self.update_timer.start(50)

    def _create_ui(self):
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QHBoxLayout(central_widget)

        control_panel = self._create_control_panel()
        main_layout.addWidget(control_panel, stretch=0)

        if not HAS_PYQTGRAPH:
            error_label = QLabel(
                "Error: 3D libraries are not available.\n"
                "Install with: pip install pyqtgraph PyOpenGL PyOpenGL_accelerate\n"
                f"Detail: {PYQTGRAPH_IMPORT_ERROR}"
            )
            error_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            main_layout.addWidget(error_label, stretch=1)
            return

        self.canvas = LidarCanvas3D()
        main_layout.addWidget(self.canvas, stretch=1)

        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        self.status_bar.showMessage("Ready - Select COM port, then Connect")

    def _create_control_panel(self) -> QWidget:
        panel = QWidget()
        panel.setMaximumWidth(300)
        layout = QVBoxLayout(panel)

        conn_group = QGroupBox("Connection")
        conn_layout = QVBoxLayout()

        port_layout = QHBoxLayout()
        port_layout.addWidget(QLabel("Port:"))
        self.port_combo = QComboBox()
        self.port_combo.setEditable(True)

        available_ports = list_ports.comports() if HAS_RPLIDAR else []
        port_names = [port.device for port in available_ports]
        if port_names:
            self.port_combo.addItems(port_names)
            for port in available_ports:
                if "CP210x" in port.description or "USB Serial" in port.description:
                    self.port_combo.setCurrentText(port.device)
                    break
        else:
            self.port_combo.addItem("COM3")
        port_layout.addWidget(self.port_combo)
        conn_layout.addLayout(port_layout)

        self.connect_button = QPushButton("Connect")
        self.connect_button.clicked.connect(self._toggle_connection)
        conn_layout.addWidget(self.connect_button)

        self.scan_button = QPushButton("Start Scan")
        self.scan_button.clicked.connect(self._toggle_scan)
        self.scan_button.setEnabled(False)
        conn_layout.addWidget(self.scan_button)

        conn_group.setLayout(conn_layout)
        layout.addWidget(conn_group)

        mouse_help = QLabel("Mouse controls: left-drag rotate, wheel zoom, right-drag pan")
        mouse_help.setWordWrap(True)
        layout.addWidget(mouse_help)

        display_group = QGroupBox("Display Settings")
        display_layout = QVBoxLayout()

        dist_layout = QHBoxLayout()
        dist_layout.addWidget(QLabel("Obstacle Range (m):"))
        self.distance_spin = QSpinBox()
        self.distance_spin.setRange(1, 20)
        self.distance_spin.setValue(4)
        dist_layout.addWidget(self.distance_spin)
        display_layout.addLayout(dist_layout)

        size_layout = QHBoxLayout()
        size_layout.addWidget(QLabel("Point Size:"))
        self.size_spin = QSpinBox()
        self.size_spin.setRange(2, 16)
        self.size_spin.setValue(6)
        self.size_spin.valueChanged.connect(self._on_size_changed)
        size_layout.addWidget(self.size_spin)
        display_layout.addLayout(size_layout)

        wall_height_layout = QHBoxLayout()
        wall_height_layout.addWidget(QLabel("Wall Height (m):"))
        self.wall_height_spin = QDoubleSpinBox()
        self.wall_height_spin.setRange(0.2, 3.0)
        self.wall_height_spin.setSingleStep(0.05)
        self.wall_height_spin.setValue(self.wall_height_m)
        self.wall_height_spin.valueChanged.connect(self._on_wall_height_changed)
        wall_height_layout.addWidget(self.wall_height_spin)
        display_layout.addLayout(wall_height_layout)

        height_layout = QHBoxLayout()
        height_layout.addWidget(QLabel("Height Layers:"))
        self.height_spin = QSpinBox()
        self.height_spin.setRange(2, 120)
        self.height_spin.setValue(self.height_layers)
        self.height_spin.valueChanged.connect(self._on_height_changed)
        height_layout.addWidget(self.height_spin)
        display_layout.addLayout(height_layout)

        display_group.setLayout(display_layout)
        layout.addWidget(display_group)

        stats_group = QGroupBox("Statistics")
        stats_layout = QVBoxLayout()
        self.status_label = QLabel("Status: Disconnected")
        self.scans_label = QLabel("Scans: 0")
        self.points_label = QLabel("Total Points: 0")
        self.rate_label = QLabel("Rate: 0.0 Hz")
        stats_layout.addWidget(self.status_label)
        stats_layout.addWidget(self.scans_label)
        stats_layout.addWidget(self.points_label)
        stats_layout.addWidget(self.rate_label)
        stats_group.setLayout(stats_layout)
        layout.addWidget(stats_group)

        self.clear_button = QPushButton("Clear Display")
        self.clear_button.clicked.connect(self._clear_display)
        layout.addWidget(self.clear_button)

        layout.addStretch()
        return panel

    def _toggle_connection(self):
        if not HAS_RPLIDAR:
            self.status_bar.showMessage("Error: rplidar library not installed.")
            return
        if not HAS_PYQTGRAPH:
            self.status_bar.showMessage("Error: 3D libraries are not installed.")
            return

        if self.connected:
            self._disconnect()
        else:
            self._connect()

    def _connect(self):
        port = self.port_combo.currentText()
        try:
            self.status_bar.showMessage(f"Connecting to {port}...")
            self.lidar = RPLidar(port, baudrate=115200, timeout=3)

            info = self.lidar.get_info()
            model = info.get("model", "Unknown")
            firmware = info.get("firmware", (0, 0))

            self.connected = True
            self.connect_button.setText("Disconnect")
            self.scan_button.setEnabled(True)
            self.port_combo.setEnabled(False)

            self.status_label.setText("Status: Connected")
            self.status_bar.showMessage(f"Connected to {model} (FW: {firmware[0]}.{firmware[1]})")
        except Exception as e:
            self.status_bar.showMessage(f"Connection failed: {e}")
            self.lidar = None
            self.connected = False

    def _disconnect(self):
        if self.scanning:
            self._stop_scan()

        if self.lidar:
            try:
                self.lidar.stop()
                self.lidar.disconnect()
            except Exception:
                pass
            self.lidar = None

        self.connected = False
        self.connect_button.setText("Connect")
        self.scan_button.setEnabled(False)
        self.port_combo.setEnabled(True)
        self.status_label.setText("Status: Disconnected")
        self.status_bar.showMessage("Disconnected")

    def _toggle_scan(self):
        if self.scanning:
            self._stop_scan()
        else:
            self._start_scan()

    def _start_scan(self):
        if not self.lidar:
            return

        try:
            self.lidar.start_motor()
            time.sleep(1)
            self.scan_iterator = self.lidar.iter_scans(max_buf_meas=2000)

            self.scanning = True
            self.scan_button.setText("Stop Scan")
            self.status_label.setText("Status: Scanning")
            self.status_bar.showMessage("Scanning started")

            self.scan_timer = QTimer()
            self.scan_timer.timeout.connect(self._read_scan)
            self.scan_timer.start(30)
        except Exception as e:
            self.status_bar.showMessage(f"Scan failed: {e}")
            self.scanning = False

    def _stop_scan(self):
        self.scanning = False

        if hasattr(self, "scan_timer"):
            self.scan_timer.stop()

        if self.lidar:
            try:
                self.lidar.stop()
                self.lidar.stop_motor()
            except Exception:
                pass

        self.scan_button.setText("Start Scan")
        self.status_label.setText("Status: Connected")
        self.status_bar.showMessage("Scanning stopped")

    def _read_scan(self):
        if not self.scanning or not self.lidar:
            return

        try:
            scan = next(self.scan_iterator, None)
            if not scan:
                return

            max_dist_m = self.distance_spin.value()
            min_dist_m = 0.10
            min_quality = 10
            angle_bin_deg = 1.0
            nearest_by_angle_bin = {}
            for quality, angle_deg, distance_mm in scan:
                distance_m = distance_mm / 1000.0
                if quality < min_quality:
                    continue
                if not (min_dist_m <= distance_m <= max_dist_m):
                    continue

                angle_key = int(angle_deg // angle_bin_deg)
                prev = nearest_by_angle_bin.get(angle_key)
                if prev is None or distance_m < prev[1]:
                    nearest_by_angle_bin[angle_key] = (angle_deg, distance_m)

            points = []
            for angle_deg, distance_m in nearest_by_angle_bin.values():
                angle_rad = np.deg2rad(angle_deg)
                points.append((distance_m * np.cos(angle_rad), distance_m * np.sin(angle_rad)))

            if not points:
                return

            self.scan_count += 1
            self.point_count = len(points)

            current_time = time.time()
            if self.last_scan_time > 0:
                dt = current_time - self.last_scan_time
                if dt > 0:
                    self.scan_rate = 1.0 / dt
            self.last_scan_time = current_time

            self.current_scan_xy = np.array(points, dtype=np.float32)
            self._rebuild_cloud()
        except StopIteration:
            pass
        except Exception as e:
            self.status_bar.showMessage(f"Read error: {e}")

    def _rebuild_cloud(self):
        if self.current_scan_xy.size == 0:
            self.point_cloud = np.empty((0, 3), dtype=np.float32)
            self.point_colors = np.empty((0, 4), dtype=np.float32)
            self.total_points = 0
            if HAS_PYQTGRAPH:
                self.canvas.set_points(self.point_cloud, self.point_colors)
            return

        layers = []
        color_layers = []
        rainbow = self._generate_rainbow_colors(self.height_layers)

        # Keep the cloud stable in Z: one live 2D scan extruded to fixed height.
        z_levels = np.linspace(0.0, self.wall_height_m, self.height_layers, dtype=np.float32)
        for z_idx, z_level in enumerate(z_levels):
            z = np.full((self.current_scan_xy.shape[0], 1), z_level, dtype=np.float32)
            layers.append(np.hstack((self.current_scan_xy, z)))
            color_layers.append(np.tile(rainbow[z_idx], (self.current_scan_xy.shape[0], 1)))

        self.point_cloud = np.vstack(layers).astype(np.float32, copy=False)
        self.point_colors = np.vstack(color_layers).astype(np.float32, copy=False)
        self.total_points = self.point_cloud.shape[0]

        if HAS_PYQTGRAPH:
            self.canvas.set_points(self.point_cloud, self.point_colors)

    def _generate_rainbow_colors(self, count: int) -> np.ndarray:
        if count <= 1:
            return np.array([[0.0, 1.0, 1.0, 1.0]], dtype=np.float32)

        hues = np.linspace(0.67, 0.0, count, dtype=np.float32)
        rgba = np.empty((count, 4), dtype=np.float32)
        for i, h in enumerate(hues):
            r, g, b = colorsys.hsv_to_rgb(float(h), 1.0, 1.0)
            rgba[i] = (r, g, b, 1.0)
        return rgba

    def _update_stats_labels(self):
        self.scans_label.setText(f"Scans: {self.scan_count}")
        self.points_label.setText(f"Total Points: {self.total_points}")
        self.rate_label.setText(f"Rate: {self.scan_rate:.1f} Hz")

    def _clear_display(self):
        self.current_scan_xy = np.empty((0, 2), dtype=np.float32)
        self.point_cloud = np.empty((0, 3), dtype=np.float32)
        self.point_colors = np.empty((0, 4), dtype=np.float32)
        self.scan_count = 0
        self.point_count = 0
        self.total_points = 0
        self.last_scan_time = 0.0
        self.scan_rate = 0.0
        if HAS_PYQTGRAPH:
            self.canvas.set_points(self.point_cloud, self.point_colors)

    def _on_size_changed(self, value):
        if HAS_PYQTGRAPH:
            self.canvas.set_point_size(value)

    def _on_wall_height_changed(self, value):
        self.wall_height_m = value
        self._rebuild_cloud()

    def _on_height_changed(self, value):
        self.height_layers = value
        self._rebuild_cloud()

    def closeEvent(self, event):
        if self.connected:
            self._disconnect()
        event.accept()


def main():
    print("=" * 60)
    print("RPLiDAR A1M8 Viewer for Windows")
    print("=" * 60)

    missing_libs = []
    if not HAS_RPLIDAR:
        missing_libs.append("rplidar-roboticia")
    if not HAS_PYQTGRAPH:
        missing_libs.append("pyqtgraph / PyOpenGL")

    if missing_libs:
        print("\nERROR: One or more required libraries were not found!")
        for lib in missing_libs:
            print(f" - Missing: {lib}")
        print("\nPlease install the missing libraries by running:")
        print("   pip install -r requirements.txt")
        print("   pip install PyOpenGL PyOpenGL_accelerate")
        print(f"\nDetail: {PYQTGRAPH_IMPORT_ERROR}")
        print("\nPress Enter to exit...")
        input()
        return

    app = QApplication(sys.argv)
    window = LidarViewer()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
