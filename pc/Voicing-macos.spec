# -*- mode: python ; coding: utf-8 -*-


a = Analysis(
    ["voice_coding.py"],
    pathex=[],
    binaries=[],
    datas=[("assets", "assets")],
    hiddenimports=[],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name="Voicing",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,
    console=False,
    icon="assets/icon.icns",
)

coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=False,
    upx_exclude=[],
    name="Voicing",
)

app = BUNDLE(
    coll,
    name="Voicing.app",
    icon="assets/icon.icns",
    bundle_identifier="com.kevinlasnh.voicing",
    info_plist={
        "LSUIElement": True,
        "NSHighResolutionCapable": True,
    },
)
