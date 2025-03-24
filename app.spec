
a = Analysis(
    ['main.py'],
    pathex=[],
    datas=[],
    hiddenimports=[],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    noarchive=False,
    optimize=2,
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,  # 添加二进制文件
    a.datas,      # 添加数据文件
    exclude_binaries=False,  # 确保包含二进制
    name='图片生成器',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=['app.ico'],
    onefile=True
)
coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='ImageGenerator',
)
app = BUNDLE(
    coll,
    name='图片生成器.app',
    icon='app.ico',
    bundle_identifier=None,
)
