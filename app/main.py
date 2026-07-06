import os
import sqlite3
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from datetime import UTC, datetime
from html import escape
from pathlib import Path
from typing import Annotated

from fastapi import Depends, FastAPI, Header, HTTPException, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from app.db import connect, initialize_database, seed_database
from app.schemas import (
    DiagnosisRequest,
    DiagnosisResponse,
    LoginRequest,
    LoginResponse,
    OrderRequest,
    ProviderHealthResponse,
)
from app.services import (
    AuthenticationError,
    InsufficientStockError,
    ProductNotFoundError,
    authenticate_user,
    create_order,
    get_product,
    list_products,
    token_for_username,
    username_from_token,
)
from qa_copilot.artifacts import FailureArtifact, load_failure_artifacts
from qa_copilot.diagnosis import diagnose_with_ai
from qa_copilot.prompt_builder import build_diagnosis_prompt
from qa_copilot.provider_health import check_provider_health
from qa_copilot.providers import supported_provider_specs
from qa_copilot.report_writer import write_markdown_report

templates = Jinja2Templates(directory="app/templates")

PROVIDER_ISSUE_LABELS = {
    "api_key": "AI 服务未连接",
    "base_url": "AI 服务未连接",
    "model": "缺少模型配置",
    "unsupported_provider": "不支持的 AI 服务",
    "unsupported_api_style": "AI 服务配置需检查",
}

PROVIDER_ISSUE_HINTS = {
    "api_key": "如需现场生成诊断，请先连接 AI 服务。",
    "base_url": "如需使用兼容网关，请先完成服务连接配置。",
    "model": "为当前 AI 服务配置模型。",
    "unsupported_provider": "检查 AI 服务名称是否拼写正确。",
    "unsupported_api_style": "检查 AI 服务调用方式配置。",
}

TEST_COVERAGE_CARDS = [
    {
        "title": "API 接口测试",
        "badge": "pytest / FastAPI TestClient",
        "body": (
            "验证登录、商品查询、订单创建、库存不足和错误响应，"
            "重点看状态码、响应体和边界条件。"
        ),
        "checks": [
            "鉴权失败返回 401",
            "库存不足返回 409",
            "商品不存在返回 404",
            "请求体验证返回 422",
        ],
    },
    {
        "title": "Service 业务规则测试",
        "badge": "pytest unit/service",
        "body": (
            "绕开页面直接验证核心业务规则，保证库存扣减、用户认证和订单状态"
            "不依赖浏览器才能发现问题。"
        ),
        "checks": ["认证逻辑", "库存扣减", "订单状态", "异常分支"],
    },
    {
        "title": "浏览器 E2E 测试",
        "badge": "Playwright",
        "body": (
            "覆盖真实用户路径：进入系统、登录、查看商品、创建订单。"
            "它证明被测系统不是静态页面，而是可自动化验证的业务流程。"
        ),
        "checks": ["登录流程", "商品列表", "创建订单", "错误提示"],
    },
    {
        "title": "CI 验证链路",
        "badge": "GitHub Actions",
        "body": (
            "每次提交自动跑 lint、API 测试、E2E 测试，并保留报告产物，"
            "面试时能证明测试不是只在本机跑过。"
        ),
        "checks": ["Ruff", "pytest", "Playwright", "诊断报告"],
    },
]

INTERVIEW_REVIEW_CARDS = [
    {
        "title": "你测了什么",
        "body": "页面把 API、Service、E2E 和 CI 分开展示，避免只说“我写了自动化测试”。",
    },
    {
        "title": "失败怎么定位",
        "body": "失败样例会展示 phase、测试节点、关键证据和可能责任边界，方便讲定位思路。",
    },
    {
        "title": "AI 有什么价值",
        "body": "AI 报告只做辅助归类和候选根因，不替代 pytest / Playwright 的质量门禁。",
    },
    {
        "title": "安全边界在哪里",
        "body": "页面只展示连接状态和脱敏摘要，不展示密钥、内部地址或运行时配置来源。",
    },
]

INTERVIEW_SCORECARDS = [
    {
        "title": "测试设计",
        "grade": "可面试展示",
        "body": "API / Service / E2E / CI 分层明确，能说明每层测试解决的质量风险。",
    },
    {
        "title": "失败证据",
        "grade": "证据链完整",
        "body": "失败会沉淀结构化 artifact、可读报告和 review 摘要，不只停留在红绿灯。",
    },
    {
        "title": "AI 价值",
        "grade": "辅助诊断",
        "body": "AI 输出 Failure Mode Matrix、候选根因 / 诊断假设和下一步，不替代测试门禁。",
    },
    {
        "title": "安全边界",
        "grade": "可公开讲",
        "body": "公开页面不展示密钥、内部地址、模型名或 key source，只展示脱敏状态和安全摘要。",
    },
]

INTERVIEW_REVIEW_STEPS = [
    "先看 AI QA 诊断工作台，确认项目不是电商 Demo，而是可直接使用的失败诊断工具。",
    "再看测试覆盖，说明 API / Service / E2E / CI 各自验证什么。",
    "进入 Demo Shop 下单，证明被测系统有真实登录、商品、库存和订单路径。",
    "最后看中文 AI 报告，讲 Failure Mode Matrix、证据、候选根因和下一步建议。",
]

DASHBOARD_PIPELINE_STEPS = [
    "被测业务路径",
    "自动化断言",
    "结构化失败证据",
    "中文 AI 诊断",
    "Failure Mode Matrix",
    "团队 Review 摘要",
]

FAILURE_MODE_ROWS = [
    {
        "mode": "Product/API behavior",
        "example": "库存不足返回状态码不符合预期",
        "evidence": "API status mismatch",
        "next_action": "检查业务异常到 HTTP 409 的映射。",
    },
    {
        "mode": "API contract",
        "example": "请求/响应契约漂移",
        "evidence": "422 validation error",
        "next_action": "对齐 request body、schema 和测试契约。",
    },
    {
        "mode": "UI/E2E behavior",
        "example": "Playwright 等待按钮可见失败",
        "evidence": "locator visibility assertion",
        "next_action": "检查页面状态、按钮禁用逻辑和截图证据。",
    },
    {
        "mode": "Flaky/timing",
        "example": "搜索结果偶发失败",
        "evidence": "10 次运行中失败 3 次",
        "next_action": "稳定等待条件，排查 debounce / fetch race。",
    },
    {
        "mode": "Environment/setup",
        "example": "fixture 初始化数据库失败",
        "evidence": "no such table during setup",
        "next_action": "检查 fixture 顺序、迁移和测试隔离。",
    },
]

ARTIFACT_CARDS = [
    {
        "title": "CI 报告包",
        "kind": "真实 CI 产物",
        "body": (
            "CI 上传的测试报告、结构化失败证据、AI 诊断和 PR 摘要预览。"
        ),
    },
    {
        "title": "演示报告包",
        "kind": "手动生成的安全演示报告包",
        "body": "基于安全示例数据生成，适合稳定面试展示，不代表当前真实故障。",
    },
]

REPORT_FALLBACK_PATH = Path("reports/examples/sample-ai-diagnosis.md")
WEB_REPORT_PATH = Path("reports/latest/web-ai-diagnosis.md")


def _plain_markdown(text: str) -> str:
    return (
        text.replace("**", "")
        .replace("`", "")
        .replace("<br>", " ")
        .replace("<br/>", " ")
        .strip()
    )


def _split_markdown_table_row(line: str) -> list[str]:
    return [_plain_markdown(cell) for cell in line.strip().strip("|").split("|")]


def _find_latest_report_path() -> Path | None:
    override = os.getenv("AI_QA_REPORT_PATH")
    if override:
        path = Path(override)
        return path if path.is_file() else None

    latest_dir = Path("reports/latest")
    preferred_reports = [
        latest_dir / "web-ai-diagnosis.md",
        latest_dir / "deepseek-ai-diagnosis-zh.md",
        latest_dir / "deepseek-ai-diagnosis.md",
        latest_dir / "ai-diagnosis-zh.md",
        latest_dir / "ai-diagnosis.md",
    ]
    for path in preferred_reports:
        if path.is_file():
            return path

    candidates = [
        path
        for path in latest_dir.glob("*diagnosis*.md")
        if path.is_file() and path.name != "pr-comment.md"
    ]
    if candidates:
        return max(candidates, key=lambda path: path.stat().st_mtime)
    if REPORT_FALLBACK_PATH.is_file():
        return REPORT_FALLBACK_PATH
    return None


def _web_report_path() -> Path:
    override = os.getenv("AI_QA_REPORT_PATH")
    if override:
        return Path(override)
    return WEB_REPORT_PATH


def _extract_report_summary(markdown: str) -> str:
    lines = markdown.splitlines()
    for index, line in enumerate(lines):
        if line.strip().lower() in {"## summary", "### summary", "## 摘要", "### 摘要"}:
            summary_lines: list[str] = []
            for candidate in lines[index + 1 :]:
                stripped = candidate.strip()
                if stripped.startswith("#"):
                    break
                if stripped and stripped != "---":
                    summary_lines.append(_plain_markdown(stripped))
            return " ".join(summary_lines).strip()
    for line in lines:
        stripped = line.strip()
        if stripped and not stripped.startswith("#") and stripped != "---":
            return _plain_markdown(stripped)
    return "报告已生成，可打开完整页面查看。"


def _extract_report_matrix(markdown: str) -> list[dict[str, str]]:
    lines = markdown.splitlines()
    for index, line in enumerate(lines):
        if ("Failure Mode" not in line and "失败模式" not in line) or "|" not in line:
            continue
        rows: list[dict[str, str]] = []
        for candidate in lines[index + 2 :]:
            if not candidate.strip().startswith("|"):
                break
            cells = _split_markdown_table_row(candidate)
            if len(cells) < 5:
                continue
            rows.append(
                {
                    "mode": cells[0],
                    "test": cells[1],
                    "evidence": cells[2],
                    "classification": cells[3],
                    "next_action": cells[4],
                }
            )
        return rows[:6]
    return []


def _render_inline_markdown(text: str) -> str:
    parts = text.split("`")
    rendered: list[str] = []
    for index, part in enumerate(parts):
        safe = escape(part)
        if index % 2:
            rendered.append(f"<code>{safe}</code>")
        else:
            rendered.append(safe)
    joined = "".join(rendered)
    while "**" in joined:
        joined = joined.replace("**", "", 2)
    return joined


def _render_markdown_document(markdown: str) -> str:
    html_parts: list[str] = []
    lines = markdown.splitlines()
    index = 0
    skipped_document_title = False
    while index < len(lines):
        line = lines[index].rstrip()
        stripped = line.strip()
        if not stripped:
            index += 1
            continue
        if stripped == "---":
            html_parts.append("<hr>")
            index += 1
            continue
        if stripped.startswith("|"):
            table_lines: list[str] = []
            while index < len(lines) and lines[index].strip().startswith("|"):
                table_lines.append(lines[index].strip())
                index += 1
            if table_lines:
                headers = _split_markdown_table_row(table_lines[0])
                body_lines = [
                    row
                    for row in table_lines[2:]
                    if not set(row.replace("|", "").strip()) <= {"-", ":"}
                ]
                html_parts.append(
                    '<div class="report-table-scroll">'
                    '<table class="matrix-table report-table">'
                )
                html_parts.append(
                    "<thead><tr>"
                    + "".join(f"<th>{_render_inline_markdown(header)}</th>" for header in headers)
                    + "</tr></thead>"
                )
                html_parts.append("<tbody>")
                for body_line in body_lines:
                    cells = _split_markdown_table_row(body_line)
                    html_parts.append(
                        "<tr>"
                        + "".join(f"<td>{_render_inline_markdown(cell)}</td>" for cell in cells)
                        + "</tr>"
                    )
                html_parts.append("</tbody></table></div>")
            continue
        if stripped.startswith("#"):
            level = min(len(stripped) - len(stripped.lstrip("#")), 3)
            text = stripped[level:].strip()
            if level == 1 and not skipped_document_title:
                skipped_document_title = True
                index += 1
                continue
            html_parts.append(f"<h{level}>{_render_inline_markdown(text)}</h{level}>")
            index += 1
            continue
        if stripped.startswith("- "):
            html_parts.append("<ul>")
            while index < len(lines) and lines[index].strip().startswith("- "):
                item = lines[index].strip()[2:].strip()
                html_parts.append(f"<li>{_render_inline_markdown(item)}</li>")
                index += 1
            html_parts.append("</ul>")
            continue
        if len(stripped) > 3 and stripped[0].isdigit() and ". " in stripped[:5]:
            html_parts.append("<ol>")
            while index < len(lines):
                candidate = lines[index].strip()
                if not (len(candidate) > 3 and candidate[0].isdigit() and ". " in candidate[:5]):
                    break
                item = candidate.split(". ", 1)[1]
                html_parts.append(f"<li>{_render_inline_markdown(item)}</li>")
                index += 1
            html_parts.append("</ol>")
            continue

        paragraph_lines = [stripped]
        index += 1
        while index < len(lines):
            candidate = lines[index].strip()
            if (
                not candidate
                or candidate.startswith("#")
                or candidate.startswith("|")
                or candidate.startswith("- ")
                or candidate == "---"
                or (len(candidate) > 3 and candidate[0].isdigit() and ". " in candidate[:5])
            ):
                break
            paragraph_lines.append(candidate)
            index += 1
        paragraph = " ".join(paragraph_lines)
        html_parts.append(f"<p>{_render_inline_markdown(paragraph)}</p>")
    return "\n".join(html_parts)


def _latest_report_view_model() -> dict[str, object]:
    path = _find_latest_report_path()
    if path is None:
        return {
            "available": False,
            "title": "最新 AI 诊断报告",
            "summary": "还没有生成报告。连接 AI 服务后运行诊断，就会在这里展示。",
            "matrix_rows": [],
            "html": "",
        }
    markdown = path.read_text(encoding="utf-8")
    return {
        "available": True,
        "title": "最新 AI 诊断报告",
        "summary": _extract_report_summary(markdown),
        "matrix_rows": _extract_report_matrix(markdown),
        "html": _render_markdown_document(markdown),
    }


def _resolve_db_path(db_path: str | Path | None) -> str | Path:
    if db_path is not None:
        return db_path
    return os.getenv("AI_QA_DB_PATH", "reports/latest/dev.sqlite")


def _extract_bearer_token(authorization: str | None) -> str:
    if authorization is None or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Missing bearer token")
    return authorization.removeprefix("Bearer ").strip()


def _provider_health_view_model() -> dict[str, object]:
    health = check_provider_health()
    missing = [str(item) for item in health["missing"]]
    errors = [str(item) for item in health["errors"]]
    issue_codes = [*errors, *missing]
    issues = [
        {
            "label": PROVIDER_ISSUE_LABELS.get(code, code.replace("_", " ").title()),
            "hint": PROVIDER_ISSUE_HINTS.get(code, "检查 AI 服务环境变量配置。"),
        }
        for code in issue_codes
    ]
    return {
        "ok": health["ok"],
        "provider": health["provider"],
        "api_style": health["api_style"],
        "api_key_configured": health["api_key_configured"],
        "status_label": "已就绪" if health["ok"] else issues[0]["label"],
        "issues": issues,
    }


def _dashboard_ai_mode_view_model(
    provider_health: dict[str, object],
) -> dict[str, object]:
    if provider_health["ok"]:
        return {
            "ok": True,
            "status_label": "实时 AI 已连接",
            "mode_label": "可现场生成中文诊断",
            "body": "已连接实时 AI 诊断能力，页面仍隐藏密钥、模型和内部地址。",
        }

    issue_labels = {
        str(issue["label"])
        for issue in provider_health["issues"]
        if isinstance(issue, dict) and "label" in issue
    }
    if issue_labels.difference({"AI 服务未连接"}):
        return {
            "ok": False,
            "status_label": "AI 配置需检查",
            "mode_label": "本地报告可用",
            "body": "现场生成前需要检查 AI 配置；工作台仍可展示安全样例和已生成报告。",
        }

    return {
        "ok": False,
        "status_label": "本地 fallback 模式",
        "mode_label": "不影响面试演示",
        "body": "未连接实时 AI 时，仍可展示安全样例、fallback 报告和完整测试证据链。",
    }


def _failure_mode_display(artifact: FailureArtifact) -> tuple[str, str]:
    keywords = {keyword.lower() for keyword in artifact.keywords}
    phase = artifact.phase.lower()
    if phase == "setup" or keywords.intersection({"fixture", "setup"}):
        return "环境 / fixture 问题", "说明失败发生在测试前置阶段，不应误判为业务缺陷。"
    if "flaky" in keywords:
        return "偶发 / 时序问题", "说明自动化测试需要关注等待条件、异步请求和稳定性。"
    if keywords.intersection({"api-assertion", "contract"}):
        return "API 契约问题", "说明接口请求体、响应 schema 或前后端契约发生漂移。"
    if keywords.intersection({"playwright", "e2e", "visibility"}):
        return "UI / E2E 行为问题", "说明浏览器路径能捕获用户实际看得到的页面状态问题。"
    if "api" in keywords:
        return "产品 / API 行为问题", "说明接口状态码、业务异常映射或服务端处理不符合预期。"
    return "未分类失败", "说明需要先补充 keywords 或失败上下文，才能稳定归因。"


def _short_failure_evidence(longrepr: str) -> str:
    for line in longrepr.splitlines():
        stripped = line.strip()
        if stripped:
            return stripped[:160]
    return "失败证据为空，需要检查测试产物采集逻辑。"


def _display_test_name(nodeid: str) -> str:
    return nodeid.rsplit("::", 1)[-1].replace("_", " ")


def _parse_keywords(raw_keywords: str) -> list[str]:
    normalized = raw_keywords.replace("，", ",").replace("\n", ",")
    return [
        keyword.strip()
        for keyword in normalized.split(",")
        if keyword.strip()
    ]


def _failure_evidence_cards(artifacts: list[FailureArtifact]) -> list[dict[str, str]]:
    cards: list[dict[str, str]] = []
    for artifact in artifacts[:6]:
        mode, qa_value = _failure_mode_display(artifact)
        cards.append(
            {
                "mode": mode,
                "test_name": _display_test_name(artifact.nodeid),
                "phase": artifact.phase,
                "evidence": _short_failure_evidence(artifact.longrepr),
                "qa_value": qa_value,
            }
        )
    return cards


def _dashboard_context(db: sqlite3.Connection) -> dict[str, object]:
    sample_artifacts = load_failure_artifacts("reports/examples")
    provider_specs = supported_provider_specs()
    provider_health = _provider_health_view_model()
    return {
        "provider_health": provider_health,
        "ai_mode": _dashboard_ai_mode_view_model(provider_health),
        "product_count": len(list_products(db)),
        "coverage_count": len(TEST_COVERAGE_CARDS),
        "sample_artifact_count": len(sample_artifacts),
        "provider_count": len(provider_specs),
        "provider_names": list(provider_specs),
        "coverage_cards": TEST_COVERAGE_CARDS,
        "review_cards": INTERVIEW_REVIEW_CARDS,
        "pipeline_steps": DASHBOARD_PIPELINE_STEPS,
        "failure_mode_rows": FAILURE_MODE_ROWS,
        "failure_evidence_cards": _failure_evidence_cards(sample_artifacts),
        "artifact_cards": ARTIFACT_CARDS,
        "latest_report": _latest_report_view_model(),
    }


def _interview_review_context(db: sqlite3.Connection) -> dict[str, object]:
    sample_artifacts = load_failure_artifacts("reports/examples")
    provider_health = _provider_health_view_model()
    return {
        "ai_mode": _dashboard_ai_mode_view_model(provider_health),
        "product_count": len(list_products(db)),
        "scorecards": INTERVIEW_SCORECARDS,
        "coverage_cards": TEST_COVERAGE_CARDS,
        "pipeline_steps": DASHBOARD_PIPELINE_STEPS,
        "review_steps": INTERVIEW_REVIEW_STEPS,
        "failure_evidence_cards": _failure_evidence_cards(sample_artifacts),
        "latest_report": _latest_report_view_model(),
    }


def create_app(db_path: str | Path | None = None) -> FastAPI:
    resolved_db_path = _resolve_db_path(db_path)

    @asynccontextmanager
    async def lifespan(api: FastAPI) -> AsyncIterator[None]:
        if resolved_db_path != ":memory:":
            Path(resolved_db_path).parent.mkdir(parents=True, exist_ok=True)
        connection = connect(resolved_db_path)
        initialize_database(connection)
        seed_database(connection)
        api.state.db = connection
        try:
            yield
        finally:
            connection.close()

    api = FastAPI(title="AI QA Copilot Demo Shop", lifespan=lifespan)
    api.mount("/static", StaticFiles(directory="app/static"), name="static")

    def get_db() -> sqlite3.Connection:
        return api.state.db

    def current_username(authorization: str | None = Header(default=None)) -> str:
        token = _extract_bearer_token(authorization)
        try:
            return username_from_token(token)
        except AuthenticationError as exc:
            raise HTTPException(status_code=401, detail=str(exc)) from exc

    def products_context(
        username: str,
        db: sqlite3.Connection,
        error: str = "",
    ) -> dict[str, object]:
        return {
            "username": username,
            "products": list_products(db),
            "error": error,
            "provider_health": _provider_health_view_model(),
        }

    DbConnection = Annotated[sqlite3.Connection, Depends(get_db)]
    CurrentUsername = Annotated[str, Depends(current_username)]

    @api.get("/health")
    def health() -> dict[str, str]:
        return {"status": "ok"}

    @api.post("/api/login", response_model=LoginResponse)
    def login(payload: LoginRequest, db: DbConnection) -> LoginResponse:
        try:
            user = authenticate_user(db, payload.username, payload.password)
        except AuthenticationError as exc:
            raise HTTPException(status_code=401, detail=str(exc)) from exc
        return LoginResponse(access_token=token_for_username(user["username"]))

    @api.get("/api/products")
    def products(db: DbConnection) -> list[dict[str, object]]:
        return list_products(db)

    @api.get("/api/products/{product_id}")
    def product_detail(
        product_id: int,
        db: DbConnection,
    ) -> dict[str, object]:
        try:
            return get_product(db, product_id)
        except ProductNotFoundError as exc:
            raise HTTPException(status_code=404, detail=str(exc)) from exc

    @api.post("/api/orders", status_code=201)
    def order_create(
        payload: OrderRequest,
        username: CurrentUsername,
        db: DbConnection,
    ) -> dict[str, object]:
        try:
            return create_order(db, username, payload.product_id, payload.quantity)
        except ProductNotFoundError as exc:
            raise HTTPException(status_code=404, detail=str(exc)) from exc
        except InsufficientStockError as exc:
            raise HTTPException(status_code=409, detail=str(exc)) from exc

    @api.post("/api/diagnosis", response_model=DiagnosisResponse)
    def diagnosis_create(payload: DiagnosisRequest) -> DiagnosisResponse:
        artifact = FailureArtifact(
            nodeid=payload.nodeid,
            failed_at=payload.failed_at,
            phase=payload.phase,
            duration_seconds=payload.duration_seconds,
            longrepr=payload.longrepr,
            keywords=payload.keywords,
        )
        prompt = build_diagnosis_prompt([artifact])
        report = diagnose_with_ai(prompt)
        return DiagnosisResponse(artifact_count=1, report_markdown=report)

    @api.get("/api/ai-providers")
    def ai_providers() -> dict[str, dict[str, dict[str, object]]]:
        return {"providers": supported_provider_specs()}

    @api.get("/api/provider-health", response_model=ProviderHealthResponse)
    def provider_health() -> ProviderHealthResponse:
        return ProviderHealthResponse(**check_provider_health())

    @api.get("/", response_class=HTMLResponse)
    def dashboard_page(request: Request, db: DbConnection) -> HTMLResponse:
        return templates.TemplateResponse(
            request,
            "dashboard.html",
            _dashboard_context(db),
        )

    @api.post("/diagnose", response_model=None)
    async def web_diagnosis(request: Request) -> RedirectResponse:
        form = await request.form()
        nodeid = str(form.get("nodeid", "")).strip() or "manual/input::failure"
        phase = str(form.get("phase", "")).strip() or "call"
        longrepr = str(form.get("longrepr", "")).strip()
        keywords = _parse_keywords(str(form.get("keywords", "")))
        if not longrepr:
            longrepr = "No failure log was provided."

        artifact = FailureArtifact(
            nodeid=nodeid,
            failed_at=datetime.now(UTC).isoformat(),
            phase=phase,
            duration_seconds=0,
            longrepr=longrepr,
            keywords=keywords,
        )
        prompt = build_diagnosis_prompt([artifact])
        report = diagnose_with_ai(prompt)
        write_markdown_report(_web_report_path(), "中文 AI 诊断报告", report)
        return RedirectResponse("/diagnosis-report", status_code=303)

    @api.get("/diagnosis-report", response_class=HTMLResponse)
    def diagnosis_report_page(request: Request) -> HTMLResponse:
        return templates.TemplateResponse(
            request,
            "diagnosis_report.html",
            {"latest_report": _latest_report_view_model()},
        )

    @api.get("/interview-review", response_class=HTMLResponse)
    def interview_review_page(request: Request, db: DbConnection) -> HTMLResponse:
        return templates.TemplateResponse(
            request,
            "interview_review.html",
            _interview_review_context(db),
        )

    @api.get("/login", response_class=HTMLResponse)
    def login_page(request: Request) -> HTMLResponse:
        return templates.TemplateResponse(request, "login.html", {"error": ""})

    @api.post("/login", response_model=None)
    async def web_login(
        request: Request,
        db: DbConnection,
    ) -> HTMLResponse | RedirectResponse:
        form = await request.form()
        username = str(form.get("username", ""))
        password = str(form.get("password", ""))
        try:
            authenticate_user(db, username, password)
        except AuthenticationError:
            return templates.TemplateResponse(
                request,
                "login.html",
                {"error": "用户名或密码错误"},
                status_code=401,
            )
        response = RedirectResponse("/products", status_code=303)
        response.set_cookie("qa_user", username, httponly=True)
        return response

    @api.get("/products", response_class=HTMLResponse, response_model=None)
    def products_page(
        request: Request,
        db: DbConnection,
    ) -> HTMLResponse | RedirectResponse:
        username = request.cookies.get("qa_user")
        if not username:
            return RedirectResponse("/login", status_code=303)
        return templates.TemplateResponse(
            request,
            "products.html",
            products_context(username, db),
        )

    @api.post("/orders", response_model=None)
    async def web_order(
        request: Request,
        db: DbConnection,
    ) -> HTMLResponse | RedirectResponse:
        username = request.cookies.get("qa_user")
        if not username:
            return RedirectResponse("/login", status_code=303)
        form = await request.form()
        product_id = int(str(form.get("product_id", "0")))
        quantity = int(str(form.get("quantity", "1")))
        try:
            order = create_order(db, username, product_id, quantity)
        except ProductNotFoundError:
            return templates.TemplateResponse(
                request,
                "products.html",
                products_context(username, db, "商品不存在。"),
                status_code=409,
            )
        except InsufficientStockError:
            return templates.TemplateResponse(
                request,
                "products.html",
                products_context(username, db, "库存不足，无法创建订单。"),
                status_code=409,
            )
        return templates.TemplateResponse(
            request,
            "order_success.html",
            {"username": username, "order": order},
        )

    return api


app = create_app()
