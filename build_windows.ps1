# ============================================
# Litigation Tracker - Windows Build Script (PowerShell)
# ============================================
#
# Prerequisites:
#   1. Python 3.9+ installed
#   2. Inno Setup installed (for installer creation)
#      Download from: https://jrsoftware.org/isdl.php
#
# Usage: 
#   Right-click and "Run with PowerShell"
#   Or: powershell -ExecutionPolicy Bypass -File build_windows.ps1
# ============================================

$ErrorActionPreference = "Stop"

Write-Host ""
Write-Host "============================================" -ForegroundColor Cyan
Write-Host "  Litigation Tracker - Build Script" -ForegroundColor Cyan
Write-Host "============================================" -ForegroundColor Cyan
Write-Host ""

# Check if Python is available
try {
    $pythonVersion = python --version 2>&1
    Write-Host "Found: $pythonVersion" -ForegroundColor Green
} catch {
    Write-Host "ERROR: Python is not installed or not in PATH" -ForegroundColor Red
    Write-Host "Please install Python 3.9+ from https://python.org"
    Read-Host "Press Enter to exit"
    exit 1
}

# Check if we're in the right directory
if (-not (Test-Path "main.py")) {
    Write-Host "ERROR: main.py not found" -ForegroundColor Red
    Write-Host "Please run this script from the LitigationTracker folder"
    Read-Host "Press Enter to exit"
    exit 1
}

# Step 1: Create virtual environment
Write-Host "[Step 1/6] Creating virtual environment..." -ForegroundColor Yellow
if (-not (Test-Path "venv_build")) {
    python -m venv venv_build
}

# Step 2: Activate and install dependencies
Write-Host "[Step 2/6] Installing dependencies..." -ForegroundColor Yellow
& ".\venv_build\Scripts\Activate.ps1"
pip install --upgrade pip | Out-Null
pip install -r requirements.txt
pip install pyinstaller pillow

# Step 3: Create icon
Write-Host "[Step 3/6] Creating application icon..." -ForegroundColor Yellow
$iconScript = @"
from PIL import Image, ImageDraw

size = 256
img = Image.new('RGBA', (size, size), (0, 0, 0, 0))
draw = ImageDraw.Draw(img)

# Background circle
draw.ellipse([10, 10, size-10, size-10], fill='#1a2332', outline='#f59e0b', width=8)

# Scale/Balance icon
draw.rectangle([80, 180, 176, 200], fill='#f59e0b')  # Base
draw.rectangle([118, 80, 138, 180], fill='#f59e0b')   # Pillar
draw.rectangle([40, 65, 216, 80], fill='#f59e0b')     # Beam
draw.ellipse([35, 90, 95, 120], fill='#3b82f6')       # Left pan
draw.ellipse([161, 90, 221, 120], fill='#3b82f6')     # Right pan
draw.line([65, 75, 65, 90], fill='#f59e0b', width=3)  # Left chain
draw.line([191, 75, 191, 90], fill='#f59e0b', width=3) # Right chain

img.save('icon.ico', format='ICO', sizes=[(256,256), (128,128), (64,64), (48,48), (32,32), (16,16)])
print('Icon created successfully')
"@
python -c $iconScript

# Step 4: Build with PyInstaller
Write-Host "[Step 4/6] Building executable with PyInstaller..." -ForegroundColor Yellow
pyinstaller --clean LitigationTracker.spec

if ($LASTEXITCODE -ne 0) {
    Write-Host "ERROR: PyInstaller build failed" -ForegroundColor Red
    Read-Host "Press Enter to exit"
    exit 1
}

# Step 5: Check for Inno Setup and build installer
Write-Host "[Step 5/6] Looking for Inno Setup..." -ForegroundColor Yellow
$innoSetupPath = "C:\Program Files (x86)\Inno Setup 6\ISCC.exe"
$innoSetupPath2 = "C:\Program Files\Inno Setup 6\ISCC.exe"

if (Test-Path $innoSetupPath) {
    Write-Host "Building Windows installer..." -ForegroundColor Yellow
    & $innoSetupPath "installer.iss"
} elseif (Test-Path $innoSetupPath2) {
    Write-Host "Building Windows installer..." -ForegroundColor Yellow
    & $innoSetupPath2 "installer.iss"
} else {
    Write-Host "Inno Setup not found. Skipping installer creation." -ForegroundColor Yellow
    Write-Host "To create installer, install Inno Setup from https://jrsoftware.org/isdl.php"
}

# Step 6: Complete
Write-Host ""
Write-Host "[Step 6/6] Build complete!" -ForegroundColor Green
Write-Host ""
Write-Host "============================================" -ForegroundColor Cyan
Write-Host "  BUILD SUCCESSFUL" -ForegroundColor Green
Write-Host "============================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "Executable location:" -ForegroundColor White
Write-Host "  dist\LitigationTracker\LitigationTracker.exe" -ForegroundColor Yellow
Write-Host ""

if (Test-Path "installer_output") {
    $installer = Get-ChildItem "installer_output\*.exe" | Select-Object -First 1
    if ($installer) {
        Write-Host "Installer location:" -ForegroundColor White
        Write-Host "  $($installer.FullName)" -ForegroundColor Yellow
    }
}

Write-Host ""
Read-Host "Press Enter to exit"

