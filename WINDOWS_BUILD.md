# 🖥️ Building Litigation Tracker as a Windows Desktop Application

This guide explains how to create a Windows installer for Litigation Tracker that users can install like any other Windows software.

## 📋 Prerequisites

### On Your Build Machine (Windows)

1. **Python 3.9+** - Download from [python.org](https://python.org)
   - ✅ Make sure to check "Add Python to PATH" during installation

2. **Inno Setup 6** - Download from [jrsoftware.org](https://jrsoftware.org/isdl.php)
   - This creates the Windows installer (.exe)

## 🚀 Quick Build (Recommended)

### Option 1: Using PowerShell (Easiest)

1. Open PowerShell in the `LitigationTracker` folder
2. Run:
   ```powershell
   powershell -ExecutionPolicy Bypass -File build_windows.ps1
   ```

### Option 2: Using Command Prompt

1. Open Command Prompt in the `LitigationTracker` folder
2. Run:
   ```cmd
   build_windows.bat
   ```

## 📦 What Gets Created

After building, you'll have:

```
LitigationTracker/
├── dist/
│   └── LitigationTracker/
│       ├── LitigationTracker.exe    ← Main executable
│       ├── templates/                ← HTML templates
│       ├── static/                   ← CSS/JS files
│       └── ... (other files)
│
└── installer_output/
    └── LitigationTracker_Setup_1.0.0.exe  ← Windows Installer
```

## 🔧 Manual Build Steps

If the automated scripts don't work, follow these steps:

### Step 1: Install Build Dependencies

```cmd
python -m venv venv_build
venv_build\Scripts\activate
pip install -r requirements.txt
pip install pyinstaller pillow
```

### Step 2: Create Application Icon

```cmd
python -c "from PIL import Image, ImageDraw; img = Image.new('RGBA', (256, 256), (0,0,0,0)); draw = ImageDraw.Draw(img); draw.ellipse([10,10,246,246], fill='#1a2332', outline='#f59e0b', width=8); draw.rectangle([80,180,176,200], fill='#f59e0b'); draw.rectangle([118,80,138,180], fill='#f59e0b'); draw.rectangle([40,65,216,80], fill='#f59e0b'); draw.ellipse([35,90,95,120], fill='#3b82f6'); draw.ellipse([161,90,221,120], fill='#3b82f6'); img.save('icon.ico', format='ICO', sizes=[(256,256),(128,128),(64,64),(48,48),(32,32),(16,16)])"
```

### Step 3: Build Executable

```cmd
pyinstaller --clean LitigationTracker.spec
```

### Step 4: Create Installer

Open `installer.iss` with Inno Setup and click **Build → Compile**

Or run from command line:
```cmd
"C:\Program Files (x86)\Inno Setup 6\ISCC.exe" installer.iss
```

## 🎯 How the Desktop App Works

When users install and run the application:

1. **Double-click** the desktop icon `Litigation Tracker`
2. The application **starts a local server** on port 8000
3. The **browser opens automatically** to `http://localhost:8000`
4. Users interact with the web interface in their browser
5. **Close the console window** to stop the server

## 📁 Installation Details

The installer:
- Installs to `C:\Users\{user}\AppData\Local\Programs\Litigation Tracker`
- Creates a desktop shortcut (optional)
- Creates a Start Menu entry
- Creates an `uploads` folder for document storage
- Database is stored as `litigation_tracker.db` in the app folder

## 🔒 Data Location

After installation, user data is stored in:
```
C:\Users\{user}\AppData\Local\Programs\Litigation Tracker\
├── litigation_tracker.db    ← SQLite database
└── uploads\                  ← Uploaded documents
```

## 🛠️ Customization

### Change Application Name/Version

Edit `installer.iss`:
```iss
#define MyAppName "Litigation Tracker"
#define MyAppVersion "1.0.0"
#define MyAppPublisher "Your Organization"
```

### Change Default Port

Edit `launcher.py`:
```python
PORT = 8000  # Change to your preferred port
```

### Hide Console Window

To run without showing the console window, edit `LitigationTracker.spec`:
```python
exe = EXE(
    ...
    console=False,  # Change from True to False
    ...
)
```

Note: With `console=False`, users won't see server logs or error messages.

## ❓ Troubleshooting

### "Python is not installed"
- Install Python from [python.org](https://python.org)
- Make sure to check "Add Python to PATH"

### "PyInstaller failed"
- Make sure all dependencies are installed: `pip install -r requirements.txt`
- Check for syntax errors in Python files

### "Inno Setup not found"
- Download and install from [jrsoftware.org](https://jrsoftware.org/isdl.php)
- The installer will be skipped if Inno Setup is not installed

### "Port 8000 already in use"
- The app will automatically try ports 8001, 8002, etc.
- Or close any other application using port 8000

### App starts but browser doesn't open
- Manually open `http://localhost:8000` in your browser

## 📤 Distributing the Application

Share the installer file:
```
installer_output/LitigationTracker_Setup_1.0.0.exe
```

Users just need to:
1. Run the installer
2. Follow the installation wizard
3. Double-click the desktop icon

No Python installation required on end-user machines!

## 🔄 Updating the Application

To release an update:
1. Update version in `installer.iss`
2. Run the build script again
3. Distribute the new installer
4. Users install over the existing installation (data is preserved)

