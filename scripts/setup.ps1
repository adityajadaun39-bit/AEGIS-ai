# AEGIS Automated Environment Bootstrapper (Windows PowerShell)
# Usage: .\scripts\setup.ps1

Write-Host "==========================================================" -ForegroundColor Cyan
Write-Host "   AEGIS Gateway: Automated Developer Environment Setup   " -ForegroundColor Cyan
Write-Host "==========================================================" -ForegroundColor Cyan

$PythonCmd = Get-Command python -ErrorAction SilentlyContinue
if (-not $PythonCmd) {
    Write-Host "[ERROR] Python 3.11+ is not found in PATH." -ForegroundColor Red
    exit 1
}

$PyVersion = python --version
Write-Host "[INFO] Detected $PyVersion" -ForegroundColor Green

# 1. Ensure .env exists
if (-not (Test-Path ".env")) {
    Write-Host "[INFO] Creating .env from .env.example..." -ForegroundColor Yellow
    Copy-Item ".env.example" ".env"
} else {
    Write-Host "[INFO] .env already exists." -ForegroundColor Green
}

# 2. Ensure data directory exists
if (-not (Test-Path "data")) {
    New-Item -ItemType Directory -Path "data" | Out-Null
    Write-Host "[INFO] Created data/ directory." -ForegroundColor Green
}

# 3. Install package in editable mode
Write-Host "[INFO] Installing dependencies via pip install -e . ..." -ForegroundColor Yellow
python -m pip install -e .

# 4. Set PYTHONPATH for current session
$env:PYTHONPATH = (Get-Location).Path

# 5. Run sanity verification tests
Write-Host "[INFO] Running verification test suite..." -ForegroundColor Cyan
python -m pytest tests/ -v --tb=short

if ($LASTEXITCODE -eq 0) {
    Write-Host "`n[SUCCESS] AEGIS environment initialized and verified successfully!" -ForegroundColor Green
    Write-Host "Start Backend API:  uvicorn backend.app:app --host 0.0.0.0 --port 8000 --reload" -ForegroundColor White
    Write-Host "Start SOC Console:  streamlit run frontend/dashboard.py --server.port 8501" -ForegroundColor White
} else {
    Write-Host "`n[WARNING] Some tests did not pass. Check output above." -ForegroundColor Yellow
}
