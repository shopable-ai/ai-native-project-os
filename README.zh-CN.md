# AI 项目推进操作系统

> 状态：标准版设计基线。当前只包含架构、工作流、治理和研究设计，不包含运行代码。

AI 项目推进操作系统用于把模糊需求转化为可研究、可决策、可执行、可验证、可恢复和可演进的项目。它不是某个业务项目，也不是某个智能体框架的包装层。

## 当前决策

- 采用“标准版 + 自研薄内核”。
- 通用方法和协议保存在本仓库。
- 具体业务能力保存在业务系统仓库。
- 具体项目事实、运行记录和交付物保存在 `projects/{project_id}/`。
- 外部开源能力通过适配器接入，不成为内核语义。
- 研究材料不是事实源；只有通过门禁后才能升格为事实、决策、契约或正式资产。

## 第一次阅读

1. [核心架构](docs/architecture/AI_PROJECT_OS_CORE.md)
2. [项目生命周期](docs/workflows/PROJECT_LIFECYCLE.md)
3. [架构师工作流](docs/workflows/ARCHITECT_WORKFLOWS.md)
4. [产物与追溯模型](docs/governance/ARTIFACTS_AND_TRACEABILITY.md)
5. [门禁、证据与评分](docs/governance/GATES_PROOF_SCORING.md)
6. [研究工作流](docs/research/RESEARCH_WORKFLOW.md)
7. [开源研究登记表](research/registry.yaml)

## 权威文件

| 问题 | 权威文件 |
|---|---|
| 系统边界和分层 | `docs/architecture/AI_PROJECT_OS_CORE.md` |
| R0、S0—S7 怎么推进 | `docs/workflows/PROJECT_LIFECYCLE.md` |
| 架构师具体做什么 | `docs/workflows/ARCHITECT_WORKFLOWS.md` |
| 文件之间如何追溯 | `docs/governance/ARTIFACTS_AND_TRACEABILITY.md` |
| 什么情况下允许声称完成 | `docs/governance/GATES_PROOF_SCORING.md` |
| 陌生领域和技术怎么研究 | `docs/research/RESEARCH_WORKFLOW.md` |
| 当前有哪些待研究选型 | `research/registry.yaml` |

## 当前不是

- 不是运行中的工作流平台。
- 不是完整企业项目管理系统。
- 不是所有项目都必须启用的最大框架。
- 不是 LangGraph、Temporal、Spec Kit、OpenSpec 或 BMAD 的替代实现。
- 不是用文档数量证明项目完成的治理系统。

## 当前阶段

```text
设计方向已确认
→ 关键设计文件已建立
→ 等待用户复核
→ 编写实施计划
→ 实现最小检查器和标准版骨架
→ 使用当前业务项目完成存量架构恢复试点
```
