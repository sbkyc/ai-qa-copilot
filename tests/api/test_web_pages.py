from __future__ import annotations

from urllib.parse import parse_qs, urlparse

from tests.helpers import clear_provider_env


def get_signed_in_products_page(client):
    client.cookies.set("qa_user", "alice")
    return client.get("/products")


def test_dashboard_page_renders_diagnosis_workspace(client):
    response = client.get("/")

    assert response.status_code == 200
    assert "AI QA 诊断工作台" in response.text
    assert 'action="/diagnose"' in response.text
    assert 'name="nodeid"' in response.text
    assert 'name="phase"' in response.text
    assert 'name="keywords"' in response.text
    assert 'name="longrepr"' in response.text
    assert "粘贴 pytest / Playwright / API 失败日志" in response.text
    assert "生成中文诊断报告" in response.text
    assert "示例失败日志" in response.text
    assert "面试官审阅模式" in response.text


def test_dashboard_uses_chinese_first_ui_labels(client):
    response = client.get("/")

    assert response.status_code == 200
    for phrase in (
        "工作台",
        "AI 报告",
        "示例系统",
        "审阅模式",
        "失败模式矩阵",
        "本地备用模式",
        "生成备用报告",
        "接口契约",
        "偶发/时序",
        "环境/初始化",
        "失败模式",
    ):
        assert phrase in response.text
    for phrase in (
        "Workbench",
        "AI Report",
        "Demo Shop",
        "Review",
        "Failure Mode",
        "fallback",
        "API contract",
        "Flaky / timing",
        "Environment/setup",
    ):
        assert phrase not in response.text


def test_public_pages_do_not_render_mojibake(client):
    client.cookies.set("qa_user", "alice")
    pages = [
        client.get("/"),
        client.get("/login"),
        client.get("/products"),
        client.get("/interview-review"),
        client.get("/diagnosis-report"),
        client.post("/orders", data={"product_id": "1", "quantity": "1"}),
    ]
    mojibake_markers = (
        "璇婃柇",
        "宸ヤ綔",
        "涓枃",
        "鍒锋柊",
        "鐢熸垚",
        "闈㈣瘯",
        "�",
    )

    for response in pages:
        assert response.status_code == 200
        for marker in mojibake_markers:
            assert marker not in response.text


def test_dashboard_explains_ai_and_artifact_boundaries(client, tmp_path, monkeypatch):
    monkeypatch.setenv("AI_QA_REPORT_PATH", str(tmp_path / "missing-report.md"))

    response = client.get("/")

    assert response.status_code == 200
    assert "候选根因" in response.text
    assert "诊断假设" in response.text
    assert "不展示密钥或内部配置" in response.text
    assert "AI 不替代 pytest / Playwright / CI" in response.text


def test_dashboard_hides_internal_implementation_details(client):
    response = client.get("/")

    assert response.status_code == 200
    for phrase in (
        "API Docs",
        "Provider Health API",
        "GitHub PR/Issues API",
        "raw logs",
        "stack traces",
        "provider preset",
        "reports/latest",
        "reports/examples",
        "qa-reports",
        "demo-qa-reports",
        "pytest-report.html",
        "failure JSON",
        "pr-comment.md",
    ):
        assert phrase not in response.text


def test_dashboard_links_to_supporting_surfaces(client):
    response = client.get("/")

    assert response.status_code == 200
    assert 'href="/interview-review"' in response.text
    assert 'href="/login"' in response.text
    assert 'href="/diagnosis-report"' in response.text


def test_web_diagnosis_form_generates_report(client, tmp_path, monkeypatch):
    report_path = tmp_path / "web-ai-diagnosis.md"
    captured: dict[str, str] = {}

    def fake_diagnose(prompt: str) -> str:
        captured["prompt"] = prompt
        return """## 摘要

表单输入已生成诊断。

## Failure Mode Matrix（失败模式矩阵）

| 失败模式 | 影响测试 | 证据 | 可能分类 | 下一步 |
| --- | --- | --- | --- | --- |
| API contract | test_contract | expected 201 got 422 | 契约漂移 | 对齐 schema。 |
"""

    monkeypatch.setenv("AI_QA_REPORT_PATH", str(report_path))
    monkeypatch.setattr("app.main.diagnose_with_ai", fake_diagnose)

    response = client.post(
        "/diagnose",
        data={
            "nodeid": "tests/api/test_orders.py::test_contract",
            "phase": "call",
            "keywords": "api, contract",
            "longrepr": "AssertionError: expected 201 got 422",
        },
        follow_redirects=False,
    )

    assert response.status_code == 303
    assert response.headers["location"] == "/diagnosis-report"
    assert report_path.read_text(encoding="utf-8").startswith("# 中文 AI 诊断报告")
    assert "表单输入已生成诊断" in report_path.read_text(encoding="utf-8")
    assert "tests/api/test_orders.py::test_contract" in captured["prompt"]
    assert "AssertionError: expected 201 got 422" in captured["prompt"]


def test_web_diagnosis_form_creates_timestamped_history_report(client, tmp_path, monkeypatch):
    captured: dict[str, str] = {}

    def fake_diagnose(prompt: str) -> str:
        captured["prompt"] = prompt
        return """## 摘要

历史报告已生成。

## Failure Mode Matrix（失败模式矩阵）

| 失败模式 | 影响测试 | 证据 | 可能分类 | 下一步 |
| --- | --- | --- | --- | --- |
| API contract | test_contract | expected 201 got 422 | 契约漂移 | 对齐 schema。 |
"""

    monkeypatch.delenv("AI_QA_REPORT_PATH", raising=False)
    monkeypatch.setenv("AI_QA_REPORT_DIR", str(tmp_path))
    monkeypatch.setattr("app.main.diagnose_with_ai", fake_diagnose)

    response = client.post(
        "/diagnose",
        data={
            "nodeid": "tests/api/test_orders.py::test_contract",
            "phase": "call",
            "keywords": "api, contract",
            "longrepr": "AssertionError: expected 201 got 422",
        },
        follow_redirects=False,
    )

    assert response.status_code == 303
    parsed = urlparse(response.headers["location"])
    assert parsed.path == "/diagnosis-report"
    report_name = parse_qs(parsed.query)["report"][0]
    assert report_name.startswith("web-ai-diagnosis-")
    assert report_name.endswith(".md")
    assert (tmp_path / report_name).is_file()
    assert "tests/api/test_orders.py::test_contract" in captured["prompt"]


def test_dashboard_shows_recent_diagnosis_history(client, tmp_path, monkeypatch):
    older = tmp_path / "web-ai-diagnosis-20260706-120000.md"
    older.write_text(
        "# 中文 AI 诊断报告\n\n## 摘要\n较早的接口契约诊断。\n",
        encoding="utf-8",
    )
    newer = tmp_path / "web-ai-diagnosis-20260706-121500.md"
    newer.write_text(
        "# 中文 AI 诊断报告\n\n## 摘要\n最新的 Playwright 可见性诊断。\n",
        encoding="utf-8",
    )
    monkeypatch.delenv("AI_QA_REPORT_PATH", raising=False)
    monkeypatch.setenv("AI_QA_REPORT_DIR", str(tmp_path))

    response = client.get("/")

    assert response.status_code == 200
    assert "最近诊断" in response.text
    assert "最新的 Playwright 可见性诊断" in response.text
    assert "较早的接口契约诊断" in response.text
    assert 'href="/diagnosis-report?report=web-ai-diagnosis-20260706-121500.md"' in response.text
    assert 'href="/diagnosis-report?report=web-ai-diagnosis-20260706-120000.md"' in response.text


def test_diagnosis_report_page_can_render_selected_history_report(
    client, tmp_path, monkeypatch
):
    selected = tmp_path / "web-ai-diagnosis-20260706-121500.md"
    selected.write_text(
        """# 中文 AI 诊断报告

## 摘要
这是被选中的历史报告。

### Failure Mode Matrix（失败模式矩阵）

| 失败模式 | 影响测试 | 证据 | 可能分类 | 下一步 |
|---|---|---|---|---|
| UI/E2E behavior | test_checkout | button hidden | UI 状态问题 | 检查前置条件。 |
""",
        encoding="utf-8",
    )
    monkeypatch.delenv("AI_QA_REPORT_PATH", raising=False)
    monkeypatch.setenv("AI_QA_REPORT_DIR", str(tmp_path))

    response = client.get(
        "/diagnosis-report?report=web-ai-diagnosis-20260706-121500.md"
    )

    assert response.status_code == 200
    assert "这是被选中的历史报告" in response.text
    assert "UI/E2E 行为" in response.text


def test_diagnosis_report_page_rejects_unsafe_history_report_name(
    client, tmp_path, monkeypatch
):
    monkeypatch.delenv("AI_QA_REPORT_PATH", raising=False)
    monkeypatch.setenv("AI_QA_REPORT_DIR", str(tmp_path))

    response = client.get("/diagnosis-report?report=../secret.md")

    assert response.status_code == 404


def test_interview_review_page_explains_project_value(client):
    response = client.get("/interview-review")

    assert response.status_code == 200
    assert "面试官审阅模式" in response.text
    assert "我会怎么审这个项目" in response.text
    assert "测试证据链" in response.text
    assert "API / Service / E2E / CI" in response.text
    assert "失败模式矩阵" in response.text
    assert "安全边界" in response.text
    assert "3 分钟讲解顺序" in response.text
    assert "候选根因 / 诊断假设" in response.text
    assert "执行阶段" in response.text
    assert "准备阶段" in response.text
    assert ">call<" not in response.text
    assert ">setup<" not in response.text
    for phrase in (
        "API Docs",
        "Provider Health API",
        "reports/latest",
        "reports/examples",
        "raw logs",
        "stack traces",
    ):
        assert phrase not in response.text


def test_dashboard_ai_mode_card_is_redacted(client, monkeypatch):
    clear_provider_env(monkeypatch)
    monkeypatch.setenv("AI_PROVIDER", "openai-compatible")
    monkeypatch.setenv("AI_API_KEY", "fake-gateway-key")
    monkeypatch.setenv("AI_MODEL", "tenant-routed-model")
    monkeypatch.setenv("AI_BASE_URL", "https://tenant.internal.example/v1")

    response = client.get("/")

    assert response.status_code == 200
    assert "AI 诊断模式" in response.text
    assert "实时 AI 已连接" in response.text
    assert "可现场生成中文诊断" in response.text
    assert "隐藏内部配置" in response.text
    assert "openai-compatible" not in response.text
    assert "API 风格" not in response.text
    assert "密钥状态" not in response.text
    assert "fake-gateway-key" not in response.text
    assert "AI_API_KEY" not in response.text
    assert "tenant-routed-model" not in response.text
    assert "tenant.internal.example" not in response.text


def test_dashboard_presents_fallback_mode_without_broken_provider_warning(client):
    response = client.get("/")

    assert response.status_code == 200
    assert "AI 诊断模式" in response.text
    assert "本地备用模式" in response.text
    assert "AI 服务未连接" not in response.text


def test_dashboard_shows_latest_ai_report_preview(client, tmp_path, monkeypatch):
    report = tmp_path / "latest-ai-diagnosis.md"
    report.write_text(
        """# AI 诊断报告

## 摘要
DeepSeek 根据失败证据识别出 API、UI、偶发时序和环境初始化问题。

### Failure Mode Matrix（失败模式矩阵）

| 失败模式 | 影响测试 | 证据 | 可能分类 | 下一步 |
|---|---|---|---|---|
| Product/API behavior | `test_stock` | 期望 409 | 产品缺陷 | 映射库存异常。 |
| UI/E2E behavior | `test_checkout` | 按钮隐藏 | UI 状态问题 | 检查前置条件。 |
""",
        encoding="utf-8",
    )
    monkeypatch.setenv("AI_QA_REPORT_PATH", str(report))

    response = client.get("/")

    assert response.status_code == 200
    assert "中文 AI 诊断报告" in response.text
    assert "DeepSeek 根据失败证据识别出 API" in response.text
    assert "产品/API 行为" in response.text
    assert "test_stock" in response.text
    assert "查看完整中文 AI 诊断报告" in response.text
    assert 'href="/diagnosis-report"' in response.text


def test_diagnosis_report_page_renders_escaped_markdown(client, tmp_path, monkeypatch):
    report = tmp_path / "latest-ai-diagnosis.md"
    report.write_text(
        """# AI 诊断报告

## 摘要
报告渲染应安全处理代码：`<script>alert("x")</script>`。

### Failure Mode Matrix（失败模式矩阵）

| 失败模式 | 影响测试 | 证据 | 可能分类 | 下一步 |
|---|---|---|---|---|
| API contract | `test_contract` | 422 validation error | 契约漂移 | 对齐请求 schema。 |
""",
        encoding="utf-8",
    )
    monkeypatch.setenv("AI_QA_REPORT_PATH", str(report))

    response = client.get("/diagnosis-report")

    assert response.status_code == 200
    assert "中文 AI 诊断报告" in response.text
    assert "接口契约" in response.text
    assert "报告渲染应安全处理代码" in response.text
    assert "<script>" not in response.text
    assert "&lt;script&gt;" in response.text


def test_diagnosis_report_page_localizes_common_english_report_terms(
    client, tmp_path, monkeypatch
):
    report = tmp_path / "latest-ai-diagnosis.md"
    report.write_text(
        """# AI 诊断报告

## Summary
English section names should be readable in Chinese.

### Failure Mode Matrix

| Failure Mode | Affected Test | Evidence | Likely Classification | Next Action |
|---|---|---|---|---|
| API contract | `test_contract` | 422 validation error | Contract drift | Align schema. |
| Flaky/timing | `test_search` | 7 pass / 3 fail | Flaky test | Wait for stable state. |
""",
        encoding="utf-8",
    )
    monkeypatch.setenv("AI_QA_REPORT_PATH", str(report))

    response = client.get("/diagnosis-report")

    assert response.status_code == 200
    for phrase in (
        "摘要",
        "失败模式矩阵",
        "失败模式",
        "影响测试",
        "可能分类",
        "下一步",
        "接口契约",
        "偶发/时序",
    ):
        assert phrase in response.text
    for phrase in (
        "Summary",
        "Failure Mode",
        "Affected Test",
        "Likely Classification",
        "Next Action",
        "API contract",
        "Flaky/timing",
    ):
        assert phrase not in response.text


def test_login_page_renders(client):
    response = client.get("/login")

    assert response.status_code == 200
    assert "AI QA 演示商店" in response.text
    assert "用户名" in response.text
    assert "密码" in response.text


def test_login_page_links_stylesheet(client):
    response = client.get("/login")

    assert response.status_code == 200
    assert 'href="/static/styles.css"' in response.text


def test_web_login_redirects_to_products(client):
    response = client.post(
        "/login",
        data={"username": "alice", "password": "password123"},
        follow_redirects=False,
    )

    assert response.status_code == 303
    assert response.headers["location"] == "/products"


def test_products_page_requires_login(client):
    response = client.get("/products", follow_redirects=False)

    assert response.status_code == 303
    assert response.headers["location"] == "/login"


def test_order_success_page_explains_qa_next_steps(client):
    client.cookies.set("qa_user", "alice")

    response = client.post("/orders", data={"product_id": "1", "quantity": "1"})

    assert response.status_code == 200
    assert "订单创建成功" in response.text
    assert "这一步证明示例系统是真实被测系统" in response.text
    assert "下单成功不是终点" in response.text
    assert "真正的项目价值不在买商品" in response.text
    assert "失败证据" in response.text
    assert "中文 AI 诊断报告" in response.text
    assert "测试覆盖设计" in response.text
    assert "返回工作台" in response.text
    assert "查看中文 AI 报告" in response.text
    assert "继续测试下单" in response.text


def test_order_success_page_hides_file_paths_and_raw_api_links(client):
    client.cookies.set("qa_user", "alice")

    response = client.post("/orders", data={"product_id": "1", "quantity": "1"})

    assert response.status_code == 200
    for phrase in (
        "API Docs",
        "Provider Health API",
        "reports/latest",
        "reports/examples",
        "pr-comment.md",
    ):
        assert phrase not in response.text


def test_demo_pages_hide_api_docs_nav(client):
    login_response = client.get("/login")
    client.cookies.set("qa_user", "alice")
    products_response = client.get("/products")

    assert login_response.status_code == 200
    assert products_response.status_code == 200
    assert "API Docs" not in login_response.text
    assert "API Docs" not in products_response.text


def test_products_page_shows_redacted_provider_status(client, monkeypatch):
    clear_provider_env(monkeypatch)
    monkeypatch.setenv("AI_PROVIDER", "openai-compatible")
    monkeypatch.setenv("AI_API_KEY", "fake-gateway-key")
    monkeypatch.setenv("AI_MODEL", "tenant-routed-model")
    monkeypatch.setenv("AI_BASE_URL", "https://tenant.internal.example/v1")

    response = get_signed_in_products_page(client)

    assert response.status_code == 200
    assert "AI 服务状态" in response.text
    assert "已就绪" in response.text
    assert "openai-compatible" in response.text
    assert "隐藏内部配置" in response.text
    assert "API 风格" not in response.text
    assert "密钥状态" not in response.text
    assert "fake-gateway-key" not in response.text
    assert "AI_API_KEY" not in response.text
    assert "tenant-routed-model" not in response.text
    assert "tenant.internal.example" not in response.text


def test_products_page_shows_missing_base_url_provider_status(client, monkeypatch):
    clear_provider_env(monkeypatch)
    monkeypatch.setenv("AI_PROVIDER", "openai-compatible")
    monkeypatch.setenv("AI_API_KEY", "fake-gateway-key")

    response = get_signed_in_products_page(client)

    assert response.status_code == 200
    assert "AI 服务状态" in response.text
    assert "AI 服务未连接" in response.text
    assert "如需使用兼容网关，请先完成服务连接配置。" in response.text


def test_products_page_shows_unsupported_provider_status(client, monkeypatch):
    clear_provider_env(monkeypatch)
    monkeypatch.setenv("AI_PROVIDER", "deepssek")
    monkeypatch.setenv("AI_API_KEY", "fake-key")

    response = get_signed_in_products_page(client)

    assert response.status_code == 200
    assert "AI 服务状态" in response.text
    assert "不支持的 AI 服务" in response.text
    assert "检查 AI 服务名称是否拼写正确。" in response.text
    assert "fake-key" not in response.text


def test_products_page_shows_unsupported_api_style_status(client, monkeypatch):
    clear_provider_env(monkeypatch)
    monkeypatch.setenv("AI_PROVIDER", "deepseek")
    monkeypatch.setenv("DEEPSEEK_API_KEY", "fake-deepseek-key")
    monkeypatch.setenv("AI_API_STYLE", "chta")

    response = get_signed_in_products_page(client)

    assert response.status_code == 200
    assert "AI 服务状态" in response.text
    assert "AI 服务配置需检查" in response.text
    assert "检查 AI 服务调用方式配置。" in response.text
    assert "fake-deepseek-key" not in response.text
