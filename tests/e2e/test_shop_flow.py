from __future__ import annotations

import pytest
from playwright.sync_api import Page, expect


@pytest.mark.e2e
def test_user_can_login_and_create_order(page: Page, live_server: str):
    page.goto(live_server)

    expect(page.get_by_role("heading", name="AI QA Demo Shop")).to_be_visible()
    page.get_by_label("Username").fill("alice")
    page.get_by_label("Password").fill("password123")
    page.get_by_role("button", name="Sign in").click()

    expect(page.get_by_role("heading", name="Products")).to_be_visible()
    provider_status = page.get_by_role("region", name="Provider Status")
    expect(provider_status.get_by_role("heading", name="Provider Status")).to_be_visible()
    expect(provider_status.locator(".provider-status-summary")).to_have_text(
        "Missing API key"
    )
    first_product = page.get_by_role("article").filter(has_text="Wireless Mouse")
    first_product.get_by_role("button", name="Create order").click()

    expect(page.get_by_role("heading", name="Order Created")).to_be_visible()
    expect(page.get_by_text("alice ordered 1 x Wireless Mouse.")).to_be_visible()


@pytest.mark.e2e
def test_user_sees_error_for_bad_login(page: Page, live_server: str):
    page.goto(live_server)

    page.get_by_label("Username").fill("alice")
    page.get_by_label("Password").fill("bad-password")
    page.get_by_role("button", name="Sign in").click()

    expect(page.get_by_role("alert")).to_have_text("Invalid username or password")
