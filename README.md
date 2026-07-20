# Knowledge RAG

> 把你的收藏夹变成可对话的 AI 知识库

## 它能做什么

把抖音收藏夹变成可以用自然语言提问的个人知识库。
流程：粘贴Cookie → 自动同步 → 每视频(下载音频→语音转文字→AI摘要→向量化) → 你可以对知识库提问。

## 快速开始 (5分钟)

### 1. 前置条件
- Python 3.12
- Node.js 18+
- Microsoft Edge

### 2. 安装
```bash
# 方式一：一键安装
python setup.py     # Linux/Mac
setup.bat           # Windows

# 方式二：手动安装
pip install -r requirements.txt
playwright install chromium
pip install ffmpeg-downloader
python -m ffmpeg_downloader install -y
cd frontend && npm install
cp .env.example .env
# 编辑 .env, 填入 LLM_API_KEY
```

### 3. 启动
```bash
# 终端1 - 后端
python -m uvicorn backend.main:app --host 127.0.0.1 --port 8000 --reload

# 终端2 - 前端
cd frontend && npm run dev
```

打开 http://localhost:3000

### 4. 获取抖音Cookie并登录
1. 在Edge中打开 https://www.douyin.com/favorites 并登录
2. F12 → Network → 刷新页面 → 点任意请求
3. 在 Request Headers 找到 Cookie 字段
4. 复制完整Cookie值 (以 sessionid=xxx; 开头)
5. 粘贴到登录页 -> 点登录

> Cookie 有效期较短(几小时~几天),过期需重新复制。

## 配置说明

| 变量 | 说明 | 默认值 |
|------|------|--------|
| LLM_API_KEY | 必填: API Key | - |
| LLM_MODEL | 模型名 | deepseek-chat |
| LLM_BASE_URL | API地址 | https://api.deepseek.com |
| EMBEDDING_PROVIDER | 嵌入方式(local/dashscope) | local |
| ASR_PROVIDER | 语音识别方式(local/dashscope) | local |
| ASR_MODEL | Whisper模型大小(base/small/medium) | base |
| HF_ENDPOINT | HF镜像(大陆必填) | https://hf-mirror.com |

完整配置见 .env.example

## Docker部署
```bash
docker compose up -d
```

## 中国大陆用户注意

### 网络镜像(已内置)
- PyPI: 安装时加 -i https://pypi.tuna.tsinghua.edu.cn/simple
- npm: 已配置 .npmrc 使用 npmmirror.com
- HuggingFace: .env 已配置 HF_ENDPOINT=https://hf-mirror.com

### 模型下载(自动)
- 首次同步: BGE-small-zh-v1.5 (400MB, 用于嵌入)
- 首语音识别: faster-whisper-base (150MB)
均从 hf-mirror.com 镜像下载。

## 常见问题

**同步进度一直是0？** 首次需下载 Whisper 模型(~150MB),等1-2分钟。
**登录提示Cookie无效？** Cookie过期,重新登录douyin.com再复制。
**弹出Edge端口/验证码？** 正常,验证Cookie后自动关闭。
**视频没有语音识别？** 部分视频版权保护无法下载音频,自动使用标题+描述。
**ffmpeg没装？** 运行: pip install ffmpeg-downloader && python -m ffmpeg_downloader install -y
**怎么换LLM？** 修改.env中的LLM_PROVIDER/BASE_URL/API_KEY,支持OpenAI兼容API。

## 技术栈

后端: Python 3.12 / FastAPI / SQLAlchemy / loguru
前端: Next.js 16 / React 19 / Tailwind CSS 4
LLM: OpenAI兼容协议 (DeepSeek / DashScope / Ollama)
向量库: ChromaDB
浏览器: Playwright + Edge
语音: faster-whisper (本地)
嵌入: BGE-small-zh (本地)
音频下载: yt-dlp + ffmpeg
数据库: SQLite (aiosqlite)

## License

MIT

## Docker 部署

### 前提条件
- Docker 24+
- Docker Compose V2+

### 快速部署

```bash
# 1. 克隆仓库
git clone https://github.com/你的用户名/knowledge-rag.git
cd knowledge-rag

# 2. 配置环境变量
cp .env.example .env
# 编辑 .env，填入 LLM_API_KEY

# 3. 启动所有服务
docker compose up -d

# 4. 查看日志
docker compose logs -f
```

启动后访问 http://localhost:3000

### 服务结构

| 服务 | 端口 | 说明 |
|------|------|------|
| backend | 8000 | FastAPI 后端（含 Playwright + ffmpeg + ChromaDB）
| frontend | 3000 | Next.js 前端界面

后端容器内置 ffmpeg，无需额外安装。

### 数据持久化

```bash
# 数据目录映射到宿主机
docker compose volumes:
  - ./data:/app/data       # SQLite DB + ChromaDB
  - ./cache:/app/cache     # 音频缓存 + 转录缓存
  - ./logs:/app/logs       # 日志
```

### 单独构建

```bash
# 只构建后端
docker build -t knowledge-rag-backend . -f docker/Dockerfile

# 只构建前端
docker build -t knowledge-rag-frontend frontend -f docker/frontend.Dockerfile

# 手动运行后端
docker run -p 8000:8000 --env-file .env -v ./data:/app/data knowledge-rag-backend
```

### 模型下载说明

Docker 容器首次运行时需要下载模型（共约 550MB）：
- **BGE-small-zh-v1.5** (400MB) — 文本嵌入，用于向量检索
- **faster-whisper-base** (150MB) — 中文语音识别

使用 HuggingFace 镜像 `hf-mirror.com` 加速下载（已配置在 .env 中）。

## 技术栈

| 层级 | 技术 | 版本 | 用途 |
|------|------|------|------|
| 运行环境 | Python | 3.12 | 后端运行时 |
| 运行环境 | Node.js | 20+ | 前端运行时 |
| 后端框架 | FastAPI | 0.115+ | REST API + WebSocket |
| 异步运行时 | Uvicorn | 0.30+ | ASGI 服务器 |
| ORM | SQLAlchemy | 2.0 | 异步数据库访问 |
| 数据库 | SQLite | 3.x | 本地持久化（无需安装） |
|  | aiosqlite | 0.20+ | SQLite 异步驱动 |
| LLM | OpenAI 兼容协议 | - | 支持 DeepSeek / DashScope / Ollama |
| 嵌入模型 | BGE-small-zh | v1.5 | 本地文本向量化（384/512维） |
| 语音识别 | faster-whisper | 1.2 | 本地中文语音转文字 |
| 向量数据库 | ChromaDB | 1.5+ | 本地向量存储与检索 |
| 浏览器 | Playwright | 1.61 | Edge 自动化（绕过反爬） |
| 音频下载 | yt-dlp | 2026+ | 抖音视频音频下载 |
| 音频处理 | ffmpeg | 8.1+ | 音频提取与转码 |
| 前端框架 | Next.js | 16 | React 全栈框架 |
| UI 框架 | React | 19 | 用户界面 |
| 样式 | Tailwind CSS | 4 | Utility-first CSS |
| Markdown 渲染 | react-markdown | - | LLM 回答渲染 |
| 图标 | lucide-react | - | 界面图标 |
| 包管理 | npm | - | 前端依赖 |
| 配置管理 | Pydantic Settings | 2.x | 环境变量验证 |
| 日志 | loguru | - | 结构化日志 |
| 容器化 | Docker | 24+ | 部署 |
| CI/CD | GitHub Actions | - | 自动测试 + Lint |

### 数据处理流水线

```
每个视频的处理流程：

Provider API  →  yt-dlp  →  ffmpeg  →  Whisper  →  DeepSeek  →  Chunk  →  BGE  →  ChromaDB
  (获取列表)   (下载视频)   (提取音频)   (语音转文字)   (AI摘要)   (分块)    (向量化)  (存储)
```

### 查询流程

```
用户提问  →  向量检索(MMR)  →  上下文注入  →  DeepSeek/LLM  →  回答 + 来源引用
```
