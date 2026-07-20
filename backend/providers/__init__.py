"""Provider registry - factor out the right provider by name."""
from backend.providers.base import BaseProvider

_registry: dict[str, type[BaseProvider]] = {}

def register_provider(name: str, cls: type[BaseProvider]) -> None:
    _registry[name] = cls

def get_provider(name: str, **kwargs) -> BaseProvider:
    cls = _registry.get(name)
    if cls is None:
        raise KeyError(f"Unknown provider: {name!r}. Available: {list(_registry)}")
    return cls(**kwargs)

def list_providers() -> list[str]:
    return list(_registry)

# Register Playwright provider
from backend.providers.douyin.provider_playwright import DouyinPlaywrightProvider
register_provider("douyin", DouyinPlaywrightProvider)
print("[providers] Using Playwright Edge provider")
