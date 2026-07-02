from __future__ import annotations

from qa_copilot.diagnosis import diagnose_with_ai


class FailingResponses:
    def create(self, model: str, input: str):  # noqa: A002
        raise TimeoutError("network timeout")


class FailingOpenAI:
    def __init__(self, api_key: str):
        self.responses = FailingResponses()


def test_diagnose_with_ai_returns_fallback_when_openai_call_fails(monkeypatch):
    monkeypatch.setenv("OPENAI_API_KEY", "fake-key")
    monkeypatch.setattr("qa_copilot.diagnosis.OpenAI", FailingOpenAI)

    report = diagnose_with_ai("failure prompt")

    assert "AI diagnosis was skipped" in report
    assert "network timeout" in report
