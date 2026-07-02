$ErrorActionPreference = "Stop"

Write-Host "==> Running Ruff"
ruff check .

Write-Host "==> Running pytest and Playwright"
pytest -q --browser chromium --tracing retain-on-failure --screenshot only-on-failure

Write-Host "==> Generating demo AI diagnosis report"
python -m qa_copilot.cli --input reports/examples --output reports/latest/demo-ai-diagnosis.md

if (-not (Test-Path "reports/latest/demo-ai-diagnosis.md")) {
  throw "Demo AI diagnosis report was not generated."
}

Write-Host "==> Verification complete"
