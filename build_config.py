"""
Build Configuration for Litigation Tracker
Used by PyInstaller to create the Windows executable
"""

import os
from pathlib import Path

# Application info
APP_NAME = "LitigationTracker"
APP_VERSION = "1.0.0"
APP_AUTHOR = "Your Organization"
APP_DESCRIPTION = "A web-based platform for tracking litigations"

# Paths
ROOT_DIR = Path(__file__).parent
DIST_DIR = ROOT_DIR / "dist"
BUILD_DIR = ROOT_DIR / "build"

# Files to include in the build
DATA_FILES = [
    # (source, destination_folder)
    ("main.py", "."),
    ("models.py", "."),
    ("auth.py", "."),
    ("excel_import.py", "."),
    ("templates", "templates"),
    ("static", "static"),
]

# Hidden imports that PyInstaller might miss
HIDDEN_IMPORTS = [
    "uvicorn.logging",
    "uvicorn.loops",
    "uvicorn.loops.auto",
    "uvicorn.protocols",
    "uvicorn.protocols.http",
    "uvicorn.protocols.http.auto",
    "uvicorn.protocols.websockets",
    "uvicorn.protocols.websockets.auto",
    "uvicorn.lifespan",
    "uvicorn.lifespan.on",
    "uvicorn.lifespan.off",
    "sqlalchemy.dialects.sqlite",
    "passlib.handlers.bcrypt",
    "email_validator",
    "jinja2",
    "multipart",
    "jose",
    "bcrypt",
    "openpyxl",
    "pandas",
    "numpy",
]

# Packages to collect all submodules
COLLECT_ALL = [
    "uvicorn",
    "fastapi",
    "starlette",
    "pydantic",
    "sqlalchemy",
    "jinja2",
    "openpyxl",
]

# Packages to copy metadata
COPY_METADATA = [
    "fastapi",
    "starlette",
    "pydantic",
]

