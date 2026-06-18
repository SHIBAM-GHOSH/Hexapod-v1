@echo off
REM Quick launcher for RPLiDAR Viewer

echo Starting RPLiDAR Viewer...

REM This command ensures the script runs within the correct conda environment
conda run -n base python lidar_viewer.py

if %errorlevel% neq 0 (
    echo.
    echo ERROR: Failed to run the application!
    echo.
    echo Make sure you have installed the dependencies by running:
    echo   install.bat
    echo.
    echo Or by running:
    echo   conda run -n base pip install -r requirements.txt
    echo.
    pause
)
