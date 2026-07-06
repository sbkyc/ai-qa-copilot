from __future__ import annotations

from datetime import UTC, datetime

from qa_copilot.artifacts import FailureArtifact
from qa_copilot.diagnosis import diagnose_with_ai
from qa_copilot.prompt_builder import build_diagnosis_prompt
from tests.helpers import clear_provider_env


class FailingProvider:
    def generate(self, prompt: str) -> str:
        raise TimeoutError("network timeout")


def test_diagnose_with_ai_returns_fallback_when_openai_call_fails(monkeypatch):
    monkeypatch.setenv("OPENAI_API_KEY", "fake-key")

    report = diagnose_with_ai("failure prompt", provider=FailingProvider())

    assert "AI 诊断已跳过" in report
    assert "network timeout" in report


class SuccessfulProvider:
    def generate(self, prompt: str) -> str:
        return f"## Summary\n\nProvider handled: {prompt}"


def test_diagnose_with_ai_accepts_injected_provider(monkeypatch):
    monkeypatch.setenv("OPENAI_API_KEY", "fake-key")

    report = diagnose_with_ai("failure prompt", provider=SuccessfulProvider())

    assert "Provider handled: failure prompt" in report


def test_diagnose_with_ai_rejects_unknown_provider_before_creating_provider(monkeypatch):
    clear_provider_env(monkeypatch)
    monkeypatch.setenv("AI_PROVIDER", "deepssek")
    monkeypatch.setenv("AI_API_KEY", "fake-key")

    def fail_if_created(*args, **kwargs):
        raise AssertionError("provider should not be created")

    monkeypatch.setattr(
        "qa_copilot.diagnosis.create_diagnosis_provider",
        fail_if_created,
    )

    report = diagnose_with_ai("failure prompt")

    assert "AI 诊断已跳过" in report
    assert "unsupported_provider" in report
    assert "provider should not be created" not in report


def test_diagnose_with_ai_rejects_invalid_api_style_before_creating_provider(monkeypatch):
    clear_provider_env(monkeypatch)
    monkeypatch.setenv("AI_PROVIDER", "deepseek")
    monkeypatch.setenv("DEEPSEEK_API_KEY", "fake-key")
    monkeypatch.setenv("AI_API_STYLE", "chta")

    def fail_if_created(*args, **kwargs):
        raise AssertionError("provider should not be created")

    monkeypatch.setattr(
        "qa_copilot.diagnosis.create_diagnosis_provider",
        fail_if_created,
    )

    report = diagnose_with_ai("failure prompt")

    assert "AI 诊断已跳过" in report
    assert "unsupported_api_style" in report
    assert "provider should not be created" not in report


def test_diagnose_with_ai_rejects_missing_base_url_before_creating_provider(monkeypatch):
    clear_provider_env(monkeypatch)
    monkeypatch.setenv("AI_PROVIDER", "openai-compatible")
    monkeypatch.setenv("AI_API_KEY", "fake-gateway-key")

    def fail_if_created(*args, **kwargs):
        raise AssertionError("provider should not be created")

    monkeypatch.setattr(
        "qa_copilot.diagnosis.create_diagnosis_provider",
        fail_if_created,
    )

    report = diagnose_with_ai("failure prompt")

    assert "AI 诊断已跳过" in report
    assert "base_url" in report
    assert "provider should not be created" not in report


def test_fallback_report_uses_failure_context_when_api_key_is_missing(monkeypatch):
    clear_provider_env(monkeypatch)
    artifact = FailureArtifact(
        nodeid="tests/e2e/test_checkout_flow.py::test_checkout_button_enables_payment",
        failed_at=datetime(2026, 7, 6, tzinfo=UTC).isoformat(),
        phase="call",
        duration_seconds=1.2,
        longrepr=(
            "AssertionError: expect(locator).to_be_visible() failed\n"
            "Locator: get_by_role('button', name='Pay now')\n"
            "Expected: visible\n"
            "Received: hidden"
        ),
        keywords=["playwright", "e2e", "visibility"],
    )

    report = diagnose_with_ai(build_diagnosis_prompt([artifact]))

    assert "AI 诊断已跳过" in report
    assert "未配置 AI 服务密钥" in report
    assert "UI/E2E behavior" in report
    assert "test_checkout_button_enables_payment" in report
    assert "expect(locator).to_be_visible() failed" in report
    assert "检查页面状态、截图或 trace" in report
