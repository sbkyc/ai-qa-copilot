from __future__ import annotations

from qa_copilot.junit_parser import load_junit_failures


def test_load_junit_failures_extracts_failure_and_error_cases(tmp_path):
    junit_xml = tmp_path / "junit.xml"
    junit_xml.write_text(
        """<?xml version="1.0" encoding="utf-8"?>
<testsuites>
  <testsuite name="pytest" timestamp="2026-07-06T12:00:00" tests="2" failures="1" errors="1">
    <testcase classname="tests.api.test_orders_api" name="test_create_order_contract" time="0.12">
      <failure message="expected 201 got 422">AssertionError: expected status code 201 but got 422
response body: {"detail": [{"loc": ["body", "quantity"], "msg": "Field required"}]}</failure>
    </testcase>
    <testcase classname="tests.conftest" name="db_seed_fixture" time="0.03">
      <error message="sqlite3.OperationalError: no such table: products">setup failed in fixture
sqlite3.OperationalError: no such table: products</error>
    </testcase>
  </testsuite>
</testsuites>
""",
        encoding="utf-8",
    )

    artifacts = load_junit_failures(junit_xml)

    assert len(artifacts) == 2
    assert artifacts[0].nodeid == (
        "tests/api/test_orders_api.py::test_create_order_contract"
    )
    assert artifacts[0].failed_at == "2026-07-06T12:00:00+00:00"
    assert artifacts[0].phase == "call"
    assert artifacts[0].duration_seconds == 0.12
    assert "expected status code 201 but got 422" in artifacts[0].longrepr
    assert {"junit", "pytest", "api", "contract"}.issubset(artifacts[0].keywords)

    assert artifacts[1].nodeid == "tests/conftest.py::db_seed_fixture"
    assert artifacts[1].phase == "setup"
    assert "no such table: products" in artifacts[1].longrepr
    assert {"fixture", "setup", "database"}.issubset(artifacts[1].keywords)
