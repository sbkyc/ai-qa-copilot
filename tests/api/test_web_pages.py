from __future__ import annotations


def test_login_page_renders(client):
    response = client.get("/")

    assert response.status_code == 200
    assert "AI QA Demo Shop" in response.text


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
