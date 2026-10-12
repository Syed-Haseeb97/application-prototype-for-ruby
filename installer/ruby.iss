; Inno Setup script (optional). Compile after scripts\build_windows.ps1:  iscc installer\ruby.iss
; Not compiled in the authoring environment.
[Setup]
AppName=Ruby
AppVersion=1.0
DefaultDirName={autopf}\Ruby
DefaultGroupName=Ruby
OutputBaseFilename=RubySetup
OutputDir=..\dist
PrivilegesRequired=lowest
SetupIconFile=..\assets\ruby.ico
UninstallDisplayIcon={app}\Ruby.exe

[Files]
Source: "..\dist\Ruby\*"; DestDir: "{app}"; Flags: recursesubdirs ignoreversion

[Icons]
Name: "{autoprograms}\Ruby"; Filename: "{app}\Ruby.exe"
Name: "{autodesktop}\Ruby"; Filename: "{app}\Ruby.exe"; Tasks: desktopicon

[Tasks]
Name: "desktopicon"; Description: "Create a desktop shortcut"

[Run]
Filename: "{app}\Ruby.exe"; Description: "Launch Ruby"; Flags: nowait postinstall skipifsilent
