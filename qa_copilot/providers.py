from __future__ import annotations

import os
from dataclasses import dataclass
from typing import Any, Protocol

from openai import OpenAI


class DiagnosisProvider(Protocol):
    def generate(self, prompt: str) -> str:
        """Generate a diagnosis report from a failure prompt."""


@dataclass(frozen=True)
class DiagnosisProviderConfig:
    api_key: str
    model: str = "gpt-4.1-mini"
    base_url: str | None = None

    @classmethod
    def from_env(cls) -> DiagnosisProviderConfig:
        base_url = os.getenv("OPENAI_BASE_URL", "").strip() or None
        return cls(
            api_key=os.getenv("OPENAI_API_KEY", "").strip(),
            model=os.getenv("OPENAI_MODEL", "gpt-4.1-mini").strip() or "gpt-4.1-mini",
            base_url=base_url,
        )


class OpenAIResponsesProvider:
    def __init__(
        self,
        config: DiagnosisProviderConfig,
        client: Any | None = None,
    ) -> None:
        self.config = config
        self.client = client

    def _client(self) -> Any:
        if self.client is not None:
            return self.client
        if self.config.base_url:
            return OpenAI(api_key=self.config.api_key, base_url=self.config.base_url)
        return OpenAI(api_key=self.config.api_key)

    def generate(self, prompt: str) -> str:
        response = self._client().responses.create(
            model=self.config.model,
            input=prompt,
        )
        return str(response.output_text)
