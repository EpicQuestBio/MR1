# =============================================================================
# MR1 Nanopore Reader ? Windows PowerShell VENV Setup & Manager
# =============================================================================
param (
    [switch]$Recreate,
    [switch]$Check
)

$ErrorActionPreference = "Stop"
$RepoRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
$VenvDir = Join-Path $RepoRoot ".venv"
$ReqFile = Join-Path $RepoRoot "requirements.txt"

Write-Host "=================================================================" -ForegroundColor Cyan
Write-Host "  MR1 Nanopore Reader - Python VENV Setup (Windows)" -ForegroundColor Cyan
Write-Host "=================================================================" -ForegroundColor Cyan

if ($Recreate -and (Test-Path $VenvDir)) {
    Write-Host ">> Removing existing virtual environment at $VenvDir..." -ForegroundColor Yellow
    Remove-Item -Recurse -Force $VenvDir
}

# 1. Locate base Python
$BasePython = (Get-Command python -ErrorAction SilentlyContinue).Source
if (-not $BasePython) {
    Write-Error "Python 3 is not installed or not found on PATH."
    exit 1
}

$PyVer = & $BasePython -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')"
Write-Host "Base Python: $BasePython (v$PyVer)" -ForegroundColor DarkCyan

# 2. Create .venv if not present
if (-not (Test-Path $VenvDir)) {
    Write-Host ">> Creating virtual environment in $VenvDir..." -ForegroundColor Cyan
    & $BasePython -m venv $VenvDir
    Write-Host "[OK] Virtual environment created." -ForegroundColor Green
} else {
    Write-Host ">> Existing virtual environment found at $VenvDir." -ForegroundColor Cyan
}

$VenvPython = Join-Path $VenvDir "Scripts\python.exe"
$VenvPip    = Join-Path $VenvDir "Scripts\pip.exe"
$ActivatePs1 = Join-Path $VenvDir "Scripts\Activate.ps1"

# 3. Upgrade pip
Write-Host ">> Upgrading pip inside venv..."
& $VenvPython -m pip install --quiet --upgrade pip

# 4. Install dependencies
if (Test-Path $ReqFile) {
    Write-Host ">> Installing dependencies from requirements.txt..."
    & $VenvPip install --quiet -r $ReqFile
    Write-Host "[OK] Dependencies installed." -ForegroundColor Green
}

# 5. Check packages
Write-Host "`n--- Installed Packages in VENV ---" -ForegroundColor Cyan
& $VenvPython -c "
for pkg in ['build123d', 'ocp_vscode', 'wireviz', 'platformio']:
    try:
        mod = __import__(pkg)
        ver = getattr(mod, '__version__', 'installed')
        print(f'  [OK] {pkg:15s}: {ver}')
    except ImportError:
        print(f'  [FAIL] {pkg:15s}: NOT INSTALLED')
"

Write-Host "`n=================================================================" -ForegroundColor Green
Write-Host "  Virtual Environment is Ready!" -ForegroundColor Green
Write-Host "=================================================================" -ForegroundColor Green
Write-Host "To activate in PowerShell:"
Write-Host "  & `"$ActivatePs1`"" -ForegroundColor Yellow
Write-Host "To run exports using venv:"
Write-Host "  & `"$VenvPython`" scripts\export_manager.py --all" -ForegroundColor Yellow