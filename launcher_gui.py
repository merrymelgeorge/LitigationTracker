"""
Litigation Tracker - Windows Desktop Launcher with System Tray
Provides a system tray icon for easy server management
"""
import os
import sys
import time
import socket
import webbrowser
import threading
import subprocess
from pathlib import Path

# Check if running on Windows
IS_WINDOWS = sys.platform == 'win32'

# Determine if running as frozen executable or script
if getattr(sys, 'frozen', False):
    APP_DIR = Path(sys._MEIPASS)
    DATA_DIR = Path(os.path.dirname(sys.executable))
else:
    APP_DIR = Path(__file__).parent
    DATA_DIR = APP_DIR

# Configuration
HOST = "127.0.0.1"
PORT = 8000
APP_NAME = "Litigation Tracker"


class ServerManager:
    """Manages the FastAPI server lifecycle"""
    
    def __init__(self):
        self.server_thread = None
        self.server_process = None
        self.port = PORT
        self.running = False
    
    def is_port_in_use(self, port: int) -> bool:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            return s.connect_ex((HOST, port)) == 0
    
    def find_available_port(self) -> int:
        for i in range(10):
            port = PORT + i
            if not self.is_port_in_use(port):
                return port
        return PORT
    
    def start_server(self):
        """Start the server in a background thread"""
        if self.running:
            return
        
        self.port = self.find_available_port()
        self.running = True
        
        def run():
            os.chdir(DATA_DIR)
            sys.path.insert(0, str(APP_DIR))
            sys.path.insert(0, str(DATA_DIR))
            
            # Ensure uploads directory exists
            (DATA_DIR / "uploads").mkdir(exist_ok=True)
            
            import uvicorn
            from main import app
            
            uvicorn.run(app, host=HOST, port=self.port, log_level="warning")
        
        self.server_thread = threading.Thread(target=run, daemon=True)
        self.server_thread.start()
        
        # Wait for server to start
        for _ in range(30):
            time.sleep(0.2)
            if self.is_port_in_use(self.port):
                break
    
    def stop_server(self):
        """Stop the server"""
        self.running = False
        # Server will stop when main thread exits
    
    def open_browser(self):
        """Open the application in browser"""
        url = f"http://{HOST}:{self.port}"
        webbrowser.open(url)
    
    def get_url(self) -> str:
        return f"http://{HOST}:{self.port}"


def run_with_tray():
    """Run with system tray icon (Windows only)"""
    try:
        import pystray
        from PIL import Image, ImageDraw
    except ImportError:
        print("pystray or PIL not available, running without tray icon")
        run_simple()
        return
    
    server = ServerManager()
    
    def create_icon():
        """Create a simple icon"""
        size = 64
        image = Image.new('RGBA', (size, size), (0, 0, 0, 0))
        draw = ImageDraw.Draw(image)
        
        # Draw a scale/balance icon
        # Base
        draw.rectangle([10, 50, 54, 54], fill='#f59e0b')
        # Pillar
        draw.rectangle([29, 20, 35, 50], fill='#f59e0b')
        # Beam
        draw.rectangle([5, 15, 59, 20], fill='#f59e0b')
        # Left pan
        draw.ellipse([5, 25, 25, 35], fill='#3b82f6')
        # Right pan
        draw.ellipse([39, 25, 59, 35], fill='#3b82f6')
        
        return image
    
    def on_open(icon, item):
        server.open_browser()
    
    def on_exit(icon, item):
        icon.stop()
        server.stop_server()
        os._exit(0)
    
    def setup(icon):
        icon.visible = True
        server.start_server()
        time.sleep(1)
        server.open_browser()
    
    menu = pystray.Menu(
        pystray.MenuItem("Open Litigation Tracker", on_open, default=True),
        pystray.Menu.SEPARATOR,
        pystray.MenuItem(f"Server: http://{HOST}:{server.port}", None, enabled=False),
        pystray.Menu.SEPARATOR,
        pystray.MenuItem("Exit", on_exit)
    )
    
    icon = pystray.Icon(
        APP_NAME,
        create_icon(),
        APP_NAME,
        menu
    )
    
    icon.run(setup)


def run_simple():
    """Run without system tray (console mode)"""
    server = ServerManager()
    
    print(f"\n{'='*50}")
    print(f"  {APP_NAME}")
    print(f"{'='*50}")
    print(f"\nStarting server...")
    
    server.start_server()
    
    print(f"\nServer running at {server.get_url()}")
    print("Opening browser...")
    
    time.sleep(1)
    server.open_browser()
    
    print("\nPress Ctrl+C to stop the server")
    print("-" * 50)
    
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\nShutting down...")
        server.stop_server()


def main():
    """Main entry point"""
    os.chdir(DATA_DIR)
    
    if IS_WINDOWS:
        # Try to run with system tray
        run_with_tray()
    else:
        # Run in console mode
        run_simple()


if __name__ == "__main__":
    main()

