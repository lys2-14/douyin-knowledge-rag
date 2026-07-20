@echo off
chcp 65001 >nul
echo ========================================
echo  Knowledge RAG - 启动
echo ========================================
echo.

echo Starting backend...
start "backend" cmd /c ".venv\Scripts\python.exe -m uvicorn backend.main:app --host 127.0.0.1 --port 8000"

echo Starting frontend...
cd frontend
start "frontend" cmd /c "npm run dev"
cd ..

echo.
echo Backend:  http://127.0.0.1:8000
echo Frontend: http://localhost:3000
echo.
pause
