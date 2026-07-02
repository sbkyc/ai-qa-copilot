# AI API Adapter Guide

AI QA Copilot keeps external AI calls behind a small provider layer so the test framework does not depend directly on one API call site.

## Provider Layer

The provider layer lives in:

```text
qa_copilot/providers.py
```

It currently includes:

- `DiagnosisProviderConfig`: reads API settings from environment variables.
- `DiagnosisProvider`: protocol for any diagnosis provider.
- `OpenAIResponsesProvider`: adapter for OpenAI's Responses API.

The diagnosis workflow uses the provider through:

```text
qa_copilot/diagnosis.py
```

This keeps failure handling and fallback behavior separate from API transport details.

## Environment Variables

```dotenv
OPENAI_API_KEY=
OPENAI_MODEL=gpt-4.1-mini
OPENAI_BASE_URL=
```

`OPENAI_API_KEY` is optional for local demo runs. If it is empty, the CLI writes a fallback report instead of failing.

`OPENAI_MODEL` controls the model used by the Responses API adapter.

`OPENAI_BASE_URL` is optional. Use it only when routing through an OpenAI-compatible gateway or proxy.

## OpenAI Example

```powershell
$env:OPENAI_API_KEY="your-api-key"
$env:OPENAI_MODEL="gpt-4.1-mini"
python -m qa_copilot.cli --input reports/examples --output reports/latest/demo-ai-diagnosis.md
```

## OpenAI-Compatible Gateway Example

```powershell
$env:OPENAI_API_KEY="gateway-key"
$env:OPENAI_MODEL="your-routed-model"
$env:OPENAI_BASE_URL="https://gateway.example.com/v1"
python -m qa_copilot.cli --input reports/examples --output reports/latest/demo-ai-diagnosis.md
```

## Fallback Behavior

The AI diagnosis feature must not break CI. The CLI writes a fallback Markdown report when:

- `OPENAI_API_KEY` is missing
- the API request times out
- the provider returns an error
- the configured gateway is unavailable

The normal pytest HTML report and JSON failure artifacts remain available even when AI diagnosis is skipped.

## Diagnosis HTTP Endpoint

The FastAPI demo app exposes `POST /api/diagnosis` for API-based integration demos.

Request body:

```json
{
  "nodeid": "tests/api/test_orders_api.py::test_create_order",
  "failed_at": "2026-07-02T10:00:00+00:00",
  "phase": "call",
  "duration_seconds": 0.12,
  "longrepr": "AssertionError: expected 409 but got 500",
  "keywords": ["api", "orders"]
}
```

Response body:

```json
{
  "artifact_count": 1,
  "report_markdown": "## Summary\n\n..."
}
```

This endpoint uses the same provider layer as the CLI, so it supports the same `OPENAI_API_KEY`, `OPENAI_MODEL`, and `OPENAI_BASE_URL` environment variables.

## Adding Another Provider

To add another provider:

1. Create a class with `generate(prompt: str) -> str`.
2. Convert the provider's response into Markdown.
3. Inject that provider into `diagnose_with_ai()`.
4. Add unit tests that use a fake client and do not call the network.
