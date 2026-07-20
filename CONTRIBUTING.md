# Contributing

感谢你考虑为 Knowledge RAG 贡献代码！

## 开发环境

```bash
# 克隆仓库
git clone <your-fork-url>
cd knowledge-rag

# 安装依赖
pip install -r requirements.txt
pip install -r requirements-dev.txt  # 开发依赖
playwright install chromium
pip install ffmpeg-downloader
python -m ffmpeg_downloader install -y
cd frontend && npm install
cd ..

# 配置环境变量
cp .env.example .env
# 编辑 .env 填入 LLM_API_KEY
```

## 代码规范

- Python：遵循 [PEP 8](https://peps.python.org/pep-0008/)，使用 ruff 检查
- TypeScript：遵循项目已有的 ESLint 配置
- 提交信息：使用中文或英文，清晰描述改动

## 提交 PR 流程

1. Fork 本仓库
2. 创建特性分支: `git checkout -b feat/my-feature`
3. 提交改动: `git commit -m "feat: add xxx"`
4. 推送到你的 Fork: `git push origin feat/my-feature`
5. 创建 Pull Request

## 开发指南

### 添加新平台支持

1. 在 `backend/providers/` 下创建新目录
2. 实现 `BaseProvider` 接口（6 个方法）
3. 在 `backend/providers/__init__.py` 注册

### 修改数据处理流程

1. 在 `backend/pipeline/` 中创建新 Stage
2. 继承 `PipelineStage` 基类
3. 在 `backend/pipeline/__init__.py` 注册到 `build_sync_pipeline()`

### 运行测试

```bash
pytest tests/ -v
```

## 架构说明

详见 [README.md](README.md) 系统架构部分。
