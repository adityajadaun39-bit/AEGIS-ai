# AEGIS Comprehensive Evaluation & Benchmark Suite Runner
# Usage: .\scripts\run_all_evaluations.ps1

Write-Host "==========================================================" -ForegroundColor Cyan
Write-Host "   AEGIS: Full Academic Benchmark & Evaluation Suite      " -ForegroundColor Cyan
Write-Host "==========================================================" -ForegroundColor Cyan

$env:PYTHONPATH = (Get-Location).Path

# Phase 1: Unit & Integration Tests
Write-Host "`n>>> [1/4] Running Full Test Suite (pytest)..." -ForegroundColor Yellow
python -m pytest tests/ -v --tb=short
if ($LASTEXITCODE -ne 0) {
    Write-Host "[FAIL] Unit test suite encountered failures." -ForegroundColor Red
    exit 1
}

# Phase 2: Security Evaluation Matrix (E01 - E10)
Write-Host "`n>>> [2/4] Running Scenario Evaluation Matrix (E01-E10)..." -ForegroundColor Yellow
python evaluation/run_evaluation.py
if ($LASTEXITCODE -ne 0) {
    Write-Host "[FAIL] Evaluation matrix failed." -ForegroundColor Red
    exit 1
}

# Phase 3: Large-Scale Benchmark (300 Scenarios)
Write-Host "`n>>> [3/4] Running 300-Scenario Latency & Accuracy Benchmark..." -ForegroundColor Yellow
python evaluation/run_benchmark.py
if ($LASTEXITCODE -ne 0) {
    Write-Host "[FAIL] Benchmark suite failed." -ForegroundColor Red
    exit 1
}

# Phase 4: High-Concurrency Load Test (50 Workers, SQLite WAL)
Write-Host "`n>>> [4/4] Running 50-Worker High-Concurrency Load Test..." -ForegroundColor Yellow
python evaluation/run_load_test.py
if ($LASTEXITCODE -ne 0) {
    Write-Host "[FAIL] Concurrency load test failed." -ForegroundColor Red
    exit 1
}

Write-Host "`n==========================================================" -ForegroundColor Green
Write-Host "   ALL 4 EVALUATION TIERS PASSED WITH 100% SUCCESS RATE   " -ForegroundColor Green
Write-Host "==========================================================" -ForegroundColor Green
Write-Host "Reports generated in evaluation/results/:"
Get-ChildItem -Path "evaluation/results" | ForEach-Object { Write-Host " - $($_.Name) ($($_.Length) bytes)" -ForegroundColor Gray }
