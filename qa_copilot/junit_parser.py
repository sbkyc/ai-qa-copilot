from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path
from xml.etree import ElementTree

from qa_copilot.artifacts import FailureArtifact


def _local_name(tag: str) -> str:
    return tag.rsplit("}", 1)[-1] if "}" in tag else tag


def _normalize_timestamp(raw: str | None) -> str:
    if not raw:
        return datetime.now(UTC).isoformat()
    candidate = raw.strip()
    if candidate.endswith("Z"):
        candidate = f"{candidate[:-1]}+00:00"
    if "+" not in candidate and candidate.count("-") > 1:
        candidate = f"{candidate}+00:00"
    try:
        parsed = datetime.fromisoformat(candidate)
    except ValueError:
        return datetime.now(UTC).isoformat()
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=UTC)
    return parsed.isoformat()


def _nodeid(classname: str, name: str) -> str:
    if not classname:
        return name or "junit::unknown"
    module_path = classname.replace(".", "/")
    if not module_path.endswith(".py"):
        module_path = f"{module_path}.py"
    return f"{module_path}::{name or 'unknown'}"


def _failure_child(testcase: ElementTree.Element) -> ElementTree.Element | None:
    for child in testcase:
        if _local_name(child.tag) in {"failure", "error"}:
            return child
    return None


def _longrepr(failure: ElementTree.Element) -> str:
    message = str(failure.attrib.get("message", "")).strip()
    text = (failure.text or "").strip()
    if message and text and message not in text:
        return f"{message}\n{text}"
    return text or message or "JUnit failure did not include details."


def _phase(failure: ElementTree.Element, longrepr: str) -> str:
    text = f"{_local_name(failure.tag)} {longrepr}".lower()
    if any(marker in text for marker in ("setup", "fixture", "no such table")):
        return "setup"
    if "teardown" in text:
        return "teardown"
    return "call"


def _keywords(nodeid: str, longrepr: str, phase: str) -> list[str]:
    text = f"{nodeid} {longrepr} {phase}".lower()
    keywords = ["junit", "pytest"]
    if any(marker in text for marker in ("setup", "fixture", "no such table")):
        keywords.extend(["setup", "fixture"])
    if any(marker in text for marker in ("sqlite", "database", "db_")):
        keywords.append("database")
    if any(marker in text for marker in ("flaky", "timing", "timeout", "race")):
        keywords.extend(["flaky", "timing"])
    if any(marker in text for marker in ("playwright", "locator", "to_be_visible", "e2e")):
        keywords.extend(["playwright", "e2e", "visibility"])
    if any(marker in text for marker in ("contract", "schema", "validation", "422")):
        keywords.extend(["api", "contract"])
    elif any(marker in text for marker in ("api", "http", "status code", "/api/")):
        keywords.append("api")
    return list(dict.fromkeys(keywords))


def load_junit_failures(path: str | Path) -> list[FailureArtifact]:
    junit_path = Path(path)
    if not junit_path.is_file():
        return []

    try:
        root = ElementTree.fromstring(junit_path.read_text(encoding="utf-8"))
    except (ElementTree.ParseError, OSError, UnicodeDecodeError):
        return []

    suites = [root] if _local_name(root.tag) == "testsuite" else [
        element for element in root.iter() if _local_name(element.tag) == "testsuite"
    ]
    artifacts: list[FailureArtifact] = []
    for suite in suites:
        failed_at = _normalize_timestamp(suite.attrib.get("timestamp"))
        for testcase in suite:
            if _local_name(testcase.tag) != "testcase":
                continue
            failure = _failure_child(testcase)
            if failure is None:
                continue
            longrepr = _longrepr(failure)
            phase = _phase(failure, longrepr)
            nodeid = _nodeid(
                str(testcase.attrib.get("classname", "")),
                str(testcase.attrib.get("name", "")),
            )
            artifacts.append(
                FailureArtifact(
                    nodeid=nodeid,
                    failed_at=failed_at,
                    phase=phase,
                    duration_seconds=float(testcase.attrib.get("time", 0) or 0),
                    longrepr=longrepr,
                    keywords=_keywords(nodeid, longrepr, phase),
                )
            )
    return artifacts
