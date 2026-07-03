Add-Type -AssemblyName System.Windows.Forms

$AppName = "Controle Impressoras"
$ExeName = "ControleImpressoras.exe"
$ProjectDir = Split-Path -Parent $MyInvocation.MyCommand.Definition
$ExeSource = Join-Path $ProjectDir "dist" $ExeName

if (-not (Test-Path -LiteralPath $ExeSource)) {
    Write-Host "ERRO: $ExeName não encontrado em $ExeSource" -ForegroundColor Red
    Write-Host "Execute primeiro: pyinstaller --onefile --windowed ... (veja o build.ps1)" -ForegroundColor Yellow
    pause
    exit 1
}

$FolderDialog = New-Object System.Windows.Forms.FolderBrowserDialog
$FolderDialog.Description = "Escolha onde instalar o $AppName"
$FolderDialog.SelectedPath = [Environment]::GetFolderPath("ProgramFiles")
$Result = $FolderDialog.ShowDialog()

if ($Result -ne "OK") {
    Write-Host "Instalação cancelada pelo usuário." -ForegroundColor Yellow
    exit 0
}

$InstallDir = $FolderDialog.SelectedPath
$AppDir = Join-Path $InstallDir $AppName

Write-Host "Instalando em: $AppDir" -ForegroundColor Cyan

# Create directory
New-Item -ItemType Directory -Path $AppDir -Force | Out-Null

# Copy exe
Copy-Item -LiteralPath $ExeSource -Destination (Join-Path $AppDir $ExeName) -Force
Write-Host "  ✓ $ExeName copiado" -ForegroundColor Green

# Desktop shortcut
$Desktop = [Environment]::GetFolderPath("Desktop")
$WScriptShell = New-Object -ComObject WScript.Shell
$Shortcut = $WScriptShell.CreateShortcut("$Desktop\$AppName.lnk")
$Shortcut.TargetPath = Join-Path $AppDir $ExeName
$Shortcut.WorkingDirectory = $AppDir
$Shortcut.Description = "Sistema de Controle de Impressoras"
$Shortcut.Save()
Write-Host "  ✓ Atalho criado na Área de Trabalho" -ForegroundColor Green

# Start Menu shortcut
$StartMenu = [Environment]::GetFolderPath("StartMenu")
$StartMenuDir = "$StartMenu\Programs\$AppName"
New-Item -ItemType Directory -Path $StartMenuDir -Force | Out-Null
$ShortcutSM = $WScriptShell.CreateShortcut("$StartMenuDir\$AppName.lnk")
$ShortcutSM.TargetPath = Join-Path $AppDir $ExeName
$ShortcutSM.WorkingDirectory = $AppDir
$ShortcutSM.Description = "Sistema de Controle de Impressoras"
$ShortcutSM.Save()
Write-Host "  ✓ Atalho criado no Menu Iniciar" -ForegroundColor Green

# Add to Add/Remove Programs
$UninstallKey = "HKLM:\SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall\$AppName"
$UninstallKeyWow = "HKLM:\SOFTWARE\WOW6432Node\Microsoft\Windows\CurrentVersion\Uninstall\$AppName"
$UninstallString = "`"$(Join-Path $AppDir $ExeName)`""
$DisplayIcon = Join-Path $AppDir $ExeName

$KeyInfo = @{
    "DisplayName" = $AppName
    "DisplayVersion" = "1.0.0"
    "Publisher" = "Suporte Técnico"
    "InstallLocation" = $AppDir
    "UninstallString" = $UninstallString
    "DisplayIcon" = $DisplayIcon
    "NoModify" = 1
    "NoRepair" = 1
}

try {
    New-Item -Path $UninstallKey -Force | Out-Null
    foreach ($kv in $KeyInfo.GetEnumerator()) {
        Set-ItemProperty -Path $UninstallKey -Name $kv.Key -Value $kv.Value
    }
    Write-Host "  ✓ Registrado em Programas e Recursos (Add/Remove Programs)" -ForegroundColor Green
} catch {
    # Fallback to HKCU if no admin
    $UninstallKeyUser = "HKCU:\SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall\$AppName"
    New-Item -Path $UninstallKeyUser -Force | Out-Null
    foreach ($kv in $KeyInfo.GetEnumerator()) {
        Set-ItemProperty -Path $UninstallKeyUser -Name $kv.Key -Value $kv.Value
    }
    Write-Host "  ⚠ Registrado em Programas e Recursos (usuário atual, sem admin)" -ForegroundColor Yellow
}

Write-Host "`n✅ Instalação concluída!" -ForegroundColor Green
Write-Host "  Pasta: $AppDir" -ForegroundColor Gray
Write-Host "  Atalhos: Área de Trabalho + Menu Iniciar" -ForegroundColor Gray
Write-Host "`nO banco de dados fica em: %LOCALAPPDATA%\ControleImpressoras\app.db" -ForegroundColor Cyan
Write-Host "  (a migration é automática na primeira execução)" -ForegroundColor Cyan

pause
