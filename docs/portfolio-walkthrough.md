# Portfolio Walkthrough

This walkthrough is the shortest path for showing AI QA Copilot in an interview or portfolio review. It connects the visible demo app, provider safety checks, test automation artifacts, and AI diagnosis output into one story.

## 3-Minute Interview Path

1. Open the FastAPI demo shop and log in with the demo account.
2. Point out the Provider Status card: it shows readiness without exposing API keys, model names, key source environment variables, or custom base URLs.
3. Run the bundled failure examples through the CLI.
4. Open the generated report or the curated sample report.
5. Explain the Failure Mode Matrix: it separates product/API bugs, contract drift, UI/E2E failures, flaky timing, and environment/setup failures.

## Run The Demo App

```powershell
uvicorn app.main:app --reload
```

Open:

```text
http://127.0.0.1:8000
```

Demo account:

```text
username: alice
password: password123
```

These are local demo credentials only; do not reuse them in production.

The products page includes Provider Status. The same provider health data is also available from the redacted API endpoint:

```powershell
Invoke-RestMethod http://127.0.0.1:8000/api/provider-health
```

## Generate A Diagnosis Demo

The repo includes safe example artifacts in `reports/examples/`, so the demo does not require intentionally breaking the test suite.

```powershell
python -m qa_copilot.cli --input reports/examples --output reports/latest/demo-ai-diagnosis.md
```

Without a configured provider key, the command writes a fallback report. With a configured provider, it sends grouped failure context to the provider.

Use a temporary demo key, and avoid sending proprietary logs to third-party providers.

DeepSeek example:

```powershell
$env:AI_PROVIDER="deepseek"
$env:DEEPSEEK_API_KEY="your-deepseek-key"
python -m qa_copilot.cli --input reports/examples --output reports/latest/demo-ai-diagnosis.md
```

Open the generated report:

```powershell
Get-Content reports/latest/demo-ai-diagnosis.md
```

For a stable portfolio example, use:

```text
reports/examples/sample-ai-diagnosis.md
```

## What To Show

Use the Failure Mode Matrix as the centerpiece:

| Failure Mode | What It Demonstrates |
| --- | --- |
| Product/API behavior | A business error returns the wrong HTTP status. |
| API contract | Request/response shape drifts from the expected contract. |
| UI/E2E behavior | A browser-visible control is hidden or not ready. |
| Flaky/timing | Repeated CI history shows unstable timing behavior. |
| Environment/setup | The test fails before assertions because setup is broken. |

The interview message is simple: this project is not just a collection of tests. It captures failure evidence, protects provider configuration, and turns automated-test output into a structured diagnosis workflow.
