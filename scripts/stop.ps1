# AEGIS Service Stopper (Windows PowerShell)
# Usage: powershell -ExecutionPolicy Bypass -File .\scripts\stop.ps1

Write-Host "Stopping AEGIS Gateway and SOC Console processes..." -ForegroundColor Yellow

$Connections = Get-NetTCPConnection -LocalPort 8000, 8501 -State Listen -ErrorAction SilentlyContinue
if ($Connections) {
    $Pids = $Connections.OwningProcess | Select-Object -Unique
    foreach ($pid_to_stop in $Pids) {
        try {
            Stop-Process -Id $pid_to_stop -Force -ErrorAction SilentlyContinue
            Write-Host " - Terminated process PID $pid_to_stop" -ForegroundColor Green
        } catch {
            Write-Host " - Could not stop PID $pid_to_stop : $_" -ForegroundColor Red
        }
    }
    Write-Host "[SUCCESS] All AEGIS services on ports 8000 and 8501 stopped." -ForegroundColor Green
} else {
    Write-Host "[INFO] No active AEGIS services found on ports 8000 or 8501." -ForegroundColor Cyan
}
