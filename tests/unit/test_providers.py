from __future__ import annotations

from qa_copilot.providers import DiagnosisProviderConfig, OpenAIResponsesProvider


class FakeResponses:
    def __init__(self):
        self.calls: list[dict[str, str]] = []

    def create(self, model: str, input: str):  # noqa: A002
        self.calls.append({"model": model, "input": input})
        return type("Response", (), {"output_text": "## Summary\n\nAPI diagnosis"})()


class FakeOpenAIClient:
    def __init__(self):
        self.responses = FakeResponses()


def test_config_from_env_reads_openai_settings(monkeypatch):
    monkeypatch.setenv("OPENAI_API_KEY", "test-key")
    monkeypatch.setenv("OPENAI_MODEL", "gpt-test")
    monkeypatch.setenv("OPENAI_BASE_URL", "https://gateway.example.test/v1")

    config = DiagnosisProviderConfig.from_env()

    assert config.api_key == "test-key"
    assert config.model == "gpt-test"
    assert config.base_url == "https://gateway.example.test/v1"


def test_openai_responses_provider_sends_prompt_to_responses_api():
    client = FakeOpenAIClient()
    provider = OpenAIResponsesProvider(
        config=DiagnosisProviderConfig(api_key="test-key", model="gpt-test"),
        client=client,
    )

    result = provider.generate("failure prompt")

    assert result == "## Summary\n\nAPI diagnosis"
    assert client.responses.calls == [{"model": "gpt-test", "input": "failure prompt"}]
