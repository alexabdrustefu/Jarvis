#ifndef AppVersion
  #define AppVersion "0.1.0"
#endif

[Setup]
AppId={{7B8ED4C0-440E-4D4C-B7C8-FE254CBE0D31}
AppName=J.A.R.V.I.S.
AppVersion={#AppVersion}
AppPublisher=Alexandru Stefu
AppPublisherURL=https://github.com/alexabdrustefu/Jarvis
AppSupportURL=https://github.com/alexabdrustefu/Jarvis/issues
DefaultDirName={localappdata}\Programs\JARVIS
DefaultGroupName=J.A.R.V.I.S.
PrivilegesRequired=lowest
ArchitecturesAllowed=x64
ArchitecturesInstallIn64BitMode=x64
WizardStyle=modern
UninstallDisplayIcon={app}\JARVIS.exe
OutputDir=..\dist
OutputBaseFilename=JARVIS-Setup-{#AppVersion}
Compression=lzma2
SolidCompression=yes
SetupLogging=yes
VersionInfoVersion={#AppVersion}

[Dirs]
Name: "{localappdata}\JARVIS"

[Files]
Source: "..\dist\JARVIS\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs
Source: "..\.env.example"; DestDir: "{localappdata}\JARVIS"; DestName: "config.example.env"; Flags: onlyifdoesntexist
Source: "..\LICENSE"; DestDir: "{app}\docs"; Flags: ignoreversion
Source: "..\README.md"; DestDir: "{app}\docs"; Flags: ignoreversion
Source: "..\INSTALLAZIONE.md"; DestDir: "{app}\docs"; Flags: ignoreversion

[Icons]
Name: "{autoprograms}\J.A.R.V.I.S."; Filename: "{app}\JARVIS.exe"
Name: "{autodesktop}\J.A.R.V.I.S."; Filename: "{app}\JARVIS.exe"; Tasks: desktopicon

[Tasks]
Name: "desktopicon"; Description: "Crea un collegamento sul desktop"; GroupDescription: "Collegamenti aggiuntivi:"

[Run]
Filename: "{app}\JARVIS.exe"; Description: "Avvia J.A.R.V.I.S."; Flags: postinstall nowait skipifsilent
