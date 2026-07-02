from __future__ import annotations

import argparse
from pathlib import Path

from qa_copilot.artifacts import load_failure_artifacts
from qa_copilot.diagnosis import diagnose_with_ai
from qa_copilot.prompt_builder import build_diagnosis_prompt
from qa_copilot.report_writer import write_markdown_report


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate AI QA diagnosis reports.")
    parser.add_argument("--input", default="reports/latest/failures")
    parser.add_argument("--output", default="reports/latest/ai-diagnosis.md")
    args = parser.parse_args()

    artifacts = load_failure_artifacts(args.input)
    if not artifacts:
        write_markdown_report(
            Path(args.output),
            "AI Diagnosis Report",
            "## Summary\n\nNo failure artifacts were found.\n",
        )
        return

    prompt = build_diagnosis_prompt(artifacts)
    body = diagnose_with_ai(prompt)
    write_markdown_report(Path(args.output), "AI Diagnosis Report", body)


if __name__ == "__main__":
    main()
