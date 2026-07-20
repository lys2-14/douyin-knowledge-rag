"""
Application entry point.
"""
from backend.api.app import create_app
from backend.config.settings import settings

app = create_app()


@app.get("/api/config/check")
async def config_check():
    import os, shutil
    from backend.config.settings import settings
    w = []
    i = {}
    key = settings.llm_api_key or settings.dashscope_api_key or ""
    if not key or key in ("sk-your-api-key", "sk-your-dashscope-key"):
        w.append("LLM_API_KEY not configured")
        i["llm_configured"] = False
    else:
        i["llm_configured"] = True
        i["llm_provider"] = settings.llm_provider
        i["llm_model"] = settings.llm_model
    os.makedirs("data", exist_ok=True)
    os.makedirs(settings.chroma_persist_dir, exist_ok=True)
    has_ffmpeg = shutil.which("ffmpeg") is not None
    i["ffmpeg_installed"] = has_ffmpeg
    if not has_ffmpeg:
        w.append("ffmpeg not installed")
    try:
        from backend.providers.douyin.signer import get_signer
        i["signer"] = type(get_signer()).__name__
    except Exception as e:
        i["signer"] = f"error: {e}"
    return {"status": "ok" if not w else "warning", "info": i, "warnings": w}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "backend.main:app",
        host=settings.app_host,
        port=settings.app_port,
        reload=settings.debug,
    )

