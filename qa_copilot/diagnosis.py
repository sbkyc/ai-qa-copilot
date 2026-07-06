from __future__ import annotations

from qa_copilot.provider_health import provider_config_issues
from qa_copilot.providers import (
    DiagnosisProvider,
    DiagnosisProviderConfig,
    create_diagnosis_provider,
)


def _fallback_context_from_prompt(prompt: str | None) -> dict[str, str]:
    if not prompt:
        return {
            "mode": "Environment/setup",
            "test": "当前诊断流程",
            "evidence": "未提供失败证据",
            "classification": "环境问题",
            "next_action": "检查 AI 服务配置后重新生成报告。",
        }

    mode = "Environment/setup"
    test = "当前诊断流程"
    evidence = "未提取到关键失败证据"
    lines = prompt.splitlines()
    for index, line in enumerate(lines):
        stripped = line.strip()
        if stripped.startswith("### "):
            mode = stripped.removeprefix("### ").strip()
        elif stripped.startswith("Test: "):
            test = stripped.removeprefix("Test: ").strip()
        elif stripped == "Trace:":
            trace_lines: list[str] = []
            for trace_line in lines[index + 1 :]:
                trace = trace_line.strip()
                if not trace and trace_lines:
                    break
                if trace:
                    trace_lines.append(trace)
                if len(trace_lines) >= 3:
                    break
            if trace_lines:
                evidence = " / ".join(trace_lines)[:240]
            break

    mode_rules = {
        "Product/API behavior": (
            "产品缺陷",
            "检查业务异常映射、HTTP 状态码和服务端处理逻辑。",
        ),
        "API contract": (
            "契约漂移",
            "对齐请求参数、响应 schema 和测试契约。",
        ),
        "UI/E2E behavior": (
            "UI 状态问题",
            "检查页面状态、截图或 trace，并确认前置操作是否完成。",
        ),
        "Flaky/timing": (
            "偶发/时序问题",
            "检查等待条件、异步请求和断言时机。",
        ),
        "Environment/setup": (
            "环境问题",
            "检查 fixture、数据库初始化和测试隔离。",
        ),
    }
    classification, next_action = mode_rules.get(
        mode,
        ("待分类问题", "补充 keywords、phase 和失败上下文后重新诊断。"),
    )
    return {
        "mode": mode,
        "test": test,
        "evidence": evidence,
        "classification": classification,
        "next_action": next_action,
    }


def fallback_report(reason: str, prompt: str | None = None) -> str:
    context = _fallback_context_from_prompt(prompt)
    matrix_row = (
        f'| {context["mode"]} | {context["test"]} | {context["evidence"]} | '
        f'{context["classification"]} | {context["next_action"]} |'
    )
    return f"""## 摘要

AI 诊断已跳过，原因：{reason}。

## Failure Mode Matrix（失败模式矩阵）

| 失败模式 | 影响测试 | 证据 | 可能分类 | 下一步 |
| --- | --- | --- | --- | --- |
{matrix_row}

## 候选根因 / 诊断假设

AI 服务当前不可用，需要人工查看 pytest 失败证据。当前证据更接近：{context["classification"]}。

## 复现步骤

运行失败证据中记录的 pytest 节点：`{context["test"]}`。

## 证据

{context["evidence"]}

## 修复建议

{context["next_action"]}

## 风险等级

未知。

## 分类

{context["classification"]}
"""


def diagnose_with_ai(
    prompt: str,
    provider: DiagnosisProvider | None = None,
    config: DiagnosisProviderConfig | None = None,
) -> str:
    resolved_config = config or DiagnosisProviderConfig.from_env()
    missing_config, config_errors = provider_config_issues(resolved_config)
    if config_errors:
        return fallback_report(f"AI 服务配置错误：{', '.join(config_errors)}", prompt)
    if "api_key" in missing_config:
        return fallback_report("未配置 AI 服务密钥", prompt)
    if missing_config:
        return fallback_report(f"AI 服务配置缺失：{', '.join(missing_config)}", prompt)

    try:
        resolved_provider = provider or create_diagnosis_provider(resolved_config)
        return resolved_provider.generate(prompt)
    except Exception as exc:
        return fallback_report(str(exc), prompt)
