<#
.SYNOPSIS
Starts the Langfuse local observability stack using the Harbor CLI within WSL2.

.DESCRIPTION
This script is a Windows-friendly wrapper for the Harbor CLI. Since Harbor is designed
for Linux/WSL2 and does not run natively in Windows PowerShell, this script passes the
command through to your default WSL distribution.
#>

Write-Host "🚀 Starting CoReason Observability Stack (Langfuse via Harbor)..." -ForegroundColor Cyan

# Check if WSL is available
if (-not (Get-Command wsl -ErrorAction SilentlyContinue)) {
    Write-Host "[ERROR] WSL is not installed on this system. Harbor requires WSL2." -ForegroundColor Red
    Write-Host "Please install WSL2 by running 'wsl --install' as Administrator." -ForegroundColor Yellow
    exit 1
}

# Run harbor through WSL
Write-Host "Forwarding command to WSL2: harbor up langfuse" -ForegroundColor Gray
$result = wsl --exec bash -lc "harbor --version >/dev/null 2>&1"
if ($LASTEXITCODE -ne 0) {
    Write-Host "[INFO] Harbor CLI is not installed in WSL. Installing automatically..." -ForegroundColor Yellow
    wsl --exec bash -lc "curl -fsSL https://raw.githubusercontent.com/av/harbor/refs/heads/main/install.sh | bash -s -- --skip-requirements"
    if ($LASTEXITCODE -ne 0) {
        Write-Host "[ERROR] Failed to install Harbor CLI." -ForegroundColor Red
        exit 1
    }
    Write-Host "[INFO] Harbor installed successfully!" -ForegroundColor Green
}

# Actually run the up command (use login shell to source bashrc/profile)
wsl --exec bash -lc "harbor up langfuse"
if ($LASTEXITCODE -eq 0) {
    Write-Host "`n✅ Observability Stack Started Successfully!" -ForegroundColor Green
    Write-Host "Langfuse UI should now be available at http://localhost:3000" -ForegroundColor Cyan
} else {
    Write-Host "`n❌ Failed to start observability stack." -ForegroundColor Red
}
