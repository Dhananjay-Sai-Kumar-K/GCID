# Start Backend Server
Write-Host "Starting Gesture Craft Backend..." -ForegroundColor Cyan
Write-Host ""

# Navigate to backend directory
Set-Location backend

# Activate virtual environment
& ..\.venv\Scripts\Activate.ps1

# Start FastAPI server
Write-Host "Backend running at: http://localhost:8000" -ForegroundColor Green
Write-Host "WebSocket endpoint: ws://localhost:8000/ws" -ForegroundColor Green
Write-Host "Health check: http://localhost:8000/health" -ForegroundColor Green
Write-Host ""
Write-Host "Press Ctrl+C to stop the server" -ForegroundColor Yellow
Write-Host ""

python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
