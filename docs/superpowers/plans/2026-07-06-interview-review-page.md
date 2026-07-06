# Interview Review Page Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add an interviewer-facing review page that explains the project's QA value without requiring the reviewer to inspect README files or raw reports.

**Architecture:** Keep the existing FastAPI/Jinja structure. Reuse the dashboard's report parsing and curated failure examples, add a focused `/interview-review` route, and expose a top-level navigation link from the dashboard and report page.

**Tech Stack:** FastAPI, Jinja2 templates, pytest API page tests, Playwright E2E tests, existing CSS.

---

### Task 1: Page Contract Tests

**Files:**
- Modify: `tests/api/test_web_pages.py`
- Modify: `tests/e2e/test_shop_flow.py`

- [ ] **Step 1: Write API page tests**

Add tests that call `GET /interview-review` and assert the page contains:

```python
assert "面试官审阅模式" in response.text
assert "我会怎么审这个项目" in response.text
assert "测试证据链" in response.text
assert "API / Service / E2E / CI" in response.text
assert "Failure Mode Matrix" in response.text
assert "安全边界" in response.text
assert "3 分钟讲解顺序" in response.text
assert "API Docs" not in response.text
assert "reports/latest" not in response.text
```

- [ ] **Step 2: Write E2E navigation test**

Extend the main E2E flow so the dashboard exposes a link named `面试官审阅模式`, and the page renders the heading `面试官审阅模式`.

- [ ] **Step 3: Verify tests fail**

Run:

```powershell
pytest tests\api\test_web_pages.py::test_interview_review_page_explains_project_value tests\e2e\test_shop_flow.py -q --browser chromium
```

Expected: the new API test fails with `404` until the route exists.

### Task 2: FastAPI Route And Template

**Files:**
- Modify: `app/main.py`
- Create: `app/templates/interview_review.html`
- Modify: `app/templates/dashboard.html`
- Modify: `app/templates/diagnosis_report.html`

- [ ] **Step 1: Add review page data**

Create simple constants in `app/main.py` for interviewer review cards:

```python
INTERVIEW_SCORECARDS = [
    {"title": "测试设计", "body": "API / Service / E2E / CI 分层明确。"},
    {"title": "失败证据", "body": "失败会沉淀 pytest report、failure JSON 和可读诊断。"},
    {"title": "AI 边界", "body": "AI 输出候选根因 / 诊断假设，不替代测试门禁。"},
    {"title": "安全边界", "body": "页面不展示密钥、内部地址、模型名或 key source。"},
]
```

- [ ] **Step 2: Add `/interview-review` route**

Use existing helpers to pass failure evidence cards and latest report preview into the template.

- [ ] **Step 3: Create Jinja template**

The template must show:
- Project review summary
- What an interviewer should inspect
- Testing evidence chain
- Failure mode examples
- AI report reading guide
- 3-minute talk track
- Links back to Dashboard, Demo Shop, and AI Report

- [ ] **Step 4: Add navigation**

Add `Interview Review` / `面试官审阅模式` links to dashboard and report pages.

- [ ] **Step 5: Verify tests pass**

Run:

```powershell
pytest tests\api\test_web_pages.py tests\e2e\test_shop_flow.py -q --browser chromium
```

Expected: all selected tests pass.

### Task 3: Styling And Documentation

**Files:**
- Modify: `app/static/styles.css`
- Modify: `README.md`
- Modify: `docs/interview-demo-script-zh.md`
- Modify: `tests/unit/test_docs.py`

- [ ] **Step 1: Add compact review-page CSS**

Reuse existing card/grid visual language. Keep the page dense and review-oriented, not a marketing landing page.

- [ ] **Step 2: Update README and Chinese script**

Mention `/interview-review` as the preferred interviewer entry after Dashboard.

- [ ] **Step 3: Add docs tests**

Assert README and Chinese script mention `面试官审阅模式` and `/interview-review`.

- [ ] **Step 4: Verify full project**

Run:

```powershell
.\scripts\verify.ps1
```

Expected: Ruff, pytest/Playwright, and demo AI diagnosis generation pass.
