from __future__ import annotations

from pathlib import Path

README = Path("README.md")
WALKTHROUGH = Path("docs/portfolio-walkthrough.md")
VISUAL_ASSETS = (
    Path("docs/assets/provider-status.png"),
    Path("docs/assets/failure-mode-matrix.png"),
)


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


def test_portfolio_walkthrough_mentions_demo_security_boundaries():
    walkthrough = WALKTHROUGH.read_text(encoding="utf-8")

    assert "local demo credentials only" in walkthrough
    assert "avoid sending proprietary logs to third-party providers" in walkthrough


def test_portfolio_visual_assets_are_documented():
    readme = README.read_text(encoding="utf-8")
    walkthrough = WALKTHROUGH.read_text(encoding="utf-8")

    assert "docs/assets/provider-status.png" in readme
    assert "docs/assets/failure-mode-matrix.png" in readme
    assert "assets/provider-status.png" in walkthrough
    assert "assets/failure-mode-matrix.png" in walkthrough
    for asset in VISUAL_ASSETS:
        assert asset.exists()
        assert asset.stat().st_size > 5_000
