from __future__ import annotations

import argparse
import json
from pathlib import Path

from qa_copilot.artifacts import load_failure_artifacts
from qa_copilot.diagnosis import diagnose_with_ai
from qa_copilot.prompt_builder import build_diagnosis_prompt
from qa_copilot.providers import supported_provider_specs
from qa_copilot.report_writer import write_markdown_report


def generate_report(input_path: str | Path, output_path: str | Path) -> None:
    artifacts = load_failure_artifacts(input_path)
    if not artifacts:
        write_markdown_report(
            Path(output_path),
            "AI Diagnosis Report",
            "## Summary\n\nNo failure artifacts were found.\n",
        )
        return

    prompt = build_diagnosis_prompt(artifacts)
    body = diagnose_with_ai(prompt)
    write_markdown_report(Path(output_path), "AI Diagnosis Report", body)


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate AI QA diagnosis reports.")
    parser.add_argument("--list-providers", action="store_true")
    parser.add_argument("--input", default="reports/latest/failures")
    parser.add_argument("--output", default="reports/latest/ai-diagnosis.md")
    args = parser.parse_args()

    if args.list_providers:
        print(json.dumps(supported_provider_specs(), indent=2, ensure_ascii=False))
        return

    generate_report(args.input, args.output)


if __name__ == "__main__":
    main()
