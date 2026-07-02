from __future__ import annotations

from qa_copilot.diagnosis import diagnose_with_ai


class FailingProvider:
    def generate(self, prompt: str) -> str:
        raise TimeoutError("network timeout")


def test_diagnose_with_ai_returns_fallback_when_openai_call_fails(monkeypatch):
    monkeypatch.setenv("OPENAI_API_KEY", "fake-key")

    report = diagnose_with_ai("failure prompt", provider=FailingProvider())

    assert "AI diagnosis was skipped" in report
    assert "network timeout" in report


class SuccessfulProvider:
    def generate(self, prompt: str) -> str:
        return f"## Summary\n\nProvider handled: {prompt}"


def test_diagnose_with_ai_accepts_injected_provider(monkeypatch):
    monkeypatch.setenv("OPENAI_API_KEY", "fake-key")

    report = diagnose_with_ai("failure prompt", provider=SuccessfulProvider())

    assert "Provider handled: failure prompt" in report
