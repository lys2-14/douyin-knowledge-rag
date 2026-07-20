from backend.config.settings import settings


def test_settings_defaults():
    assert settings.app_name == "Knowledge RAG"
    assert settings.provider == "douyin"
