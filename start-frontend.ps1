# Start Frontend (Web Browser Mode)
Write-Host "Starting Gesture Craft Frontend (Web)..." -ForegroundColor Cyan
Write-Host ""

Set-Location frontend-aaa

Write-Host "Frontend running at: http://localhost:5173" -ForegroundColor Green
Write-Host ""
Write-Host "Press Ctrl+C to stop the server" -ForegroundColor Yellow
Write-Host ""

npm run dev
