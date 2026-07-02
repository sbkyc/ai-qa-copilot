from __future__ import annotations

from pathlib import Path

README = Path("README.md")
WALKTHROUGH = Path("docs/portfolio-walkthrough.md")


def test_readme_links_portfolio_walkthrough():
    readme = README.read_text(encoding="utf-8")

    assert "[Portfolio Walkthrough](docs/portfolio-walkthrough.md)" in readme
    assert "3-minute interview path" in readme


def test_portfolio_walkthrough_covers_demo_story():
    walkthrough = WALKTHROUGH.read_text(encoding="utf-8")

    assert "Provider Status" in walkthrough
    assert "python -m qa_copilot.cli --input reports/examples" in walkthrough
    assert "Failure Mode Matrix" in walkthrough
    assert "reports/examples/sample-ai-diagnosis.md" in walkthrough
    assert "DeepSeek" in walkthrough
