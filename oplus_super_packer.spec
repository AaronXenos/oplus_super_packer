import sys
from PyInstaller.building.build_main import Analysis, PYZ, EXE, COLLECT
from PyInstaller.building.datastruct import TOC

# Entry script
entry_script = 'oplus_super_packer.py'

# Exclude heavy/unused modules to shrink size
excluded_modules = [
    'tkinter', 'numpy', 'pandas', 'scipy', 'matplotlib', 'PyQt5', 'PySide2',
    'pytest', 'unittest', 'IPython', 'notebook', 'sqlite3',
    'asyncio',
]

# Add hiddenimports only if PyInstaller misses something.
hidden_imports = []

# No extra data/binaries for this CLI tool
datas = []
binaries = []

block_cipher = None

analysis = Analysis(
    [entry_script],
    pathex=[],
    binaries=binaries,
    datas=datas,
    hiddenimports=hidden_imports,
    hookspath=[],
    excludes=excluded_modules,
    noarchive=False,
)

pyz = PYZ(analysis.pure, analysis.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    analysis.scripts,
    analysis.binaries,
    analysis.zipfiles,
    analysis.datas,
    [],
    exclude_binaries=False,
    name='oplus_super_packer',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=True,
    disable_windowed_traceback=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon='EXE.ico',
)