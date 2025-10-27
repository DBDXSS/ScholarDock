@echo off
chcp 65001 > nul
echo 🚀 Starting Google Scholar Spider (Background Mode)...

REM Kill any existing processes
taskkill /f /im python.exe /fi "WINDOWTITLE eq *8001*" > nul 2>&1
taskkill /f /im node.exe /fi "WINDOWTITLE eq *3000*" > nul 2>&1

REM Create directories
if not exist "data" mkdir data
if not exist "logs" mkdir logs

echo 📦 Starting backend...
cd backend
REM Start backend completely hidden
powershell -WindowStyle Hidden -Command "python run.py > ../logs/backend.log 2>&1"
cd ..

echo ⏳ Waiting for backend to start...
timeout /t 3 /nobreak > nul

REM Check if backend is running
curl -s http://localhost:8001/api/health > nul 2>&1
if %errorlevel% equ 0 (
    echo ✅ Backend is running
) else (
    echo ❌ Backend failed to start
    pause
    exit /b 1
)

echo 🎨 Starting frontend...
cd frontend
REM Start frontend completely hidden
powershell -WindowStyle Hidden -Command "npm run dev > ../logs/frontend.log 2>&1"
cd ..

echo ⏳ Waiting for frontend to start...
timeout /t 5 /nobreak > nul

echo.
echo ✨ Services started in background!
echo 🌐 Frontend: http://localhost:3000
echo 📡 Backend:  http://localhost:8001
echo 📚 API Docs: http://localhost:8001/docs
echo.
echo 📝 Logs:
echo    Backend: logs\backend.log
echo    Frontend: logs\frontend.log
echo.
echo 💡 To view logs in real-time, run: tail-logs.bat
echo 🛑 To stop services, run: stop.bat
echo.
pause