"""
Litigation Tracker - Windows Desktop Launcher
Starts the FastAPI server and opens the browser automatically
"""
import os
import sys
import time
import socket
import webbrowser
import threading
from pathlib import Path

# Determine if running as frozen executable or script
if getattr(sys, 'frozen', False):
    # Running as compiled executable
    APP_DIR = Path(sys._MEIPASS)
    DATA_DIR = Path(os.path.dirname(sys.executable))
else:
    # Running as script
    APP_DIR = Path(__file__).parent
    DATA_DIR = APP_DIR

# Configuration
HOST = "127.0.0.1"
PORT = 8000
APP_NAME = "Litigation Tracker"
BROWSER_DELAY = 2  # seconds to wait before opening browser


def is_port_in_use(port: int) -> bool:
    """Check if a port is already in use"""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        return s.connect_ex((HOST, port)) == 0


def find_available_port(start_port: int = 8000, max_attempts: int = 10) -> int:
    """Find an available port starting from start_port"""
    for i in range(max_attempts):
        port = start_port + i
        if not is_port_in_use(port):
            return port
    return start_port


def open_browser(port: int):
    """Open the default browser after a delay"""
    time.sleep(BROWSER_DELAY)
    url = f"http://{HOST}:{port}"
    print(f"Opening browser at {url}")
    webbrowser.open(url)


def setup_environment():
    """Setup the working directory and environment"""
    # Add app directory to Python path FIRST
    sys.path.insert(0, str(APP_DIR))
    sys.path.insert(0, str(DATA_DIR))
    
    # Change to data directory for database and uploads
    os.chdir(DATA_DIR)
    
    # Ensure required directories exist
    uploads_dir = DATA_DIR / "uploads"
    uploads_dir.mkdir(exist_ok=True)
    
    # Set environment variables
    os.environ["PYTHONDONTWRITEBYTECODE"] = "1"
    
    # Verify static directory exists
    static_dir = APP_DIR / "static"
    templates_dir = APP_DIR / "templates"
    
    if not static_dir.exists():
        print(f"Warning: Static directory not found at {static_dir}")
    if not templates_dir.exists():
        print(f"Warning: Templates directory not found at {templates_dir}")


def run_server(port: int):
    """Run the FastAPI server"""
    import uvicorn
    
    try:
        from main import app
        
        print(f"\n{'='*50}")
        print(f"  {APP_NAME}")
        print(f"  Server running at http://{HOST}:{port}")
        print(f"  Press Ctrl+C to stop")
        print(f"{'='*50}\n")
        
        uvicorn.run(app, host=HOST, port=port, log_level="info")
        
    except Exception as e:
        print(f"Error starting server: {e}")
        import traceback
        traceback.print_exc()
        input("Press Enter to exit...")
        sys.exit(1)


def main():
    """Main entry point"""
    print(f"Starting {APP_NAME}...")
    print(f"App directory: {APP_DIR}")
    print(f"Data directory: {DATA_DIR}")
    
    # Setup environment
    setup_environment()
    
    # Find available port
    port = find_available_port(PORT)
    if port != PORT:
        print(f"Port {PORT} is in use, using port {port}")
    
    # Start browser opener in background thread
    browser_thread = threading.Thread(target=open_browser, args=(port,), daemon=True)
    browser_thread.start()
    
    # Run the server (this blocks)
    try:
        run_server(port)
    except KeyboardInterrupt:
        print("\nShutting down...")
        sys.exit(0)


if __name__ == "__main__":
    main()

