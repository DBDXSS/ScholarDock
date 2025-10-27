@echo off
chcp 65001 > nul
echo 📋 Real-time log viewer for Google Scholar Spider
echo.
echo Choose which logs to view:
echo [1] Backend logs only
echo [2] Frontend logs only
echo [3] Both logs (split view)
echo [4] Exit
echo.
set /p choice="Enter your choice (1-4): "

if "%choice%"=="1" goto backend
if "%choice%"=="2" goto frontend
if "%choice%"=="3" goto both
if "%choice%"=="4" goto exit
goto invalid

:backend
echo.
echo 📡 Viewing Backend logs (Press Ctrl+C to stop)...
echo ================================================
powershell -Command "Get-Content logs\backend.log -Wait"
goto end

:frontend
echo.
echo 🎨 Viewing Frontend logs (Press Ctrl+C to stop)...
echo ================================================
powershell -Command "Get-Content logs\frontend.log -Wait"
goto end

:both
echo.
echo 📊 Opening both log files in separate windows...
start "Backend Logs" cmd /k "powershell -Command \"Get-Content logs\backend.log -Wait\""
start "Frontend Logs" cmd /k "powershell -Command \"Get-Content logs\frontend.log -Wait\""
echo ✅ Log windows opened
goto end

:invalid
echo ❌ Invalid choice. Please enter 1, 2, 3, or 4.
pause
goto start

:exit
echo 👋 Goodbye!
goto end

:end
pause