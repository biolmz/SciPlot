# -*- mode: python ; coding: utf-8 -*-
"""SciPlot 打包配置（PyInstaller spec）。"""
from PyInstaller.utils.hooks import collect_data_files

# 仅收集 matplotlib 必需数据（字体、样式、颜色映射）
datas = collect_data_files("matplotlib")

hiddenimports = [
    "scipy.special._ufuncs_cxx",
    "scipy.optimize._lbfgsb",
    "statsmodels.stats.multicomp",
    # pkg_resources (setuptools) 依赖，避免运行时缺失
    "jaraco.text", "jaraco.functools", "jaraco.context",
    "more_itertools", "platformdirs", "packaging",
]

# 排除环境中与 SciPlot 无关的大型库，避免触发其 hook 导致打包失败
excludes = [
    "torch", "torchvision", "torchaudio", "torchtext", "torch_geometric",
    "tensorflow", "keras", "sklearn", "scikit-learn", "scikit-image",
    "numba", "dask", "sympy", "networkx", "cv2", "opencv",
    "PyQt5", "PyQtWebEngine", "PyQt6",
    "tkinter", "IPython", "notebook", "jupyter", "jupyterlab",
    "matplotlib.backends.backend_tkagg",
    "matplotlib.backends.backend_wxagg",
    "matplotlib.backends.backend_gtk3agg",
    "matplotlib.backends.backend_gtk4agg",
    "matplotlib.backends.backend_macosx",
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
    a.binaries,
    a.datas,
    [],
    name="SciPlot",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon="assets/icon.ico",
)
