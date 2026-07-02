from __future__ import annotations

import os

from openai import OpenAI

FALLBACK_REPORT = """## Summary

AI diagnosis was skipped because OPENAI_API_KEY is not configured.

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
        return FALLBACK_REPORT

    model = os.getenv("OPENAI_MODEL", "gpt-4.1-mini")
    client = OpenAI(api_key=api_key)
    response = client.responses.create(
        model=model,
        input=prompt,
    )
    return response.output_text
