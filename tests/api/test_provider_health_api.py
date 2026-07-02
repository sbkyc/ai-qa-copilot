from __future__ import annotations


def test_check_provider_health_api(client, monkeypatch):
    monkeypatch.setenv("AI_PROVIDER", "deepseek")
    monkeypatch.setenv("DEEPSEEK_API_KEY", "secret-deepseek-key")

    response = client.get("/api/provider-health")

    assert response.status_code == 200
    payload = response.json()
    assert payload["ok"] is True
    assert payload["provider"] == "deepseek"
    assert payload["api_key_source"] == "DEEPSEEK_API_KEY"
    assert "secret-deepseek-key" not in str(payload)
