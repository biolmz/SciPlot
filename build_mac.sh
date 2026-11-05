#!/usr/bin/env bash
# SciPlot macOS 一键打包脚本（在 Mac 上运行，产出 .app 与 .dmg）
# 用法：bash build_mac.sh
set -e

echo "==> 检测架构..."
ARCH=$(uname -m)
echo "    架构: $ARCH (Apple Silicon 出 arm64，Intel 出 x86_64)"

echo "==> 创建虚拟环境..."
python3 -m venv .venv
source .venv/bin/activate

echo "==> 安装依赖（首次约需几分钟）..."
pip install --upgrade pip
pip install PySide6 numpy scipy pandas matplotlib statsmodels openpyxl pyinstaller

echo "==> 检查图标..."
if [ ! -f assets/icon.icns ]; then
    python gen_icns.py
fi

echo "==> PyInstaller 打包 .app ..."
pyinstaller --clean --noconfirm SciPlot_mac.spec

echo "==> ad-hoc 签名（本机运行更顺畅）..."
codesign --force --deep --sign - "dist/SciPlot.app" 2>/dev/null || echo "    （签名跳过）"

echo "==> 生成 DMG ..."
hdiutil create -volname "SciPlot" -srcfolder "dist/SciPlot.app" -ov -format UDZO "dist/SciPlot-1.0.0.dmg"

echo ""
echo "======================================"
echo " 完成！产物："
echo "   dist/SciPlot-1.0.0.dmg   (安装包)"
echo "   dist/SciPlot.app         (应用本体)"
echo ""
echo " 若首次打开被 Gatekeeper 拦截，终端执行："
echo "   xattr -cr /Applications/SciPlot.app"
echo "======================================"
