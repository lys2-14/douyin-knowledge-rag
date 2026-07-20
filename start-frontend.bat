@echo off
chcp 65001 > nul
echo ========================================
echo  📚 Knowledge RAG - Frontend
echo ========================================
echo.
cd /d "%~dp0frontend"
echo Starting frontend dev server...
echo.
call npm run dev
if errorlevel 1 (
    echo.
    echo ❌ Failed to start. Run 'npm install' first.
    pause
)
