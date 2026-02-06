# Gesture Craft - Quick Start Script
# This script helps you get the application running quickly

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  Gesture Craft - AAA Hand Tracking   " -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# Check Python version
Write-Host "[1/6] Checking Python version..." -ForegroundColor Yellow
$pythonVersion = python --version 2>&1
if ($pythonVersion -match "Python 3\.[9-9]|Python 3\.1[0-9]") {
    Write-Host "✓ Python version OK: $pythonVersion" -ForegroundColor Green
} else {
    Write-Host "✗ Python 3.9+ required. Found: $pythonVersion" -ForegroundColor Red
    exit 1
}

# Check Node.js version
Write-Host "[2/6] Checking Node.js version..." -ForegroundColor Yellow
$nodeVersion = node --version 2>&1
if ($nodeVersion -match "v1[8-9]|v[2-9][0-9]") {
    Write-Host "✓ Node.js version OK: $nodeVersion" -ForegroundColor Green
} else {
    Write-Host "✗ Node.js 18+ required. Found: $nodeVersion" -ForegroundColor Red
    exit 1
}

# Setup Python virtual environment
Write-Host "[3/6] Setting up Python virtual environment..." -ForegroundColor Yellow
if (!(Test-Path ".venv")) {
    python -m venv .venv
    Write-Host "✓ Virtual environment created" -ForegroundColor Green
} else {
    Write-Host "✓ Virtual environment already exists" -ForegroundColor Green
}

# Activate virtual environment and install dependencies
Write-Host "[4/6] Installing Python dependencies..." -ForegroundColor Yellow
& .venv\Scripts\Activate.ps1
pip install -r requirements.txt --quiet
Write-Host "✓ Python dependencies installed" -ForegroundColor Green

# Install Node.js dependencies
Write-Host "[5/6] Installing Node.js dependencies..." -ForegroundColor Yellow
Set-Location frontend-aaa
if (!(Test-Path "node_modules")) {
    npm install --silent
    Write-Host "✓ Node.js dependencies installed" -ForegroundColor Green
} else {
    Write-Host "✓ Node.js dependencies already installed" -ForegroundColor Green
}
Set-Location ..

Write-Host "[6/6] Setup complete!" -ForegroundColor Green
Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  Ready to Launch!                     " -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "To start the application:" -ForegroundColor White
Write-Host ""
Write-Host "Option 1: Web Browser Mode" -ForegroundColor Yellow
Write-Host "  Terminal 1: .\start-backend.ps1" -ForegroundColor White
Write-Host "  Terminal 2: .\start-frontend.ps1" -ForegroundColor White
Write-Host ""
Write-Host "Option 2: Electron Desktop App" -ForegroundColor Yellow
Write-Host "  Terminal 1: .\start-backend.ps1" -ForegroundColor White
Write-Host "  Terminal 2: .\start-electron.ps1" -ForegroundColor White
Write-Host ""
Write-Host "Script execution finished." -ForegroundColor Gray
