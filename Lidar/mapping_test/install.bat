@echo off
REM RPLiDAR Viewer Installer for Windows
REM This script installs all required dependencies

echo ================================================
echo RPLiDAR A1M8 Viewer - Windows Installer
echo ================================================
echo.

REM Check if Python is installed
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo ERROR: Python is not installed or not in PATH!
    echo.
    echo Please install Python from https://www.python.org/downloads/
    echo Make sure to check "Add Python to PATH" during installation
    echo.
    pause
    exit /b 1
)

echo Python found!
python --version
echo.

REM Upgrade pip
echo Upgrading pip...
python -m pip install --upgrade pip
echo.

REM Install requirements
echo Installing dependencies...
echo This may take a few minutes...
echo.

REM Check if conda is available to ensure installation in the correct environment
where conda >nul 2>&1
if %errorlevel% equ 0 (
    echo Conda detected. Installing dependencies into the 'base' environment.
    conda run -n base python -m pip install -r requirements.txt
) else (
    echo Conda not found. Using default system Python.
    python -m pip install -r requirements.txt
)

if %errorlevel% equ 0 (
    echo.
    echo ================================================
    echo Installation completed successfully!
    echo ================================================
    echo.
    echo To run the application:
    echo   python lidar_viewer.py
    echo.
    echo Or double-click: run_viewer.bat
    echo.
) else (
    echo.
    echo ================================================
    echo Installation failed!
    echo ================================================
    echo.
    echo Please check the error messages above.
    echo You may need to run this script as Administrator.
    echo.
)

pause
