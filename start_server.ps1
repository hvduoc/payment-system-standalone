# Payment System Server Startup Script
Write-Host "Starting Payment System Server on Port 8005..." -ForegroundColor Green
Write-Host "================================================" -ForegroundColor Yellow

Set-Location "d:\DUAN1\Airbnb\payment-system-standalone"

Write-Host "Server will be available at: http://localhost:8005" -ForegroundColor Cyan
Write-Host "Admin Panel: http://localhost:8005/admin/handovers" -ForegroundColor Cyan
Write-Host ""

python -m uvicorn main:app --host 0.0.0.0 --port 8005 --reload