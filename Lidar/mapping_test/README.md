# RPLiDAR A1M8 Viewer for Windows

A simple GUI application to visualize real-time LiDAR data from the RPLiDAR A1M8 sensor on Windows.

## Features

- **Real-time visualization** of LiDAR scans
- **Interactive GUI** with PySide6
- **Configurable display settings**
  - Adjustable range (1-20 meters)
  - Point size control
  - Grid overlay
- **Connection statistics**
  - Scan count
  - Points per scan
  - Scan rate (Hz)
- **Easy port selection** for Windows COM ports

## Requirements

- Windows 10/11
- Python 3.8 or higher
- RPLiDAR A1M8 connected via USB

## Installation

### 1. Install Python
Download and install Python from [python.org](https://www.python.org/downloads/)
- Make sure to check "Add Python to PATH" during installation
### 1. Install Anaconda/Miniconda
Download and install the Anaconda Distribution (or Miniconda) from [anaconda.com](https://www.anaconda.com/products/distribution). This will manage the Python environment and all required libraries.

### 2. Install Dependencies

Open PowerShell or Command Prompt and move into the `mapping_test` folder:
```cmd
cd /d D:\CS_Projects\Lidar\mapping_test
```

Install required packages:
```cmd
python -m pip install -r requirements.txt
```

Or run the installer script:
```cmd
install.bat
```

## Usage

### 1. Connect the LiDAR
- Plug in your RPLiDAR A1M8 to a USB port
- Note the COM port (check Device Manager → Ports)
- Common ports: COM3, COM4, COM5, COM6

### 2. Run the Application

```cmd
cd /d D:\CS_Projects\Lidar\mapping_test
python lidar_viewer.py
```

Or run:
```cmd
run_viewer.bat
```

Do not run `tempCodeRunnerFile.py`; it is a temporary editor file and not the application.

This script ensures the application runs inside the correct Conda environment. If this fails, see the Troubleshooting section.

### 3. Using the GUI

1. **Select COM Port** - Choose your LiDAR's port from dropdown
2. **Click "Connect"** - Establish connection to the LiDAR
3. **Click "Start Scan"** - Begin scanning and visualization
4. **Adjust Settings**:
   - **Range**: Maximum distance to display (meters)
   - **Point Size**: Size of drawn points (pixels)
5. **Click "Stop Scan"** when done
6. **Click "Disconnect"** to close the connection

### Controls

- **Connect/Disconnect** - Connect to/from LiDAR
- **Start/Stop Scan** - Control scanning
- **Range** - Adjust visualization range (1-20m)
- **Point Size** - Adjust point drawing size (1-10px)
- **Clear Display** - Clear current visualization

## Troubleshooting

### 'conda' is not recognized as an internal or external command
This means Conda is not in your system's PATH. You must run the application from an **Anaconda Prompt**.
1. Open 'Anaconda Prompt' from your Start Menu.
2. Navigate to the project folder. If your project is on a different drive (e.g., the `D:` drive), you must also change the drive. The easiest way is to use the `/d` switch.
   ```cmd
   cd /d D:\path\to\mapping_test
   ```
3. Run the launcher script from that directory:
   ```cmd
   .\run_viewer.bat
   ```

### "rplidar library not found"
```cmd
pip install rplidar-roboticia
```

### "Permission denied" or "Access denied"
- Close any other program using the LiDAR
- Try a different USB port
- Restart your computer

### "Cannot connect to COM port"
1. Open Device Manager (Windows key + X → Device Manager)
2. Expand "Ports (COM & LPT)"
3. Find "USB Serial Port" or "Silicon Labs CP210x"
4. Note the COM number (e.g., COM5)
5. Use that COM port in the application

### LiDAR not spinning
- The motor starts automatically when you click "Start Scan"
- Make sure the LiDAR has power (USB connection)
- Try disconnecting and reconnecting

### No data appearing
- Check that the correct COM port is selected
- Make sure no other program is using the LiDAR
- Try stopping and starting the scan again
- Check the statistics panel for scan count

## Technical Details

### Supported LiDAR
- **RPLiDAR A1M8** (primary target)
- Also works with: A1, A2, A3

### Specifications
- **Update Rate**: 20 Hz GUI refresh
- **Scan Rate**: 5-10 Hz (depends on LiDAR model)
- **Range**: 0-12 meters (configurable up to 20m)
- **Points per Scan**: ~360 points

### COM Port Settings
- **Baud Rate**: 115200 (for A1M8)
- **Timeout**: 3 seconds

## Files

- `lidar_viewer.py` - Main application
- `requirements.txt` - Python dependencies
- `README.md` - This file

## License

Free to use and modify.

## Support

For issues or questions:
1. Check Device Manager for correct COM port
2. Verify LiDAR is powered on
3. Ensure no other software is using the LiDAR
4. Try different USB ports

---

**Note**: The first connection may take a few seconds while the LiDAR initializes.
