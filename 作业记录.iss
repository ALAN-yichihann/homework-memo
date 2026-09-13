#define AppName "作业记录"
#define AppVersion "26.9_beta"
[Setup]
AppId={{8A1C2E2A-7E1B-4D8C-B2CC-1A3F8CE1D5A0}
AppName={#AppName}
AppVersion={#AppVersion}
AppPublisher=ALAN
DefaultDirName={autopf}\{#AppName}
DefaultGroupName={#AppName}
SetupIconFile=icon\icon.ico
OutputDir=installer
OutputBaseFilename=作业记录安装包_26.9_beta
Compression=lzma
SolidCompression=yes
WizardStyle=modern
UninstallDisplayName={#AppName}
[Languages]
Name: "chinesesimplified"; MessagesFile: "compiler:Languages\Chinese.isl"
[Files]
Source: "dist\HomeworkMemo.exe"; DestDir: "{app}"; Flags: ignoreversion
[Icons]
Name: "{group}\作业记录"; Filename: "{app}\HomeworkMemo.exe"; IconFilename: "{app}\HomeworkMemo.exe"
Name: "{commondesktop}\作业记录"; Filename: "{app}\HomeworkMemo.exe"; IconFilename: "{app}\HomeworkMemo.exe"
[Run]
Filename: "{app}\HomeworkMemo.exe"; Description: "启动作业记录"; Flags: nowait postinstall skipifsilent

