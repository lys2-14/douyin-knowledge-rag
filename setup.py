#!/usr/bin/env python3
"""
Knowledge RAG 鈥?涓€閿畨瑁呴厤缃剼鏈?璺ㄥ钩鍙板彲鐢?(Windows / macOS / Linux)
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

# Windows 涓?ANSI 鍙兘涓嶆敮鎸?if sys.platform == "win32":
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
        print(f"  鈫?{desc}...", end=" ", flush=True)
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
    echo("  馃摎 Knowledge RAG 鈥?瀹夎閰嶇疆鍚戝", CYAN)
    echo("=" * 55, CYAN)
    print()

    # 鈹€鈹€ 0. 鐜妫€鏌?鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€
    echo("銆?/5銆戠幆澧冩鏌?)

    py_ok = check_installed("python3", [sys.executable, "--version"])
    if not py_ok:
        echo("  鉂?Python 鏈畨瑁咃紝璇峰厛瀹夎 Python 3.10+", RED)
        sys.exit(1)
    echo(f"  鉁?Python {sys.version.split()[0]}", GREEN)

    pip_ok = run([sys.executable, "-m", "pip", "--version"], "pip")
    if not pip_ok:
        echo("  鈿狅笍  pip 涓嶅彲鐢紝灏濊瘯瀹夎...", YELLOW)
        run([sys.executable, "-m", "ensurepip", "--upgrade"])

    has_ffmpeg = check_installed("ffmpeg", ["ffmpeg", "-version"])
    if has_ffmpeg:
        echo("  鉁?ffmpeg", GREEN)
    else:
        echo("  鈿狅笍  ffmpeg 鏈壘鍒?(闊抽澶勭悊闇€瑕侊紝鍙◢鍚庡畨瑁?", YELLOW)

    has_node = check_installed("node", ["node", "--version"])
    has_npm = check_installed("npm", ["npm", "--version"])
    if has_node and has_npm:
        node_v = subprocess.run(["node", "--version"], capture_output=True, text=True).stdout.strip()
        echo(f"  鉁?Node {node_v}", GREEN)
    else:
        echo("  鈿狅笍  Node.js 鏈畨瑁?(鍓嶇闇€瑕侊紝鍙◢鍚庡畨瑁?", YELLOW)

    print()

    # 鈹€鈹€ 1. 閰嶇疆 .env 鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€
    echo("銆?/5銆慉PI 閰嶇疆")

    env_path = ROOT / ".env"
    env_example = ROOT / ".env.example"

    if env_path.exists():
        echo("  鉁?.env 宸插瓨鍦紝璺宠繃", GREEN)
    elif env_example.exists():
        shutil.copy(str(env_example), str(env_path))
        echo("  鉁?宸蹭粠 .env.example 鍒涘缓 .env", GREEN)
    else:
        echo("  鈩癸笍  鏈壘鍒?.env.example锛屾墜鍔ㄥ垱寤虹┖閰嶇疆", YELLOW)
        env_path.write_text("")

    # 鎻愮ず杈撳叆 API Key
    current_key = ""
    if env_path.exists():
        for line in env_path.read_text().splitlines():
            if line.startswith("LLM_API_KEY="):
                current_key = line.split("=", 1)[1].strip()
                break

    if not current_key or current_key == "YOUR_API_KEY_HERE":
        echo("\n  馃攽 闇€瑕侀厤缃?LLM API Key")
        echo("     鎺ㄨ崘浣跨敤闃块噷浜戠櫨鐐?(DashScope) 鎴?OpenAI 鍏煎鎺ュ彛")
        echo("     娉ㄥ唽鍦板潃: https://bailian.console.aliyun.com/")
        key = prompt("  璇疯緭鍏ヤ綘鐨?API Key", "")
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
            echo("  鉁?API Key 宸蹭繚瀛?, GREEN)

    print()

    # 鈹€鈹€ 2. 瀹夎 Python 渚濊禆 鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€
    echo("銆?/5銆戝畨瑁?Python 渚濊禆")
    req = ROOT / "requirements.txt"
    if req.exists():
        ok = run(
            [sys.executable, "-m", "pip", "install", "-r", str(req)],
            "pip install -r requirements.txt"
        )
        if not ok:
            echo("  鈿狅笍  閮ㄥ垎渚濊禆瀹夎澶辫触锛屽彲绋嶅悗鎵嬪姩閲嶈瘯", YELLOW)
    else:
        echo("  鈿狅笍  鏈壘鍒?requirements.txt", YELLOW)

    print()

    # 鈹€鈹€ 3. 瀹夎鍓嶇渚濊禆 鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€
    echo("銆?/5銆戝畨瑁呭墠绔緷璧?)
    if has_node and has_npm:
        frontend_dir = ROOT / "frontend"
        if (frontend_dir / "package.json").exists():
            # 妫€娴嬩腑鍥藉ぇ闄嗙綉缁滐紝浣跨敤娣樺疂闀滃儚
            npmrc = frontend_dir / ".npmrc"
            if not npmrc.exists():
                echo("  鈩癸笍  妫€娴嬪埌涓浗澶ч檰缃戠粶锛屼娇鐢ㄦ窐瀹濋暅鍍忓姞閫?, YELLOW)
                npmrc.write_text("registry=https://registry.npmmirror.com/\n")

            ok = run(
                ["npm", "install", "--no-audit", "--no-fund"],
                "npm install",
                cwd=str(frontend_dir),
            )
            if not ok:
                echo("  鈿狅笍  鍓嶇渚濊禆瀹夎澶辫触锛屽彲绋嶅悗 cd frontend && npm install", YELLOW)
    else:
        echo("  鈿狅笍  Node.js 鏈畨瑁咃紝璺宠繃鍓嶇 (鍙◢鍚庡畨瑁?", YELLOW)

    print()

    # 鈹€鈹€ 4. 鍒涘缓鏁版嵁鐩綍 鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€
    echo("銆?/5銆戝垱寤烘暟鎹洰褰?)
    for d in ["data", "logs", "cache/audio", "cache/transcript", "cache/thumbnails"]:
        (ROOT / d).mkdir(parents=True, exist_ok=True)
    echo("  鉁?鐩綍宸插垱寤?, GREEN)

    print()

    # 鈹€鈹€ 5. 瀹屾垚 鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€
    echo("銆?/5銆戝畨瑁呭畬鎴?", GREEN)
    print()
    echo("=" * 55, CYAN)
    echo("  鍚姩鏂瑰紡:", CYAN)
    echo("=" * 55, CYAN)
    print()
    echo("  鍚庣鏈嶅姟:")
    echo(f"    cd {ROOT}")
    echo("    python -m backend.main")
    print()
    echo("  鍓嶇鐣岄潰 (鏂板紑涓€涓粓绔?:")
    echo(f"    cd {ROOT}/frontend")
    echo("    npm run dev")
    print()
    echo("  娴忚鍣ㄦ墦寮€:")
    echo("    鍚庣鏂囨。: http://127.0.0.1:8000/docs")
    echo("    鍓嶇椤甸潰: http://127.0.0.1:3000")
    print()
    echo("  鐧诲綍鏂瑰紡:")
    echo("    1. 鍦ㄦ祻瑙堝櫒鎵撳紑 douyin.com 骞剁櫥褰?)
    echo("    2. 鎸?F12 鈫?Network 鈫?鍒锋柊椤甸潰 鈫?鐐逛换鎰忚姹?)
    echo("    3. 澶嶅埗 Request Headers 閲岀殑 Cookie 鍊?)
    echo("    4. 鍦ㄧ櫥褰曢〉闈㈢矘璐?Cookie")
    print()
    echo("  闇€瑕佸府鍔?:")
    echo("    https://github.com/浣犵殑鐢ㄦ埛鍚?knowledge-rag")
    print()


if __name__ == "__main__":
    main()

