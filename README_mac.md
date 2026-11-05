# SciPlot macOS 打包指南

SciPlot 的代码（`scplot/` 包 + `main.py`）是纯 Python + PySide6，完全跨平台。
Windows 版 exe 已就绪，本目录已备好 macOS 打包所需全部文件：

| 文件 | 用途 |
|------|------|
| `SciPlot_mac.spec` | macOS 打包配置（生成 `.app`） |
| `build_mac.sh` | 在 Mac 上一键打包脚本 |
| `assets/icon.icns` | macOS 应用图标 |
| `.github/workflows/build-macos.yml` | 云端自动打包（无需 Mac） |

> ⚠️ 说明：PyInstaller **不支持跨平台打包**——Windows 上无法直接生成 `.dmg`。
> 必须在 macOS 环境打包。下面两种方式任选其一。

---

## 方式一：GitHub Actions 云端打包（没有 Mac 也能出 dmg，推荐）

1. 把本项目推送到 GitHub（需一个仓库，public 即可，免费额度够用）：
   ```bash
   cd SciPlot
   git init
   git add .
   git commit -m "SciPlot 科学数据分析与绘图软件"
   git branch -M main
   git remote add origin https://github.com/你的用户名/SciPlot.git
   git push -u origin main
   ```

2. 打开仓库网页 → **Actions** 标签 → 左侧选 **Build macOS DMG** → **Run workflow**。

3. 约 10 分钟后，两个架构的 dmg 出现在该次运行的 Artifacts 里：
   - `SciPlot-macOS-arm64` → Apple Silicon（M1/M2/M3/M4）
   - `SciPlot-macOS-x86_64` → Intel Mac
   按自己 Mac 的芯片下载对应文件。

---

## 方式二：在 Mac 上本地一键打包

1. 把整个 `SciPlot` 文件夹拷到 Mac（U 盘 / AirDrop / 网盘均可）。

2. 打开「终端」，进入该目录执行：
   ```bash
   bash build_mac.sh
   ```
   脚本会自动建虚拟环境、装依赖、打包 `.app` 并生成 `dist/SciPlot-1.0.0.dmg`。

   > 若 Mac 未安装 Xcode Command Line Tools，会先提示安装（`xcode-select --install`）。

---

## 安装与首次打开（Gatekeeper）

把 `.dmg` 双击挂载，拖 `SciPlot.app` 到「应用程序」。首次打开若提示
「无法验证开发者 / 已损坏」，是 macOS 对未签名应用的限制，终端执行一次即可：

```bash
xattr -cr /Applications/SciPlot.app
```

之后再正常双击打开。

---

## 附：架构说明

| Mac 芯片 | 下载/打包架构 |
|----------|--------------|
| Apple Silicon（2020 年后，M1 及以后） | arm64 |
| Intel（2020 年前） | x86_64 |

本地打包时脚本会自动按当前机器架构出包，无需手动指定。
