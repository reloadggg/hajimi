from __future__ import annotations

from typing import Any, Dict, Optional
from urllib.parse import urljoin

import app.config.settings as settings


def _get_config() -> Dict[str, Any]:
    config = getattr(settings, "embedding_service", {})
    if not isinstance(config, dict):
        return {}
    return config


def is_configured() -> bool:
    base_url = (_get_config().get("base_url") or "").strip()
    return bool(base_url)


def build_service_url(path_key: str, default_path: str) -> Optional[str]:
    config = _get_config()
    base_url = (config.get("base_url") or "").strip()
    if not base_url:
        return None

    base = base_url.rstrip("/") + "/"
    path = (config.get(path_key) or default_path).lstrip("/")
    return urljoin(base, path)


def build_headers() -> Dict[str, str]:
    config = _get_config()
    headers: Dict[str, str] = {"Content-Type": "application/json"}
    api_key = (config.get("api_key") or "").strip()
    if api_key:
        headers.setdefault("Authorization", f"Bearer {api_key}")
    return headers


def get_timeout(default: float = 60.0) -> float:
    config = _get_config()
    timeout_value = config.get("timeout")
    if timeout_value is None:
        return default
    try:
        return float(timeout_value)
    except (TypeError, ValueError):
        return default
