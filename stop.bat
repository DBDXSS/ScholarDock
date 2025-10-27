@echo off
chcp 65001 > nul
echo 🛑 Stopping Google Scholar Spider services...

echo Stopping backend (port 8001)...
REM Kill processes using port 8001
for /f "tokens=5" %%a in ('netstat -aon ^| findstr :8001') do (
    taskkill /f /pid %%a > nul 2>&1
)

REM Kill uvicorn processes
taskkill /f /im python.exe /fi "WINDOWTITLE eq Backend Server" > nul 2>&1

echo Stopping frontend (port 3000)...
REM Kill processes using port 3000
for /f "tokens=5" %%a in ('netstat -aon ^| findstr :3000') do (
    taskkill /f /pid %%a > nul 2>&1
)

REM Kill vite/node processes
taskkill /f /im node.exe /fi "WINDOWTITLE eq Frontend Server" > nul 2>&1

REM Kill any remaining node processes that might be running vite
wmic process where "name='node.exe' and commandline like '%%vite%%'" delete > nul 2>&1

echo ✅ Services stopped
pause