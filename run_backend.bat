@echo off
cd /d %~dp0
echo Starting Smart Warehouse AI backend on http://127.0.0.1:8000/
py -m uvicorn backend.main:app --host 127.0.0.1 --port 8000
pause
