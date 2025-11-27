# -*- mode: python ; coding: utf-8 -*-
"""
PyInstaller spec file for Litigation Tracker
Run: pyinstaller LitigationTracker.spec
"""

import os
import sys
from pathlib import Path

# Get the directory containing this spec file
SPEC_DIR = Path(SPECPATH)

block_cipher = None

# Data files to include
datas = [
    (str(SPEC_DIR / 'templates'), 'templates'),
    (str(SPEC_DIR / 'static'), 'static'),
    (str(SPEC_DIR / 'main.py'), '.'),
    (str(SPEC_DIR / 'models.py'), '.'),
    (str(SPEC_DIR / 'auth.py'), '.'),
    (str(SPEC_DIR / 'excel_import.py'), '.'),
]

# Hidden imports
hiddenimports = [
    'uvicorn.logging',
    'uvicorn.loops',
    'uvicorn.loops.auto',
    'uvicorn.protocols',
    'uvicorn.protocols.http',
    'uvicorn.protocols.http.auto',
    'uvicorn.protocols.http.h11_impl',
    'uvicorn.protocols.http.httptools_impl',
    'uvicorn.protocols.websockets',
    'uvicorn.protocols.websockets.auto',
    'uvicorn.protocols.websockets.websockets_impl',
    'uvicorn.protocols.websockets.wsproto_impl',
    'uvicorn.lifespan',
    'uvicorn.lifespan.on',
    'uvicorn.lifespan.off',
    'sqlalchemy.dialects.sqlite',
    'sqlalchemy.sql.default_comparator',
    'passlib.handlers.bcrypt',
    'bcrypt',
    'email_validator',
    'dns.resolver',
    'dns.rdatatype',
    'jinja2',
    'multipart',
    'python_multipart',
    'jose',
    'jose.jwt',
    'openpyxl',
    'pandas',
    'pandas._libs.tslibs.base',
    'numpy',
    'aiofiles',
    'anyio',
    'anyio._backends',
    'anyio._backends._asyncio',
    'starlette',
    'starlette.routing',
    'starlette.middleware',
    'starlette.middleware.cors',
    'starlette.staticfiles',
    'starlette.templating',
    'fastapi',
    'fastapi.security',
    'pydantic',
    'pydantic_settings',
    'h11',
    'httptools',
    'watchfiles',
    'websockets',
    'click',
    'typing_extensions',
]

a = Analysis(
    [str(SPEC_DIR / 'launcher.py')],
    pathex=[str(SPEC_DIR)],
    binaries=[],
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        'tkinter',
        'matplotlib',
        'scipy',
        'IPython',
        'notebook',
        'pytest',
    ],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='LitigationTracker',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=True,  # Set to False to hide console window
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=str(SPEC_DIR / 'icon.ico') if (SPEC_DIR / 'icon.ico').exists() else None,
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='LitigationTracker',
)

