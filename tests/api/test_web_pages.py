from __future__ import annotations

from tests.helpers import clear_provider_env


def get_signed_in_products_page(client):
    client.cookies.set("qa_user", "alice")
    return client.get("/products")


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

    response = get_signed_in_products_page(client)

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

    response = get_signed_in_products_page(client)

    assert response.status_code == 200
    assert "Provider Status" in response.text
    assert "Missing base URL" in response.text
    assert "Add AI_BASE_URL for OpenAI-compatible gateways." in response.text


def test_products_page_shows_unsupported_provider_status(client, monkeypatch):
    clear_provider_env(monkeypatch)
    monkeypatch.setenv("AI_PROVIDER", "deepssek")
    monkeypatch.setenv("AI_API_KEY", "fake-key")

    response = get_signed_in_products_page(client)

    assert response.status_code == 200
    assert "Provider Status" in response.text
    assert "Unsupported provider" in response.text
    assert "Check the AI_PROVIDER spelling." in response.text
    assert "fake-key" not in response.text


def test_products_page_shows_unsupported_api_style_status(client, monkeypatch):
    clear_provider_env(monkeypatch)
    monkeypatch.setenv("AI_PROVIDER", "deepseek")
    monkeypatch.setenv("DEEPSEEK_API_KEY", "fake-deepseek-key")
    monkeypatch.setenv("AI_API_STYLE", "chta")

    response = get_signed_in_products_page(client)

    assert response.status_code == 200
    assert "Provider Status" in response.text
    assert "Unsupported API style" in response.text
    assert "Use AI_API_STYLE=chat or AI_API_STYLE=responses." in response.text
    assert "fake-deepseek-key" not in response.text
