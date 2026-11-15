@echo off
title PrivateDrive - Remote Virtual Drive Server
cd /d "%~dp0"

echo ==========================================================
echo        Starting PrivateDrive for Windows
echo ==========================================================
echo.

python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] Python is not installed or not in your PATH.
    echo Please install Python from https://www.python.org/downloads/
    echo (Make sure to check "Add Python to PATH" during installation)
    pause
    exit /b
)

echo Checking dependencies...
python -m pip install -r requirements.txt >nul 2>&1

echo.
echo Launching PrivateDrive Server...
echo ==========================================================
python app.py

pause
