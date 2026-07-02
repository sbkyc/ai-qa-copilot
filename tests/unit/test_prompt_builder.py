from __future__ import annotations

from qa_copilot.artifacts import FailureArtifact
from qa_copilot.prompt_builder import build_diagnosis_prompt


def test_build_diagnosis_prompt_contains_failure_context():
    artifact = FailureArtifact(
        nodeid="tests/api/test_orders_api.py::test_create_order_rejects_insufficient_stock",
        failed_at="2026-07-02T10:00:00+00:00",
        phase="call",
        duration_seconds=0.13,
        longrepr="AssertionError: expected 409 but got 500",
        keywords=["api"],
    )

    prompt = build_diagnosis_prompt([artifact])

    assert "expected 409 but got 500" in prompt
    assert "Suspected root cause" in prompt
    assert "test script bug" in prompt
