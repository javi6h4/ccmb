; installer.iss - Script de Inno Setup para generar CCMB_Setup.exe
; Requiere Inno Setup 6 (gratis): https://jrsoftware.org/isdl.php
;
; Uso: correr build.bat primero (genera dist\CCMB.exe), despues compilar
; este script con el Compilador de Inno Setup (ISCC.exe) o abrirlo con la
; app "Inno Setup Compiler" y presionar "Compile".
; El resultado queda en installer_output\CCMB_Setup.exe

#define MyAppName "CCMB"
#define MyAppVersion "1.0.0"
#define MyAppPublisher "CCMB"
#define MyAppExeName "CCMB.exe"

[Setup]
AppId={{B988DC38-BD70-43C9-A91F-0847B9A8CC99}}
AppName={#MyAppName}
AppVersion={#MyAppVersion}
AppPublisher={#MyAppPublisher}
DefaultDirName={autopf}\{#MyAppName}
DefaultGroupName={#MyAppName}
DisableProgramGroupPage=yes
OutputDir=installer_output
OutputBaseFilename=CCMB_Setup
SetupIconFile=assets\icon.ico
Compression=lzma2
SolidCompression=yes
WizardStyle=modern
ArchitecturesInstallIn64BitMode=x64compatible
UninstallDisplayIcon={app}\{#MyAppExeName}
PrivilegesRequired=lowest
PrivilegesRequiredOverridesAllowed=dialog

[Languages]
Name: "spanish"; MessagesFile: "compiler:Languages\Spanish.isl"

[Tasks]
Name: "desktopicon"; Description: "Crear un acceso directo en el Escritorio"; GroupDescription: "Accesos directos adicionales:"

[Files]
Source: "dist\{#MyAppExeName}"; DestDir: "{app}"; Flags: ignoreversion

[Icons]
Name: "{group}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"
Name: "{group}\Desinstalar {#MyAppName}"; Filename: "{uninstallexe}"
Name: "{autodesktop}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; Tasks: desktopicon

[Run]
Filename: "{app}\{#MyAppExeName}"; Description: "Abrir {#MyAppName} ahora"; Flags: nowait postinstall skipifsilent
