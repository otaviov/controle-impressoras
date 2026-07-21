$ErrorActionPreference = "Stop"

$ProjectRoot = Split-Path -Parent $MyInvocation.MyCommand.Definition
Set-Location -LiteralPath $ProjectRoot

Write-Host "=== Build do ControleImpressoras ===" -ForegroundColor Cyan

# 1. Verifica virtual environment
$VenvDir = Join-Path $ProjectRoot ".venv"
if (-not (Test-Path -LiteralPath "$VenvDir\Scripts\python.exe")) {
    Write-Host "Criando virtual environment..." -ForegroundColor Yellow
    python -m venv $VenvDir
}

Write-Host "Instalando dependencias..." -ForegroundColor Yellow
& "$VenvDir\Scripts\pip" install -r "$ProjectRoot\requirements.txt" --quiet
if ($LASTEXITCODE -ne 0) {
    Write-Host "Falha ao instalar dependencias!" -ForegroundColor Red
    exit 1
}

# 2. Verifica recursos necessarios
$Resources = @(
    @{Path="themes\dark_premium.qss"; Label="tema dark"},
    @{Path="alembic\versions"; Label="migrations"},
    @{Path="alembic.ini"; Label="config alembic"},
    @{Path="logo.png"; Label="logo"}
)

foreach ($Res in $Resources) {
    $FullPath = Join-Path $ProjectRoot $Res.Path
    if (-not (Test-Path -LiteralPath $FullPath)) {
        Write-Host "ERRO: $($Res.Label) nao encontrado em $FullPath" -ForegroundColor Red
        exit 1
    }
    Write-Host "  OK $($Res.Label)" -ForegroundColor Green
}

# 3. Limpa builds anteriores
Remove-Item -LiteralPath "$ProjectRoot\dist" -Recurse -Force -ErrorAction SilentlyContinue
Remove-Item -LiteralPath "$ProjectRoot\build" -Recurse -Force -ErrorAction SilentlyContinue
Remove-Item -LiteralPath "$ProjectRoot\*.spec" -Force -ErrorAction SilentlyContinue

# 4. Build PyInstaller (--onedir)
Write-Host "`nGerando executavel (pode levar alguns minutos)..." -ForegroundColor Yellow

$PyInstaller = "$VenvDir\Scripts\pyinstaller.exe"
$CommonArgs = @(
    "--onedir"
    "--windowed"
    "--noupx"
    "--add-data", "themes;themes"
    "--add-data", "alembic;alembic"
    "--add-data", "logo.png;."
    "--add-data", "alembic.ini;."
    "--hidden-import", "app.models"
    "--hidden-import", "app.services"
    "--hidden-import", "app.views"
    "--hidden-import", "app.utils"
    "--hidden-import", "alembic.config"
    "--hidden-import", "alembic.command"
    "--hidden-import", "alembic.runtime.environment"
    "--hidden-import", "dotenv"
    "--hidden-import", "logging.config"
    "--hidden-import", "matplotlib.backends.backend_qtagg"
    "--hidden-import", "matplotlib.backends.backend_agg"
    "--name", "ControleImpressoras"
    "main.py"
)

& $PyInstaller $CommonArgs 2>&1
if ($LASTEXITCODE -ne 0 -and $LASTEXITCODE -ne $null) {
    Write-Host "Falha no PyInstaller!" -ForegroundColor Red
    exit 1
}

# 5. Verifica resultado
$ExeDir = Join-Path $ProjectRoot "dist\ControleImpressoras"
$ExePath = Join-Path $ExeDir "ControleImpressoras.exe"
if (Test-Path -LiteralPath $ExePath) {
    $Size = "{0:N0}" -f ((Get-Item $ExePath).Length / 1MB)
    $TotalSize = "{0:N0}" -f ((Get-ChildItem $ExeDir -Recurse | Measure-Object -Property Length -Sum).Sum / 1MB)
    Write-Host "`nBuild concluido!" -ForegroundColor Green
    Write-Host "   Pasta: dist\ControleImpressoras\" -ForegroundColor Gray
    Write-Host "   .exe:  $Size MB  (total: $TotalSize MB)" -ForegroundColor Gray
    # 6. Gera instalador Inno Setup
    $InnoPath = "$env:LOCALAPPDATA\Programs\Inno Setup 6\ISCC.exe"
    if (Test-Path -LiteralPath $InnoPath) {
        Write-Host "`nGerando instalador Inno Setup..." -ForegroundColor Yellow
        & $InnoPath "setup.iss" 2>&1
        if ($LASTEXITCODE -eq 0) {
            $InstallerSize = "{0:N0}" -f ((Get-Item "$ProjectRoot\dist\ControleImpressoras_Installer.exe").Length / 1MB)
            Write-Host "  OK Instalador: dist\ControleImpressoras_Installer.exe ($InstallerSize MB)" -ForegroundColor Green
        } else {
            Write-Host "  Falha no Inno Setup!" -ForegroundColor Red
        }
    } else {
        Write-Host "`nInno Setup nao encontrado em $InnoPath" -ForegroundColor Yellow
        Write-Host "Instale com: winget install JRSoftware.InnoSetup" -ForegroundColor Yellow
    }
} else {
    Write-Host "`nERRO: executavel nao foi gerado!" -ForegroundColor Red
    exit 1
}
