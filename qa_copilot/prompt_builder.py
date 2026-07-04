from __future__ import annotations

from collections import defaultdict

from qa_copilot.artifacts import FailureArtifact

FAILURE_MODE_ORDER = (
    "Product/API behavior",
    "API contract",
    "UI/E2E behavior",
    "Flaky/timing",
    "Environment/setup",
    "Unclassified",
)


def _failure_mode(artifact: FailureArtifact) -> str:
    keywords = {keyword.lower() for keyword in artifact.keywords}
    phase = artifact.phase.lower()

    if phase == "setup" or keywords.intersection({"fixture", "setup"}):
        return "Environment/setup"
    if "flaky" in keywords:
        return "Flaky/timing"
    if keywords.intersection({"api-assertion", "contract"}):
        return "API contract"
    if keywords.intersection({"playwright", "e2e", "visibility"}):
        return "UI/E2E behavior"
    if "api" in keywords:
        return "Product/API behavior"
    return "Unclassified"


def _group_by_failure_mode(
    artifacts: list[FailureArtifact],
) -> dict[str, list[FailureArtifact]]:
    grouped: dict[str, list[FailureArtifact]] = defaultdict(list)
    for artifact in artifacts:
        grouped[_failure_mode(artifact)].append(artifact)
    return {mode: grouped[mode] for mode in FAILURE_MODE_ORDER if grouped[mode]}


def build_diagnosis_prompt(artifacts: list[FailureArtifact]) -> str:
    sections = [
        "你是一个 AI QA Copilot，负责辅助诊断自动化测试失败。",
        "请用简体中文输出结构化 Markdown 报告。",
        "技术名词、测试路径、HTTP 状态码、异常名和 failure mode 名称可以保留英文。",
        "报告必须包含这些二级标题：",
        "- 摘要",
        "- Failure Mode Matrix（失败模式矩阵）",
        "- 候选根因 / 诊断假设",
        "- 复现步骤",
        "- 证据",
        "- 修复建议",
        "- 风险等级",
        "- 分类：产品缺陷、测试脚本问题、偶发/时序问题、环境问题",
        "",
        "Failure Mode Matrix 表格必须包含这些列：失败模式、影响测试、证据、可能分类、下一步。",
        "请避免把候选根因写成已确认根因；用“可能”“候选”“诊断假设”这类措辞。",
        "",
        "Failure mode groups:",
    ]
    for mode, grouped_artifacts in _group_by_failure_mode(artifacts).items():
        sections.extend(["", f"### {mode}"])
        for artifact in grouped_artifacts:
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
    if not artifacts:
        sections.extend(
            [
                "",
                "没有提供失败证据。",
            ]
        )
    return "\n".join(sections)
