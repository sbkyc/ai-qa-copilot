from __future__ import annotations

from pathlib import Path

README = Path("README.md")
WALKTHROUGH = Path("docs/portfolio-walkthrough.md")
SCREENSHOTS_DOC = Path("docs/screenshots.md")
SCREENSHOT_SCRIPT = Path("scripts/capture-portfolio-screenshots.ps1")
RESUME_ZH = Path("docs/resume-zh.md")
INTERVIEW_QA_ZH = Path("docs/interview-qa.md")
INTERVIEW_WALKTHROUGH_ZH = Path("docs/interview-walkthrough-zh.md")
VISUAL_ASSETS = (
    Path("docs/assets/provider-status.png"),
    Path("docs/assets/failure-mode-matrix.png"),
)
CHINESE_INTERVIEW_DOCS = (
    README,
    RESUME_ZH,
    INTERVIEW_QA_ZH,
    INTERVIEW_WALKTHROUGH_ZH,
)
MOJIBAKE_PATTERNS = (
    "锟",
    "娑",
    "鐠",
    "閸",
    "閻",
    "閿",
    "閵",
    "缁",
    "鈧",
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


def test_portfolio_screenshot_capture_process_is_documented():
    walkthrough = WALKTHROUGH.read_text(encoding="utf-8")
    screenshots_doc = SCREENSHOTS_DOC.read_text(encoding="utf-8")
    script = SCREENSHOT_SCRIPT.read_text(encoding="utf-8")

    assert "[Screenshot Capture](screenshots.md)" in walkthrough
    assert "scripts\\capture-portfolio-screenshots.ps1" in screenshots_doc
    assert "docs/assets/provider-status.png" in screenshots_doc
    assert "docs/assets/failure-mode-matrix.png" in screenshots_doc
    assert "demo-provider-key-for-screenshot-only" in script
    assert "fake key text leaked into Provider Status screenshot" in script
    assert "tenant.internal.example" in script
    assert "$LASTEXITCODE" in script
    assert "Screenshot capture failed" in script


def test_chinese_interview_docs_do_not_contain_common_mojibake():
    for path in CHINESE_INTERVIEW_DOCS:
        text = path.read_text(encoding="utf-8")
        for pattern in MOJIBAKE_PATTERNS:
            assert pattern not in text, f"{path} contains mojibake-like text: {pattern}"


def test_readme_links_chinese_interview_materials():
    readme = README.read_text(encoding="utf-8")

    assert "中文面试材料 / Chinese Interview Prep" in readme
    assert "docs/resume-zh.md" in readme
    assert "docs/interview-qa.md" in readme
    assert "docs/interview-walkthrough-zh.md" in readme


def test_chinese_interview_docs_cover_current_project_story():
    resume = RESUME_ZH.read_text(encoding="utf-8")
    qa = INTERVIEW_QA_ZH.read_text(encoding="utf-8")
    walkthrough = INTERVIEW_WALKTHROUGH_ZH.read_text(encoding="utf-8")

    combined = "\n".join((resume, qa, walkthrough))

    for phrase in (
        "FastAPI",
        "pytest",
        "Playwright",
        "GitHub Actions",
        "Provider Status",
        "Failure Mode Matrix",
        "DeepSeek",
        "OpenAI-compatible",
        "API key",
        "脱敏",
        "不暴露",
    ):
        assert phrase in combined


def test_chinese_walkthrough_is_a_three_minute_interview_script():
    walkthrough = INTERVIEW_WALKTHROUGH_ZH.read_text(encoding="utf-8")

    for heading in (
        "## 30 秒项目介绍",
        "## 技术栈",
        "## 自动化测试价值",
        "## AI diagnosis 价值",
        "## Provider 安全设计",
        "## Failure Mode Matrix 怎么讲",
        "## 我在项目里做了什么",
        "## 后续扩展方向",
    ):
        assert heading in walkthrough
