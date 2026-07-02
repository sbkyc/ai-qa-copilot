from __future__ import annotations

import json

from qa_copilot.cli import generate_report
from qa_copilot.cli import main as cli_main


def test_generate_report_writes_no_artifacts_message(tmp_path):
    output = tmp_path / "diagnosis.md"

    generate_report(tmp_path / "missing", output)

    assert "No failure artifacts were found." in output.read_text(encoding="utf-8")


def test_generate_report_writes_diagnosis_for_failure_artifact(tmp_path, monkeypatch):
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    failures = tmp_path / "failures"
    failures.mkdir()
    (failures / "failure.json").write_text(
        json.dumps(
            {
                "nodeid": "tests/api/test_orders_api.py::test_create_order",
                "failed_at": "2026-07-02T10:00:00+00:00",
                "phase": "call",
                "duration_seconds": 0.12,
                "longrepr": "AssertionError: expected 409 but got 500",
                "keywords": ["api", "orders"],
            }
        ),
        encoding="utf-8",
    )
    output = tmp_path / "diagnosis.md"

    generate_report(failures, output)

    report = output.read_text(encoding="utf-8")
    assert "# AI Diagnosis Report" in report
    assert "API key is not configured" in report


def test_cli_lists_supported_providers(monkeypatch, capsys):
    monkeypatch.setattr("sys.argv", ["qa-copilot", "--list-providers"])

    cli_main()

    output = json.loads(capsys.readouterr().out)
    assert output["deepseek"]["api_style"] == "chat"
    assert output["openai"]["api_style"] == "responses"
