#!/usr/bin/env python3
"""
Knowledge RAG — 一键安装配置脚本
跨平台可用 (Windows / macOS / Linux)
"""
from __future__ import annotations

import os
import shutil
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parent
GREEN = "\033[92m"
YELLOW = "\033[93m"
RED = "\033[91m"
CYAN = "\033[96m"
RESET = "\033[0m"

# Windows 下 ANSI 可能不支持
if sys.platform == "win32":
    import ctypes
    kernel32 = ctypes.windll.kernel32
    kernel32.SetConsoleMode(kernel32.GetStdHandle(-11), 7)


def echo(msg: str, color: str = "") -> None:
    print(f"{color}{msg}{RESET}")


def prompt(text: str, default: str = "") -> str:
    if default:
        val = input(f"{CYAN}?{RESET} {text} [{default}]: ").strip()
        return val or default
    return input(f"{CYAN}?{RESET} {text}: ").strip()


def run(cmd: list[str], desc: str = "", cwd: str | None = None) -> bool:
    if desc:
        print(f"  → {desc}...", end=" ", flush=True)
    try:
        subprocess.run(cmd, cwd=cwd or str(ROOT), check=True,
                       capture_output=True, text=True)
        if desc:
            echo("OK", GREEN)
        return True
    except subprocess.CalledProcessError as e:
        if desc:
            echo("FAIL", RED)
        if e.stderr:
            print(f"    {e.stderr.strip()}")
        return False


def check_installed(name: str, cmd: list[str]) -> bool:
    try:
        subprocess.run(cmd, capture_output=True, text=True)
        return True
    except FileNotFoundError:
        return False


def main():
    echo("=" * 55, CYAN)
    echo("  📚 Knowledge RAG — 安装配置向导", CYAN)
    echo("=" * 55, CYAN)
    print()

    # ── 0. 环境检查 ──────────────────────────────────────────────────
    echo("【0/5】环境检查")

    py_ok = check_installed("python3", [sys.executable, "--version"])
    if not py_ok:
        echo("  ❌ Python 未安装，请先安装 Python 3.10+", RED)
        sys.exit(1)
    echo(f"  ✅ Python {sys.version.split()[0]}", GREEN)

    pip_ok = run([sys.executable, "-m", "pip", "--version"], "pip")
    if not pip_ok:
        echo("  ⚠️  pip 不可用，尝试安装...", YELLOW)
        run([sys.executable, "-m", "ensurepip", "--upgrade"])

    has_ffmpeg = check_installed("ffmpeg", ["ffmpeg", "-version"])
    if has_ffmpeg:
        echo("  ✅ ffmpeg", GREEN)
    else:
        echo("  ⚠️  ffmpeg 未找到 (音频处理需要，可稍后安装)", YELLOW)

    has_node = check_installed("node", ["node", "--version"])
    has_npm = check_installed("npm", ["npm", "--version"])
    if has_node and has_npm:
        node_v = subprocess.run(["node", "--version"], capture_output=True, text=True).stdout.strip()
        echo(f"  ✅ Node {node_v}", GREEN)
    else:
        echo("  ⚠️  Node.js 未安装 (前端需要，可稍后安装)", YELLOW)

    print()

    # ── 1. 配置 .env ────────────────────────────────────────────────
    echo("【1/5】API 配置")

    env_path = ROOT / ".env"
    env_example = ROOT / ".env.example"

    if env_path.exists():
        echo("  ✅ .env 已存在，跳过", GREEN)
    elif env_example.exists():
        shutil.copy(str(env_example), str(env_path))
        echo("  ✅ 已从 .env.example 创建 .env", GREEN)
    else:
        echo("  ℹ️  未找到 .env.example，手动创建空配置", YELLOW)
        env_path.write_text("")

    # 提示输入 API Key
    current_key = ""
    if env_path.exists():
        for line in env_path.read_text().splitlines():
            if line.startswith("LLM_API_KEY="):
                current_key = line.split("=", 1)[1].strip()
                break

    if not current_key or current_key == "sk-your-api-key":
        echo("\n  🔑 需要配置 LLM API Key")
        echo("     推荐使用阿里云百炼 (DashScope) 或 OpenAI 兼容接口")
        echo("     注册地址: https://bailian.console.aliyun.com/")
        key = prompt("  请输入你的 API Key", "")
        if key:
            # Update .env
            lines = env_path.read_text().splitlines() if env_path.exists() else []
            found = False
            for i, line in enumerate(lines):
                if line.startswith("LLM_API_KEY="):
                    lines[i] = f"LLM_API_KEY={key}"
                    found = True
                    break
            if not found:
                lines.append(f"LLM_API_KEY={key}")
            env_path.write_text("\n".join(lines))
            echo("  ✅ API Key 已保存", GREEN)

    print()

    # ── 2. 安装 Python 依赖 ─────────────────────────────────────────
    echo("【2/5】安装 Python 依赖")
    req = ROOT / "requirements.txt"
    if req.exists():
        ok = run(
            [sys.executable, "-m", "pip", "install", "-r", str(req)],
            "pip install -r requirements.txt"
        )
        if not ok:
            echo("  ⚠️  部分依赖安装失败，可稍后手动重试", YELLOW)
    else:
        echo("  ⚠️  未找到 requirements.txt", YELLOW)

    print()

    # ── 3. 安装前端依赖 ─────────────────────────────────────────────
    echo("【3/5】安装前端依赖")
    if has_node and has_npm:
        frontend_dir = ROOT / "frontend"
        if (frontend_dir / "package.json").exists():
            # 检测中国大陆网络，使用淘宝镜像
            npmrc = frontend_dir / ".npmrc"
            if not npmrc.exists():
                echo("  ℹ️  检测到中国大陆网络，使用淘宝镜像加速", YELLOW)
                npmrc.write_text("registry=https://registry.npmmirror.com/\n")

            ok = run(
                ["npm", "install", "--no-audit", "--no-fund"],
                "npm install",
                cwd=str(frontend_dir),
            )
            if not ok:
                echo("  ⚠️  前端依赖安装失败，可稍后 cd frontend && npm install", YELLOW)
    else:
        echo("  ⚠️  Node.js 未安装，跳过前端 (可稍后安装)", YELLOW)

    print()

    # ── 4. 创建数据目录 ─────────────────────────────────────────────
    echo("【4/5】创建数据目录")
    for d in ["data", "logs", "cache/audio", "cache/transcript", "cache/thumbnails"]:
        (ROOT / d).mkdir(parents=True, exist_ok=True)
    echo("  ✅ 目录已创建", GREEN)

    print()

    # ── 5. 完成 ─────────────────────────────────────────────────────
    echo("【5/5】安装完成!", GREEN)
    print()
    echo("=" * 55, CYAN)
    echo("  启动方式:", CYAN)
    echo("=" * 55, CYAN)
    print()
    echo("  后端服务:")
    echo(f"    cd {ROOT}")
    echo("    python -m backend.main")
    print()
    echo("  前端界面 (新开一个终端):")
    echo(f"    cd {ROOT}/frontend")
    echo("    npm run dev")
    print()
    echo("  浏览器打开:")
    echo("    后端文档: http://127.0.0.1:8000/docs")
    echo("    前端页面: http://127.0.0.1:3000")
    print()
    echo("  登录方式:")
    echo("    1. 在浏览器打开 douyin.com 并登录")
    echo("    2. 按 F12 → Network → 刷新页面 → 点任意请求")
    echo("    3. 复制 Request Headers 里的 Cookie 值")
    echo("    4. 在登录页面粘贴 Cookie")
    print()
    echo("  需要帮助?:")
    echo("    https://github.com/你的用户名/knowledge-rag")
    print()


if __name__ == "__main__":
    main()

