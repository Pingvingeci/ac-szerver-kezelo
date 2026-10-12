; AC Szerver Kezelő – telepítő (Inno Setup 6)
; Fordítás: ISCC /DAppVersion=1.2.3 installer.iss   (a build.bat ezt magától megcsinálja)

#define AppName "AC Szerver Kezelő"
#define AppExe "AC_Szerver_Kezelo.exe"
#ifndef AppVersion
  #define AppVersion "0.0.0"
#endif

[Setup]
AppId={{8C3B5E2A-6F1D-4B7C-9E2A-3D5F7A1B9C40}
AppName={#AppName}
AppVersion={#AppVersion}
AppVerName={#AppName} {#AppVersion}
VersionInfoVersion={#AppVersion}
; Felhasználói telepítés: nem kell rendszergazda, és a frissítés sem kér jóváhagyást
PrivilegesRequired=lowest
PrivilegesRequiredOverridesAllowed=dialog
DefaultDirName={autopf}\AC Szerver Kezelo
DisableProgramGroupPage=yes
DisableDirPage=no
UsePreviousAppDir=yes
OutputDir=dist
OutputBaseFilename=AC_Szerver_Kezelo_Setup_{#AppVersion}
SetupIconFile=assets\icon.ico
UninstallDisplayIcon={app}\{#AppExe}
UninstallDisplayName={#AppName}
Compression=lzma2/max
SolidCompression=yes
WizardStyle=modern
CloseApplications=yes
RestartApplications=no

[Languages]
Name: "hu"; MessagesFile: "compiler:Languages\Hungarian.isl"

[Tasks]
Name: "desktopicon"; Description: "{cm:CreateDesktopIcon}"; GroupDescription: "{cm:AdditionalIcons}"

[Files]
Source: "dist\{#AppExe}"; DestDir: "{app}"; Flags: ignoreversion
Source: "README.md"; DestDir: "{app}"; DestName: "OLVASSEL.md"; Flags: ignoreversion

[Icons]
Name: "{autoprograms}\{#AppName}"; Filename: "{app}\{#AppExe}"
Name: "{autodesktop}\{#AppName}"; Filename: "{app}\{#AppExe}"; Tasks: desktopicon

[Run]
; Csendes (frissítés közbeni) telepítésnél is lefut, így a program magától újraindul
Filename: "{app}\{#AppExe}"; Description: "{cm:LaunchProgram,{#AppName}}"; Flags: nowait postinstall