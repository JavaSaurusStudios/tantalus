@echo off
setlocal

REM Check if python is available
python --version >nul 2>&1
if errorlevel 1 (
    echo Python is not installed or not in PATH.
    echo Please install Python 3.x from https://python.org/downloads
    pause
    exit /b 1
)

echo Python found.

REM Install dependencies from requirements.txt if it exists
if exist requirements.txt (
    echo Installing required Python packages...
    python -m pip install --upgrade pip
    python -m pip install -r requirements.txt
) else (
    echo requirements.txt not found, skipping dependency installation.
)

echo Running the application...
python main.py

pause
