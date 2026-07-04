from __future__ import annotations

from qa_copilot.provider_health import provider_config_issues
from qa_copilot.providers import (
    DiagnosisProvider,
    DiagnosisProviderConfig,
    create_diagnosis_provider,
)


def fallback_report(reason: str) -> str:
    return f"""## 摘要

AI 诊断已跳过，原因：{reason}。

## Failure Mode Matrix（失败模式矩阵）

| 失败模式 | 影响测试 | 证据 | 可能分类 | 下一步 |
| --- | --- | --- | --- | --- |
| Environment/setup | 当前诊断流程 | {reason} | 环境问题 | 检查 AI 服务配置后重新生成报告。 |

## 候选根因 / 诊断假设

AI 服务当前不可用，需要人工查看 pytest 失败证据。

## 复现步骤

运行失败证据中记录的 pytest 节点。

## 证据

本地测试报告和结构化失败证据已生成。

## 修复建议

检查失败断言、请求参数、响应内容和浏览器调试附件。

## 风险等级

未知。

## 分类

环境问题
"""


def diagnose_with_ai(
    prompt: str,
    provider: DiagnosisProvider | None = None,
    config: DiagnosisProviderConfig | None = None,
) -> str:
    resolved_config = config or DiagnosisProviderConfig.from_env()
    missing_config, config_errors = provider_config_issues(resolved_config)
    if config_errors:
        return fallback_report(f"AI 服务配置错误：{', '.join(config_errors)}")
    if "api_key" in missing_config:
        return fallback_report("未配置 AI 服务密钥")
    if missing_config:
        return fallback_report(f"AI 服务配置缺失：{', '.join(missing_config)}")

    try:
        resolved_provider = provider or create_diagnosis_provider(resolved_config)
        return resolved_provider.generate(prompt)
    except Exception as exc:
        return fallback_report(str(exc))
