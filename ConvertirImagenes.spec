# -*- mode: python ; coding: utf-8 -*-
"""
ConvertirImagenes.spec — PyInstaller spec for cross-platform AVIF converter.

Build command:
    pyinstaller ConvertirImagenes.spec

CRITICAL: --collect-data tkinterdnd2 (handled below in datas) ensures
that the hidden Tcl/Tk DnD extension binaries are bundled into the
frozen executable.  Without this, Drag & Drop will silently fail.
"""
import sys
from PyInstaller.utils.hooks import collect_data_files

# ── Collect hidden binary data from tkinterdnd2 ───────────────────────
datas = []
try:
    datas += collect_data_files('tkinterdnd2')
except Exception:
    print("WARNING: could not collect tkinterdnd2 data files. DnD may not work in the packaged app.")

# ── Analysis ──────────────────────────────────────────────────────────
a = Analysis(
    ['app.py'],
    pathex=[],
    binaries=[],
    datas=datas,
    hiddenimports=[
        'tkinterdnd2',
        'PIL',
        'pillow_avif',          # pillow-avif-plugin registers via entry_points
        'piexif',
        'customtkinter',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
    optimize=0,
)

pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='ConvertirImagenes',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,          # GUI app → no console window
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    # icon='assets/icon.ico',   # Uncomment and set path when you have an icon
)

coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='ConvertirImagenes',
)

# ── macOS .app bundle (ignored on other platforms) ────────────────────
if sys.platform == 'darwin':
    app = BUNDLE(
        coll,
        name='ConvertirImagenes.app',
        # icon='assets/icon.icns',  # Uncomment for macOS icon
        bundle_identifier='com.convertirimagenes.app',
    )
