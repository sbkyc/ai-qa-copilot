from __future__ import annotations

from qa_copilot.provider_health import check_provider_health


def test_check_provider_health_reports_missing_key(monkeypatch):
    monkeypatch.setenv("AI_PROVIDER", "deepseek")
    monkeypatch.delenv("AI_API_KEY", raising=False)
    monkeypatch.delenv("DEEPSEEK_API_KEY", raising=False)

    health = check_provider_health()

    assert health["ok"] is False
    assert health["provider"] == "deepseek"
    assert health["api_style"] == "chat"
    assert health["missing"] == ["api_key"]


def test_check_provider_health_reports_configured_provider_without_leaking_key(monkeypatch):
    monkeypatch.setenv("AI_PROVIDER", "deepseek")
    monkeypatch.setenv("DEEPSEEK_API_KEY", "secret-deepseek-key")

    health = check_provider_health()

    assert health["ok"] is True
    assert health["provider"] == "deepseek"
    assert health["model"] == "deepseek-chat"
    assert health["base_url"] == "https://api.deepseek.com"
    assert health["api_style"] == "chat"
    assert health["api_key_configured"] is True
    assert health["api_key_source"] == "DEEPSEEK_API_KEY"
    assert "secret-deepseek-key" not in str(health)
