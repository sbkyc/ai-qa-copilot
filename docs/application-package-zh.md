# 中文投递材料包

这份材料用于投递自动化测试、测试开发、AI QA、Python 后端和 AI 应用开发相关岗位。它把项目经历、3 分钟讲稿和高频问答压缩成可直接复制或背诵的版本。

## 简历项目经历 4 条 bullet

**AI 自动化测试与缺陷诊断平台 | Python / FastAPI / pytest / Playwright / GitHub Actions / DeepSeek**

- 基于 FastAPI 构建 AI QA 诊断工作台，支持粘贴 pytest / Playwright / API 失败日志并生成中文 AI 诊断报告；Demo Shop 作为 API 与浏览器 E2E 自动化测试的被测系统。
- 使用 pytest 设计服务层与接口自动化测试，结合 fixture 隔离测试数据库，并通过 hook 收集 nodeid、phase、longrepr、keywords 等结构化 failure JSON。
- 使用 Playwright Python 覆盖真实浏览器登录和下单流程，配合 CI 上传 pytest HTML report、failure artifacts、AI diagnosis 和 dry-run PR comment preview。
- 设计 OpenAI / DeepSeek / OpenAI-compatible provider adapter 与 Provider Status UI，支持 provider readiness 检查，并默认脱敏 API key、base URL、model 和 key source。

## 30 秒项目介绍

这是一个 AI 自动化测试与缺陷诊断平台。首页是可直接使用的 AI QA 诊断工作台：粘贴 pytest、Playwright 或 API 失败日志后，可以生成中文 AI diagnosis 和 Failure Mode Matrix，并在“最近诊断”里保留多次报告。底层用 FastAPI Demo Shop、pytest、Playwright、failure JSON、CI artifacts 和 provider adapter 支撑完整工程闭环。

## 3 分钟演示讲稿

1. 打开 AI QA 诊断工作台：`http://127.0.0.1:8000`。
2. 粘贴或保留默认失败日志，点击“生成中文诊断报告”。
3. 打开 `/diagnosis-report`，讲 Failure Mode Matrix 如何输出证据、分类、候选根因 / 诊断假设和下一步建议。
4. 讲五个能力：端到端 QA 自动化、失败证据链、AI 辅助诊断、Provider 安全边界、CI 作品集产物。
5. 进入 Demo Shop，用 `alice / password123` 登录并创建订单，说明它是被测系统，不是项目本体。
6. 解释如果这里失败，pytest / Playwright 会把失败上下文保存成 failure JSON。
7. 打开 `reports/examples/sample-ai-diagnosis.md` 或 `qa-reports`，说明 CI artifact 证据链。
8. 说明 `pr-comment.md` 是 dry-run PR comment preview，不调用 GitHub PR/Issues API，也不会自动评论 PR。
9. 讲 Provider Status：页面能显示 DeepSeek / OpenAI provider 是否 ready，但不会展示 API key、base URL、model 或 key source。
10. 收尾：这个项目不是电商系统，而是用真实业务流程展示自动化测试、失败诊断、AI provider 安全和 CI artifact 的工程闭环。

## 面试高频问答

**Q：买完商品之后然后呢？**

A：现在首页诊断工作台才是主要入口。买商品不是项目目标，它是被测业务路径。正常下单证明 E2E 主流程可用；如果登录、商品加载、库存或下单失败，项目会把失败转成 failure JSON、AI diagnosis、Failure Mode Matrix 和 PR comment preview。

**Q：AI 在这里做了什么？**

A：AI 不决定测试是否通过。pytest 和 Playwright 才是质量门禁。AI 负责把失败上下文整理成 review-friendly 的诊断材料，比如证据、分类、候选根因、复现步骤和下一步建议。

**Q：为什么要做 Provider Status？**

A：AI 应用需要可观测性，也需要安全边界。Provider Status 让用户知道 DeepSeek / OpenAI 是否配置 ready，但不暴露 API key、base URL、model 或 key source，适合 public portfolio 展示。

**Q：这个项目会不会过度包装？**

A：不会。首页支持真实粘贴失败日志，AI 输出叫候选根因 / 诊断假设，不声称确认真实根因；PR comment 是 dry-run preview，不调用 GitHub PR/Issues API，也不会自动发评论。

**Q：项目体现了哪些测试开发能力？**

A：体现了 pytest fixture、服务层测试、API 状态码和响应体验证、Playwright 浏览器 E2E、CI artifact、失败证据收集、报告生成和测试失败诊断链路。

**Q：项目体现了哪些 AI 应用开发能力？**

A：体现了 provider adapter、DeepSeek / OpenAI-compatible 接入、prompt 输入组织、fallback report、Provider health validation、敏感配置脱敏和 AI 输出结构化。

## 投递前检查清单

- GitHub README 首屏能说明项目价值。
- 本地 `http://127.0.0.1:8000` 打开后能看到中文 AI QA 诊断工作台。
- Demo Shop 登录和下单流程可跑通。
- `reports/examples/sample-ai-diagnosis.md` 可用于稳定展示 Failure Mode Matrix。
- `qa-reports` / `demo-qa-reports` 的边界能讲清楚。
- 简历只放 2 到 3 个项目，AI QA Copilot 放第一位。
- 不在简历或 README 中放真实 API key、手机号截图、内部日志或公司专有数据。

## 项目级别定位

这个项目适合作为自动化测试 / 测试开发求职的主项目，也能作为转向 AI 应用开发的桥梁项目。它不是生产级平台，但已经具备完整 portfolio 项目的关键要素：真实被测系统、自动化测试、失败证据、AI 诊断、provider 安全、CI artifact、中文演示材料和可复现的本地展示路径。
