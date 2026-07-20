@echo off
chcp 65001 >nul
echo ========================================
echo  Knowledge RAG - 一键安装脚本
echo ========================================
echo.

echo [1/6] 创建 Python 虚拟环境...
python -m venv .venv
call .venv\Scripts\activate.bat

echo [2/6] 安装 Python 依赖...
pip install -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple
if %errorlevel% neq 0 (
    echo 清华镜像失败，尝试直接安装...
    pip install -r requirements.txt
)

echo [3/6] 安装 Playwright 浏览器...
playwright install chromium

echo [4/6] 安装 ffmpeg...
pip install ffmpeg-downloader
python -m ffmpeg_downloader install -y

echo [5/6] 安装前端依赖...
cd frontend
call npm install
cd ..

echo [6/6] 创建配置文件...
copy .env.example .env 2>nul
echo.
echo ========================================
echo  安装完成！
echo.
echo  接下来：
echo  1. 编辑 .env 填入你的 LLM_API_KEY
echo  2. 运行 start.bat 启动服务
echo  3. 打开 http://localhost:3000
echo ========================================
