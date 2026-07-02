from __future__ import annotations

from qa_copilot.providers import DiagnosisProvider, DiagnosisProviderConfig, OpenAIResponsesProvider


def fallback_report(reason: str) -> str:
    return f"""## Summary

AI diagnosis was skipped because {reason}.

## Suspected root cause

Review the pytest failure artifact manually.

## Reproduction steps

Run the failing pytest node shown in the failure artifact.

## Evidence

The local pytest report and JSON failure artifact are available in reports/latest.

## Suggested fix

Inspect the failed assertion, request payload, response body, and browser trace.

## Risk level

Unknown

## Classification

environment issue
"""


def diagnose_with_ai(
    prompt: str,
    provider: DiagnosisProvider | None = None,
    config: DiagnosisProviderConfig | None = None,
) -> str:
    resolved_config = config or DiagnosisProviderConfig.from_env()
    if not resolved_config.api_key:
        return fallback_report("OPENAI_API_KEY is not configured")

    try:
        resolved_provider = provider or OpenAIResponsesProvider(resolved_config)
        return resolved_provider.generate(prompt)
    except Exception as exc:
        return fallback_report(str(exc))
