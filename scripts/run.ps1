# AEGIS One-Click Local Launcher (Windows PowerShell)
# Usage: powershell -ExecutionPolicy Bypass -File .\scripts\run.ps1

Write-Host "==========================================================" -ForegroundColor Cyan
Write-Host "         AEGIS AI Security Gateway & SOC Launcher          " -ForegroundColor Cyan
Write-Host "==========================================================" -ForegroundColor Cyan

$RepoDir = Split-Path -Parent $PSScriptRoot
Set-Location $RepoDir
$env:PYTHONPATH = $RepoDir

# Check existing port bindings
$Existing8000 = Get-NetTCPConnection -LocalPort 8000 -State Listen -ErrorAction SilentlyContinue
$Existing8501 = Get-NetTCPConnection -LocalPort 8501 -State Listen -ErrorAction SilentlyContinue

if ($Existing8000) {
    Write-Host "[INFO] FastAPI is already running on port 8000 (PID: $($Existing8000.OwningProcess[0]))." -ForegroundColor Green
} else {
    Write-Host "[START] Launching FastAPI Gateway on http://127.0.0.1:8000 ..." -ForegroundColor Yellow
    Start-Process -FilePath "python" -ArgumentList "-m uvicorn backend.app:app --host 127.0.0.1 --port 8000" -WindowStyle Minimized
    Start-Sleep -Seconds 2
}

if ($Existing8501) {
    Write-Host "[INFO] Streamlit SOC Console is already running on port 8501 (PID: $($Existing8501.OwningProcess[0]))." -ForegroundColor Green
} else {
    Write-Host "[START] Launching Streamlit SOC Console on http://127.0.0.1:8501 ..." -ForegroundColor Yellow
    Start-Process -FilePath "python" -ArgumentList "-m streamlit run frontend/dashboard.py --server.port 8501 --server.headless true" -WindowStyle Minimized
    Start-Sleep -Seconds 3
}

# Verify endpoints
Write-Host "`n>>> Checking Service Health..." -ForegroundColor Cyan
try {
    $Health = Invoke-RestMethod -Uri "http://127.0.0.1:8000/health" -TimeoutSec 3
    if ($Health.status -eq "healthy") {
        Write-Host "[OK] Gateway Health: HEALTHY (http://127.0.0.1:8000)" -ForegroundColor Green
        Write-Host "     API Swagger Docs: http://127.0.0.1:8000/docs" -ForegroundColor Gray
    }
} catch {
    Write-Host "[WARN] Gateway is still starting up..." -ForegroundColor Yellow
}

Write-Host "[OK] Streamlit SOC Console: http://127.0.0.1:8501" -ForegroundColor Green
Write-Host "[OK] Standalone HTML Presentation Deck: file://$RepoDir/frontend/deck.html" -ForegroundColor Green

Write-Host "`nOpening SOC Console in default browser..." -ForegroundColor Cyan
Start-Process "http://127.0.0.1:8501"

Write-Host "`n==========================================================" -ForegroundColor Green
Write-Host "   AEGIS IS LIVE! Press Ctrl+C or run .\scripts\stop.ps1   " -ForegroundColor Green
Write-Host "==========================================================" -ForegroundColor Green
