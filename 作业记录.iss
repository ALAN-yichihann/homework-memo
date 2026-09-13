#define AppName "作业记录"
#define AppVersion "1.0.0"
[Setup]
AppId={{8A1C2E2A-7E1B-4D8C-B2CC-1A3F8CE1D5A0}
AppName={#AppName}
AppVersion={#AppVersion}
DefaultDirName={autopf}\{#AppName}
DefaultGroupName={#AppName}
OutputDir=installer
OutputBaseFilename=作业记录安装包
Compression=lzma
SolidCompression=yes
WizardStyle=modern
[Files]
Source: "dist\HomeworkMemo.exe"; DestDir: "{app}"; Flags: ignoreversion
[Icons]
Name: "{group}\作业记录"; Filename: "{app}\作业记录.exe"
Name: "{commondesktop}\作业记录"; Filename: "{app}\作业记录.exe"
[Run]
Filename: "{app}\作业记录.exe"; Description: "启动作业记录"; Flags: nowait postinstall skipifsilent

