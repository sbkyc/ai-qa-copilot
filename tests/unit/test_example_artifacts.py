from __future__ import annotations

from pathlib import Path

from qa_copilot.artifacts import load_failure_artifacts
from qa_copilot.prompt_builder import build_diagnosis_prompt

EXAMPLES = Path("reports/examples")


def test_example_artifacts_cover_core_qa_failure_modes():
    artifacts = load_failure_artifacts(EXAMPLES)
    keywords = {keyword for artifact in artifacts for keyword in artifact.keywords}

    assert "playwright" in keywords
    assert "api-assertion" in keywords
    assert "flaky" in keywords
    assert "fixture" in keywords
    assert "setup" in keywords


def test_example_artifacts_build_rich_diagnosis_prompt():
    artifacts = load_failure_artifacts(EXAMPLES)

    prompt = build_diagnosis_prompt(artifacts)

    assert "tests/e2e/test_checkout_flow.py::test_checkout_button_enables_payment" in prompt
    assert "expect(locator).to_be_visible()" in prompt
    assert "tests/api/test_orders_api.py::test_create_order_contract" in prompt
    assert "expected status code 201 but got 422" in prompt
    assert "tests/e2e/test_product_search.py::test_search_filters_results" in prompt
    assert "passed 7 times and failed 3 times" in prompt
    assert "tests/conftest.py::db_seed_fixture" in prompt
    assert "sqlite3.OperationalError" in prompt
