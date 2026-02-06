# Start Electron Desktop App
Write-Host "Starting Gesture Craft (Electron Desktop)..." -ForegroundColor Cyan
Write-Host ""

Set-Location frontend-aaa

Write-Host "Launching Electron desktop application..." -ForegroundColor Green
Write-Host ""
Write-Host "Note: Make sure the backend is running!" -ForegroundColor Yellow
Write-Host "Backend should be at: ws://localhost:8000/ws" -ForegroundColor Yellow
Write-Host ""
Write-Host "Press Ctrl+C to stop the application" -ForegroundColor Yellow
Write-Host ""

npm run electron:dev
