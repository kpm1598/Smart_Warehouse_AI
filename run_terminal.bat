@echo off
cd /d %~dp0
echo Starting Smart Warehouse AI terminal...
echo The backend must be running first (run_backend.bat).
py -m terminal.main
pause
