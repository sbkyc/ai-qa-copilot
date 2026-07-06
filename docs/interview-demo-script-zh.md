# 中文面试演示脚本

这份脚本用于 3 到 5 分钟现场演示。目标不是把每个文件都讲完，而是让面试官快速理解：这个项目不是普通电商 Demo，而是一个围绕自动化测试失败分析的 AI QA Copilot。

## 一句话介绍

这是一个 AI 自动化测试与缺陷诊断平台。首页就是可直接使用的 AI QA 诊断工作台：面试官可以粘贴 pytest、Playwright 或 API 失败日志，生成中文 AI 诊断报告。底层仍然用 FastAPI、pytest、Playwright、failure JSON、CI artifacts 和 provider adapter 支撑完整工程闭环。

## 3 分钟演示路线

1. 打开本地 AI QA 诊断工作台：`http://127.0.0.1:8000`
2. 保留左侧默认失败日志，或粘贴一段 pytest / Playwright / API 失败输出。
3. 点击“生成中文诊断报告”。
4. 打开中文 AI 报告，重点讲 Failure Mode Matrix：分类、证据、候选根因 / 诊断假设和下一步建议。
5. 指出 AI 诊断模式卡片：页面能显示当前是本地 fallback 还是实时 AI，但不展示密钥或内部配置。
6. 如果面试官想看被测系统，再进入 Demo Shop，登录 `alice / password123` 并创建订单。
7. 解释：Demo Shop 只是测试对象，真正产品能力是把失败日志转成可读的诊断报告。

英文压缩版可以讲成：Workbench failure input -> Chinese AI diagnosis report -> Failure Mode Matrix -> optional Demo Shop evidence。

## AI QA 诊断工作台怎么讲

可以这样说：

> 这个首页不是营销页，也不是单纯说明文档。它是一个可以直接使用的 AI QA 诊断工作台。面试官可以把测试失败日志粘进去，点击生成中文诊断报告，然后看到 Failure Mode Matrix、证据、候选根因和下一步建议。

## 面试官审阅模式怎么讲

可以这样说：

> 如果面试官时间很短，我会先用首页工作台生成一份报告，再打开 `/interview-review`。这个页面按面试官视角组织：先看我测了什么，再看测试证据链，然后看 Failure Mode Matrix 和安全边界。

这个页面要强调：

- “我会怎么审这个项目”回答面试官的评估标准。
- “测试证据链”说明 API / Service / E2E / CI 如何串起来。
- “3 分钟讲解顺序”就是现场演示路线。
- “安全边界”说明 AI 报告和 provider 状态不会泄漏敏感配置。

如果面试官问“这些数据是真的吗”，可以回答：

> 首页表单可以使用真实粘贴的失败日志；如果没有实时 AI key，系统会生成 fallback 报告。报告预览和 CI demo 也会使用 curated examples，用来稳定展示诊断结构，不伪装成当前 CI 真实失败。

## Demo Shop 下单怎么讲

可以这样说：

> 这里的商品下单不是为了做电商业务，而是作为被测系统。自动化测试需要一个真实可运行的业务流程，所以我设计了登录、商品列表、创建订单和库存异常这些场景。正常下单说明系统主路径可用；如果这里失败，pytest / Playwright 会把失败上下文收集成结构化 artifact。

下单成功页要强调：

- 订单成功说明真实 E2E 路径跑通。
- 下单成功不是终点。
- 如果失败，下一步看测试报告、failure JSON、AI diagnosis 和 PR comment preview。

## Failure Mode Matrix 怎么讲

可以这样说：

> 普通测试报告只告诉我“哪个用例失败”。Failure Mode Matrix 会进一步把失败归类，比如 Product/API behavior、API contract、UI/E2E behavior、Flaky/timing、Environment/setup。这样团队可以更快判断责任边界：是产品接口问题、测试契约漂移、浏览器状态问题、偶发时序问题，还是测试环境 setup 问题。

注意用词：

- 说“候选根因”或“诊断假设”。
- 不说“AI 自动确认真实根因”。
- 不说“AI 自动修复 bug”。

## Provider Status 怎么讲

可以这样说：

> AI provider 可以配置 DeepSeek、OpenAI 或 OpenAI-compatible gateway。因为这是 public portfolio，页面需要能看出 provider 是否 ready，但不能泄漏密钥和内部配置。所以 Provider Status 只展示 provider、API style、API key 是否 configured、缺少哪些配置；不会展示 API key、base URL、model 或 key source。

如果页面显示 DeepSeek 已就绪，可以补一句：

> 这说明本地 provider 配置是可用的，但页面仍然不会显示真实 API key。

## CI artifacts 怎么讲

可以这样说：

> CI 不只是跑绿灯。这个项目会把测试报告、失败 JSON、AI diagnosis 和 dry-run PR comment preview 都上传到 `qa-reports`。这样面试官或 reviewer 能看到从失败发生到诊断摘要的完整证据链。

边界也要主动说清楚：

> `pr-comment.md` 做了 basic redaction，但完整 artifact 可能包含 raw logs、screenshots、traces 或 stack traces。真实公司项目里，公开前必须人工 review artifacts。

## 高频问答

**Q：买完商品之后然后呢？**

A：现在首页诊断工作台才是主要产品入口。买商品只是可选的被测业务场景，用来让 Playwright E2E 覆盖真实登录和下单流程。如果这个流程失败，项目会把失败转成 failure JSON、AI diagnosis、Failure Mode Matrix 和 PR comment preview。

**Q：AI 在项目里到底做了什么？**

A：AI 不负责判断测试是否通过。pytest 和 Playwright 才是质量门禁。AI 负责把失败上下文整理成更容易 review 的诊断材料，包括证据、分类、候选根因和下一步建议。

**Q：这个项目是不是包装过度？**

A：我刻意保留了边界：首页可以输入失败日志，但 AI 输出只叫候选根因 / 诊断假设；PR comment 是 dry-run preview，不调用 GitHub PR/Issues API，也不会自动发评论。Provider Status 也只展示 readiness，不暴露 secret。

**Q：为什么不直接做一个聊天机器人？**

A：聊天机器人容易变成纯 UI demo。我这个项目把 AI 放进自动化测试失败诊断这个具体工程场景里，能同时展示测试开发能力、Python 工程能力、CI 能力和 LLM provider 集成能力。

**Q：如果 AI 服务不可用怎么办？**

A：项目会生成 fallback report，CI 仍然保留 pytest report 和 failure artifacts。AI 是增强诊断体验，不会阻断自动化测试主流程。

## 结束语

可以这样收尾：

> 这个项目的重点不是电商功能本身，而是一个可以直接使用的 AI QA 诊断工作台。它把测试失败日志、自动化测试、失败证据、AI 诊断、provider 安全边界和 CI artifact 串成了完整闭环。这也是我从自动化测试转向 AI 应用开发时最想展示的能力。
