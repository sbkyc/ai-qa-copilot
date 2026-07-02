# Demo Failure Flow

This project includes curated failure artifacts so reviewers can see the AI diagnosis workflow without breaking the test suite.

## Generate A Demo Diagnosis Report

Run:

```powershell
python -m qa_copilot.cli --input reports/examples --output reports/latest/demo-ai-diagnosis.md
```

Then open:

```powershell
Get-Content reports/latest/demo-ai-diagnosis.md
```

If `OPENAI_API_KEY` is not configured, the command writes a fallback report. This is intentional: the automation workflow should still complete even when AI access is unavailable.

If `OPENAI_API_KEY` is configured, the same command sends the sample failure context to the configured OpenAI model and writes a generated diagnosis report.

## What The Demo Shows

The sample artifacts cover several realistic QA failure modes:

- an insufficient-stock API test that expected HTTP `409` but received HTTP `500`
- a Playwright visibility failure with screenshot and trace references
- an API contract mismatch with request and response evidence
- a flaky search test with repeated pass/fail history
- a database fixture/setup failure

The generated report is expected to explain the likely root cause, evidence, reproduction steps, suggested fix, risk level, and whether each failure looks like a product bug, test script bug, or environment issue.

See [diagnosis-examples.md](diagnosis-examples.md) for the full example catalog.

## Real CI Flow

In real test runs, `tests/conftest.py` writes failed test artifacts to:

```text
reports/latest/failures/
```

GitHub Actions then runs:

```powershell
python -m qa_copilot.cli --input reports/latest/failures --output reports/latest/ai-diagnosis.md
```

The resulting report is uploaded with the rest of the test artifacts.
