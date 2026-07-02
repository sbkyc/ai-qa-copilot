from __future__ import annotations

import os
from typing import Any

from qa_copilot.providers import PROVIDER_PRESETS, DiagnosisProviderConfig


def _configured_key_source(provider: str) -> str | None:
    preset = PROVIDER_PRESETS.get(provider, PROVIDER_PRESETS["openai"])
    for name in ("AI_API_KEY", *preset.api_key_env_names):
        if os.getenv(name, "").strip():
            return name
    return None


def check_provider_health() -> dict[str, Any]:
    config = DiagnosisProviderConfig.from_env()
    key_source = _configured_key_source(config.provider)
    missing: list[str] = []
    if not config.api_key:
        missing.append("api_key")
    if not config.model:
        missing.append("model")
    if config.api_style == "chat" and not config.base_url:
        missing.append("base_url")

    return {
        "ok": not missing,
        "provider": config.provider,
        "model": config.model,
        "base_url": config.base_url,
        "api_style": config.api_style,
        "api_key_configured": bool(config.api_key),
        "api_key_source": key_source,
        "missing": missing,
    }
