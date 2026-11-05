# -*- mode: python ; coding: utf-8 -*-
"""SciPlot macOS 打包配置（生成 .app bundle，配合 build_mac.sh 出 .dmg）。"""
from PyInstaller.utils.hooks import collect_data_files

datas = collect_data_files("matplotlib")

hiddenimports = [
    "scipy.special._ufuncs_cxx",
    "scipy.optimize._lbfgsb",
    "statsmodels.stats.multicomp",
    # pkg_resources (setuptools) 依赖，避免运行时缺失
    "jaraco.text", "jaraco.functools", "jaraco.context",
    "more_itertools", "platformdirs", "packaging",
]

excludes = [
    "torch", "torchvision", "torchaudio", "torchtext",
    "tensorflow", "keras", "sklearn", "scikit-learn", "scikit-image",
    "numba", "dask", "sympy", "networkx", "cv2", "opencv",
    "PyQt5", "PyQt6", "PyQtWebEngine",
    "tkinter", "IPython", "notebook", "jupyter", "jupyterlab",
    "matplotlib.backends.backend_tkagg",
    "matplotlib.backends.backend_wxagg",
    "matplotlib.backends.backend_gtk3agg",
    "matplotlib.backends.backend_gtk4agg",
    "pytest", "pip", "wheel",
]

a = Analysis(
    ["main.py"],
    pathex=[],
    binaries=[],
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=excludes,
    noarchive=False,
    optimize=1,
)

pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name="SciPlot",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon="assets/icon.icns",
)

coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=False,
    name="SciPlot",
)

app = BUNDLE(
    coll,
    name="SciPlot.app",
    icon="assets/icon.icns",
    bundle_identifier="com.sciplot.app",
    info_plist={
        "CFBundleName": "SciPlot",
        "CFBundleDisplayName": "SciPlot 科学数据分析与绘图",
        "CFBundleShortVersionString": "1.0.0",
        "CFBundleVersion": "1.0.0",
        "NSHighResolutionCapable": True,
        "LSMinimumSystemVersion": "10.15",
    },
)
