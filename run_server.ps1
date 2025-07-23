# PowerShell script to run Django server for cross-device access
# Usage: .\run_server.ps1

Write-Host "Finance Tracker - Multi-Device Server Launcher" -ForegroundColor Green
Write-Host "=================================================" -ForegroundColor Green

$currentDir = Get-Location
Write-Host "Current directory: $currentDir" -ForegroundColor Cyan

if (-not (Test-Path "manage.py")) {
    if (Test-Path "finance_tracker\manage.py") {
        Set-Location "finance_tracker"
        Write-Host "Changed directory to: $(Get-Location)" -ForegroundColor Cyan
    } else {
        Write-Host "Error: Could not find manage.py. Please run this script from the project root directory." -ForegroundColor Red
        exit 1
    }
}

$networkIp = (Get-NetIPAddress | Where-Object {$_.AddressFamily -eq "IPv4" -and $_.PrefixOrigin -eq "Dhcp"}).IPAddress
if (-not $networkIp) {
    $networkIp = "127.0.0.1"
}

Write-Host "`nNetwork Information for Mobile Access:" -ForegroundColor Yellow
Write-Host "-----------------------------------------------------" -ForegroundColor Yellow
Write-Host "Your IP address: $networkIp" -ForegroundColor Yellow
Write-Host "`nMobile Access URL: http://$networkIp`:8000" -ForegroundColor Green
Write-Host "`nCopy this URL to access from your mobile device" -ForegroundColor Cyan
Write-Host "when connected to the same WiFi network." -ForegroundColor Cyan
Write-Host "=================================================" -ForegroundColor Green

$settingsPath = "finance_tracker\settings.py"
if (-not (Test-Path $settingsPath)) {
    $settingsPath = "settings.py"
}

if (Test-Path $settingsPath) {
    $settingsContent = Get-Content $settingsPath -Raw
    
    if ($settingsContent -notmatch "CSRF_TRUSTED_ORIGINS.*$networkIp") {
        if ($settingsContent -match "# CSRF_TRUSTED_ORIGINS \+= \['http://") {
            $settingsContent = $settingsContent -replace "# CSRF_TRUSTED_ORIGINS \+= \['http://.*?:8000'\]", "CSRF_TRUSTED_ORIGINS += ['http://$networkIp`:8000']"
        } else {
            $settingsContent = $settingsContent -replace "(CSRF_TRUSTED_ORIGINS = \[.*?\])", "`$1`nCSRF_TRUSTED_ORIGINS += ['http://$networkIp`:8000']"
        }
        
        $settingsContent | Set-Content $settingsPath
        Write-Host "  Added $networkIp to CSRF_TRUSTED_ORIGINS" -ForegroundColor Green
    } else {
        Write-Host "  $networkIp already in CSRF_TRUSTED_ORIGINS" -ForegroundColor Green
    }
}

Write-Host "`nStarting server on 0.0.0.0:8000..." -ForegroundColor Cyan
Write-Host "-------------------------------------" -ForegroundColor Cyan
Write-Host "Finance Tracker will be accessible at:" -ForegroundColor Yellow
Write-Host "  Local:            http://127.0.0.1:8000" -ForegroundColor Yellow
Write-Host "  On Your Network:  http://$networkIp`:8000" -ForegroundColor Yellow
Write-Host "-------------------------------------" -ForegroundColor Cyan
Write-Host "Press Ctrl+C to stop the server" -ForegroundColor Red
Write-Host ""

python manage.py runserver 0.0.0.0:8000 