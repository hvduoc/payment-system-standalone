@echo off
echo Starting Payment System Server on Port 8005...
echo ================================================
cd /d "d:\DUAN1\Airbnb\payment-system-standalone"
python -m uvicorn main:app --host 0.0.0.0 --port 8005 --reload
pause