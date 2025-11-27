@echo off
REM ============================================
REM Litigation Tracker - Windows Build Script
REM ============================================
REM 
REM Prerequisites:
REM   1. Python 3.9+ installed and in PATH
REM   2. pip install pyinstaller
REM   3. Inno Setup installed (for installer creation)
REM      Download from: https://jrsoftware.org/isdl.php
REM
REM Usage: Run this script from the LitigationTracker folder
REM ============================================

echo.
echo ============================================
echo   Litigation Tracker - Build Script
echo ============================================
echo.

REM Check if Python is available
python --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Python is not installed or not in PATH
    echo Please install Python 3.9+ from https://python.org
    pause
    exit /b 1
)

REM Check if we're in the right directory
if not exist "main.py" (
    echo ERROR: main.py not found
    echo Please run this script from the LitigationTracker folder
    pause
    exit /b 1
)

echo [Step 1/5] Creating virtual environment...
if not exist "venv_build" (
    python -m venv venv_build
)

echo [Step 2/5] Activating virtual environment and installing dependencies...
call venv_build\Scripts\activate.bat

pip install --upgrade pip
pip install -r requirements.txt
pip install pyinstaller

echo [Step 3/5] Creating icon file...
REM Create a simple icon using Python (or use an existing .ico file)
python -c "
from PIL import Image, ImageDraw
import os

size = 256
img = Image.new('RGBA', (size, size), (0, 0, 0, 0))
draw = ImageDraw.Draw(img)

# Background circle
draw.ellipse([10, 10, size-10, size-10], fill='#1a2332', outline='#f59e0b', width=8)

# Scale/Balance icon
# Base
draw.rectangle([80, 180, 176, 200], fill='#f59e0b')
# Pillar
draw.rectangle([118, 80, 138, 180], fill='#f59e0b')
# Beam
draw.rectangle([40, 65, 216, 80], fill='#f59e0b')
# Left pan
draw.ellipse([35, 90, 95, 120], fill='#3b82f6')
# Right pan
draw.ellipse([161, 90, 221, 120], fill='#3b82f6')
# Chains
draw.line([65, 75, 65, 90], fill='#f59e0b', width=3)
draw.line([191, 75, 191, 90], fill='#f59e0b', width=3)

# Save as ICO
img.save('icon.ico', format='ICO', sizes=[(256, 256), (128, 128), (64, 64), (48, 48), (32, 32), (16, 16)])
print('Icon created: icon.ico')
" 2>nul || echo Warning: Could not create icon (PIL not available)

echo [Step 4/5] Building executable with PyInstaller...
pyinstaller --clean LitigationTracker.spec

if errorlevel 1 (
    echo ERROR: PyInstaller build failed
    pause
    exit /b 1
)

echo [Step 5/5] Build complete!
echo.
echo ============================================
echo   BUILD SUCCESSFUL
echo ============================================
echo.
echo The executable is located at:
echo   dist\LitigationTracker\LitigationTracker.exe
echo.
echo To create the Windows installer:
echo   1. Install Inno Setup from https://jrsoftware.org/isdl.php
echo   2. Open installer.iss with Inno Setup
echo   3. Click Build -^> Compile
echo   4. The installer will be created in installer_output\
echo.
echo Or run: "C:\Program Files (x86)\Inno Setup 6\ISCC.exe" installer.iss
echo.

pause

