; Inno Setup Script for Controle Impressoras
; Build: ISCC.exe setup.iss

#define MyAppName "Controle Impressoras"
#define MyAppVersion "2.0.0"
#define MyAppPublisher "Suporte Tecnico"
#define MyAppExeName "ControleImpressoras.exe"

[Setup]
AppId={{B8A3C2D1-E5F4-4A6B-9C8D-7E1F2A3B4C5D}
AppName={#MyAppName}
AppVersion={#MyAppVersion}
AppPublisher={#MyAppPublisher}
DefaultDirName={autopf}\{#MyAppName}
DefaultGroupName={#MyAppName}
AllowNoIcons=yes
OutputDir=dist
OutputBaseFilename=ControleImpressoras_Installer
Compression=lzma2/max
SolidCompression=yes
WizardStyle=modern
UninstallDisplayIcon={app}\{#MyAppExeName}
PrivilegesRequired=admin
DisableProgramGroupPage=yes

[Languages]
Name: "portuguese"; MessagesFile: "compiler:Languages\BrazilianPortuguese.isl"

[Tasks]
Name: "desktopicon"; Description: "Criar atalho na &Area de Trabalho"; GroupDescription: "Atalhos:"; Flags: checkedonce

[Files]
Source: "dist\ControleImpressoras\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs

[Icons]
Name: "{autoprograms}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; WorkingDir: "{app}"; Comment: "Sistema de Controle de Impressoras"
Name: "{autodesktop}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; WorkingDir: "{app}"; Comment: "Sistema de Controle de Impressoras"; Tasks: desktopicon

[Run]
Filename: "{app}\{#MyAppExeName}"; Description: "Iniciar {#MyAppName}"; Flags: postinstall nowait skipifsilent shellexec

[Code]
var
  DataPage: TInputOptionWizardPage;
  DataDir: String;

function InitializeSetup: Boolean;
begin
  DataDir := ExpandConstant('{localappdata}') + '\ControleImpressoras';
  Result := True;
end;

procedure CurPageChanged(CurPageID: Integer);
begin
  if CurPageID = wpFinished then
  begin
    DataPage := CreateInputOptionPage(wpFinished,
      'Dados do Aplicativo', '',
      'O banco de dados, anexos e backups ficam em:'#13#10 + DataDir + #13#10#13#10 +
      'Deseja preservar estes dados ao desinstalar?',
      True, False);
    DataPage.Add('Preservar dados (recomendado)');
    DataPage.Add('Remover todos os dados');
    DataPage.SelectedValueIndex := 0;
  end;
end;

function GetUninstallString: String;
begin
  Result := '/UNINSTALL';
end;

procedure CurUninstallStepChanged(CurUninstallStep: TUninstallStep);
var
  RemoveData: Boolean;
begin
  if CurUninstallStep = usUninstall then
  begin
    RemoveData := MsgBox(
      'Remover tambem os dados do aplicativo?'#13#10#13#10 +
      'Banco de dados, anexos e backups em:'#13#10 +
      DataDir,
      mbConfirmation, MB_YESNO) = idYes;
    if RemoveData then
    begin
      if DelTree(DataDir, True, True, True) then
        Log('Dados removidos: ' + DataDir)
      else
        Log('Falha ao remover dados: ' + DataDir);
    end;
  end;
end;
