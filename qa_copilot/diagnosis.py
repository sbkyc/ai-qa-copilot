from __future__ import annotations

import os

from openai import OpenAI


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


def diagnose_with_ai(prompt: str) -> str:
    api_key = os.getenv("OPENAI_API_KEY", "")
    if not api_key:
        return fallback_report("OPENAI_API_KEY is not configured")

    model = os.getenv("OPENAI_MODEL", "gpt-4.1-mini")
    try:
        client = OpenAI(api_key=api_key)
        response = client.responses.create(
            model=model,
            input=prompt,
        )
        return response.output_text
    except Exception as exc:
        return fallback_report(str(exc))
