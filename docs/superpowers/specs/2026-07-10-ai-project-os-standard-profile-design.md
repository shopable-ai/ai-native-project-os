# AI Project OS 标准版设计确认记录

> 状态：已被替代，禁止作为当前分类权威。
>
> 替代文件：`2026-07-10-framework-edition-and-project-governance-design.md`
>
> 保留原因：本记录证明早期“标准版—最大企业版”与“多智能体版—生产版”曾被混写，后续不得静默改写历史。

## 用户确认的方向

- 当前最多建设到标准版，暂不建设最大企业版。
- 采用 AI Project OS 自研薄内核。
- 为避免聊天上下文膨胀，将关键架构和工作流保存到独立新目录。
- 新目录与当前业务仓库并列，方便独立修改、审查和版本化。

## 已确认设计

- 架构权威源：`docs/architecture/AI_PROJECT_OS_CORE.md`
- 生命周期权威源：`docs/workflows/PROJECT_LIFECYCLE.md`
- 架构师职责权威源：`docs/workflows/ARCHITECT_WORKFLOWS.md`
- 追溯权威源：`docs/governance/ARTIFACTS_AND_TRACEABILITY.md`
- 证据与评分权威源：`docs/governance/GATES_PROOF_SCORING.md`
- 研究方法权威源：`docs/research/RESEARCH_WORKFLOW.md`
- 待研究选型：`research/registry.yaml`

## 本轮明确不做

- 不实现运行代码。
- 不安装任何第三方依赖。
- 不迁移当前业务仓库文件。
- 不建设多智能体版或生产版。
- 不把设计评分描述成实现或生产评分。

## 下一阶段入口

用户复核本设计基线后，下一阶段只能是编写实施计划。实施计划的第一目标是最小追溯检查器和标准版目录契约，而不是完整工作流平台。

## 后续替代说明

本记录没有区分框架版本等级、项目基础治理配置和可叠加运行能力，因此只能作为决策演进证据，不能继续指导机器字段或项目路由。
