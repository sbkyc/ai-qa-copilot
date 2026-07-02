from __future__ import annotations

from tests.helpers import clear_provider_env


def test_login_page_renders(client):
    response = client.get("/")

    assert response.status_code == 200
    assert "AI QA Demo Shop" in response.text


def test_login_page_links_stylesheet(client):
    response = client.get("/")

    assert response.status_code == 200
    assert 'href="/static/styles.css"' in response.text


def test_web_login_redirects_to_products(client):
    response = client.post(
        "/login",
        data={"username": "alice", "password": "password123"},
        follow_redirects=False,
    )

    assert response.status_code == 303
    assert response.headers["location"] == "/products"


def test_products_page_requires_login(client):
    response = client.get("/products", follow_redirects=False)

    assert response.status_code == 303
    assert response.headers["location"] == "/"


def test_products_page_shows_redacted_provider_status(client, monkeypatch):
    clear_provider_env(monkeypatch)
    monkeypatch.setenv("AI_PROVIDER", "openai-compatible")
    monkeypatch.setenv("AI_API_KEY", "fake-gateway-key")
    monkeypatch.setenv("AI_MODEL", "tenant-routed-model")
    monkeypatch.setenv("AI_BASE_URL", "https://tenant.internal.example/v1")
    client.cookies.set("qa_user", "alice")

    response = client.get("/products")

    assert response.status_code == 200
    assert "Provider Status" in response.text
    assert "Ready" in response.text
    assert "openai-compatible" in response.text
    assert "chat" in response.text
    assert "fake-gateway-key" not in response.text
    assert "AI_API_KEY" not in response.text
    assert "tenant-routed-model" not in response.text
    assert "tenant.internal.example" not in response.text


def test_products_page_shows_missing_base_url_provider_status(client, monkeypatch):
    clear_provider_env(monkeypatch)
    monkeypatch.setenv("AI_PROVIDER", "openai-compatible")
    monkeypatch.setenv("AI_API_KEY", "fake-gateway-key")
    client.cookies.set("qa_user", "alice")

    response = client.get("/products")

    assert response.status_code == 200
    assert "Provider Status" in response.text
    assert "Missing base URL" in response.text
    assert "Add AI_BASE_URL for OpenAI-compatible gateways." in response.text
