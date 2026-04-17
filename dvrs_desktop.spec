# -*- mode: python ; coding: utf-8 -*-

from pathlib import Path

from PyInstaller.utils.hooks import collect_data_files
from PyInstaller.utils.win32.versioninfo import (
    VSVersionInfo,
    FixedFileInfo,
    StringFileInfo,
    StringTable,
    StringStruct,
    VarFileInfo,
    VarStruct,
)


project_root = Path(SPECPATH)
datas = collect_data_files("dvrs_tool", includes=["static/*", "static/assets/*"])
version_info = VSVersionInfo(
    ffi=FixedFileInfo(
        filevers=(0, 1, 3, 0),
        prodvers=(0, 1, 3, 0),
        mask=0x3F,
        flags=0x0,
        OS=0x40004,
        fileType=0x1,
        subtype=0x0,
        date=(0, 0),
    ),
    kids=[
        StringFileInfo(
            [
                StringTable(
                    "040904B0",
                    [
                        StringStruct("CompanyName", "Motorola Solutions"),
                        StringStruct("FileDescription", "DVRS Planner"),
                        StringStruct("FileVersion", "0.1.3"),
                        StringStruct("InternalName", "DVRSPlanner"),
                        StringStruct("OriginalFilename", "DVRSPlanner.exe"),
                        StringStruct("ProductName", "DVRS Planner"),
                        StringStruct("ProductVersion", "0.1.3"),
                    ],
                )
            ]
        ),
        VarFileInfo([VarStruct("Translation", [1033, 1200])]),
    ],
)

analysis = Analysis(
    ["run_desktop.py"],
    pathex=[str(project_root)],
    binaries=[],
    datas=datas,
    hiddenimports=[
        "PySide6.QtWebEngineWidgets",
        "PySide6.QtWebEngineCore",
        "uvicorn.logging",
        "uvicorn.loops.auto",
        "uvicorn.protocols.http.auto",
        "uvicorn.protocols.websockets.auto",
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
    optimize=0,
)
pyz = PYZ(analysis.pure)

exe = EXE(
    pyz,
    analysis.scripts,
    analysis.binaries,
    analysis.datas,
    [],
    name="DVRSPlanner",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=str(project_root / "dvrs_tool" / "static" / "assets" / "branding" / "motorola-solutions-emsignia-app.ico"),
    version=version_info,
)
