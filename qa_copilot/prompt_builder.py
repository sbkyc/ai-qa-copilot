from __future__ import annotations

from qa_copilot.artifacts import FailureArtifact


def build_diagnosis_prompt(artifacts: list[FailureArtifact]) -> str:
    sections = [
        "You are an AI QA copilot helping diagnose automated test failures.",
        "Return a structured report with these headings:",
        "- Summary",
        "- Suspected root cause",
        "- Reproduction steps",
        "- Evidence",
        "- Suggested fix",
        "- Risk level",
        "- Classification: product bug, test script bug, or environment issue",
        "",
        "Failure context:",
    ]
    for artifact in artifacts:
        sections.extend(
            [
                f"Test: {artifact.nodeid}",
                f"Failed at: {artifact.failed_at}",
                f"Phase: {artifact.phase}",
                f"Duration seconds: {artifact.duration_seconds}",
                f"Keywords: {', '.join(artifact.keywords)}",
                "Trace:",
                artifact.longrepr,
                "",
            ]
        )
    return "\n".join(sections)
