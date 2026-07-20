@echo off
chcp 65001 > nul
echo ========================================
echo  📚 Knowledge RAG - Backend
echo ========================================
echo.
cd /d "%~dp0"
echo Starting backend server...
python -m backend.main
if errorlevel 1 (
    echo.
    echo ❌ Failed to start. Is Python installed?
    pause
)
