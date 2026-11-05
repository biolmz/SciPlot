; SciPlot 安装包脚本（Inno Setup 6）
; 需要先完成 onedir 打包（dist\SciPlot\ 文件夹）

#define MyAppName "SciPlot"
#define MyAppNameCn "SciPlot 科学数据分析与绘图"
#define MyAppVersion "1.0.0"
#define MyAppPublisher "SciPlot"
#define MyAppExeName "SciPlot.exe"

[Setup]
AppId={{6F3A1E2B-8C4D-4A5E-9B7F-2D1C8E3A5F09}
AppName={#MyAppNameCn}
AppVersion={#MyAppVersion}
AppPublisher={#MyAppPublisher}
DefaultDirName={autopf}\{#MyAppName}
DefaultGroupName={#MyAppNameCn}
DisableProgramGroupPage=yes
OutputDir=installer
OutputBaseFilename=SciPlot-Setup-{#MyAppVersion}
SetupIconFile=assets\icon.ico
UninstallDisplayIcon={app}\{#MyAppExeName}
Compression=lzma2
SolidCompression=yes
WizardStyle=modern
ArchitecturesInstallIn64BitMode=x64
PrivilegesRequired=admin
VersionInfoVersion={#MyAppVersion}
VersionInfoDescription={#MyAppNameCn}
CloseApplications=yes

[Languages]
Name: "chinesesimp"; MessagesFile: "compiler:Languages\ChineseSimplified.isl"

[Tasks]
Name: "desktopicon"; Description: "创建桌面快捷方式"; GroupDescription: "附加任务："; Flags: unchecked

[Files]
Source: "dist_onedir\SciPlot\*"; DestDir: "{app}"; Flags: recursesubdirs ignoreversion createallsubdirs

[Icons]
Name: "{autoprograms}\{#MyAppNameCn}"; Filename: "{app}\{#MyAppExeName}"
Name: "{autodesktop}\{#MyAppNameCn}"; Filename: "{app}\{#MyAppExeName}"; Tasks: desktopicon

[Run]
Filename: "{app}\{#MyAppExeName}"; Description: "立即运行 {#MyAppNameCn}"; Flags: nowait postinstall skipifsilent
