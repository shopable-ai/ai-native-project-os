# AI 项目推进操作系统

> 目标框架版本等级：`standard`。
>
> 当前成熟度：设计待复核；实现状态与验证状态见 `project-os.yaml.maturity`。
>
> 当前总体评分：`not_evaluated`。设计目标分：`95.93`，只描述目标方案，不是当前得分。

AI 项目推进操作系统用于把模糊需求转化为可研究、可决策、可执行、可验证、可恢复和可演进的项目。它不是某个业务项目，也不是某个智能体框架的包装层。

## 当前决策

- 目标框架版本等级采用 `standard`，最高等级 `enterprise` 本阶段不建设。
- 项目治理由 `lite|standard` 基础配置叠加 `multi_agent|production` 能力，不与框架等级混用。
- 采用自研薄内核，外部能力通过适配器接入。
- 人类提前批准和维护 Markdown 规则；独立 AI 负责日常内容、Evidence、风险和质量审核；人工不逐条审核普通业务输出。
- 审核失败自动进入有界改写、重新审核、规则缺口或安全阻断；高风险动作授权与内容审核互不替代。
- 通用方法和协议保存在本仓库。
- 具体业务能力保存在业务系统仓库。
- 项目事实、Run、Evidence 和交付物默认保存在 L2 自身的约定目录。
- `projects/{project_id}/` 仅在多实例隔离有证据时启用，作为可选 L3 namespace；L1 不预建实例目录。
- 外部开源能力通过适配器接入，不成为内核语义。
- 研究材料不是事实源；只有通过门禁后才能升格为事实、决策、契约或正式资产。

## 第一次阅读

1. [人类总览与四条主线](docs/architecture/AI_PROJECT_OS_OVERVIEW.md)
2. [项目交付工作流](docs/workflows/PROJECT_DELIVERY_WORKFLOW.md)
3. [R0 与 S0—S7 阶段退出门禁](docs/workflows/STAGE_EXIT_GATES.md)
4. [术语权威](docs/governance/TERMINOLOGY.md)
5. [核心架构](docs/architecture/AI_PROJECT_OS_CORE.md)
6. [框架版本等级](docs/architecture/FRAMEWORK_EDITION_MODEL.md)
7. [仓库与层级契约](docs/architecture/REPOSITORY_AND_LAYER_CONTRACT.md)
8. [受控对象模型](docs/governance/CONTROLLED_OBJECT_MODEL.md)
9. [L2 端到端推进 SOP](docs/workflows/L2_PROGRESSION.md)
10. [项目类型与治理配置路由](docs/workflows/PROJECT_TYPE_AND_GOVERNANCE_ROUTING.md)
11. [Run、Evidence、验收裁决](docs/governance/RUN_EVIDENCE_ACCEPTANCE.md)
12. [门禁、唯一证据枚举与评分](docs/governance/GATES_PROOF_SCORING.md)

## 权威文件

| 问题 | 权威文件 |
|---|---|
| 人如何理解整套系统和四条主线 | `docs/architecture/AI_PROJECT_OS_OVERVIEW.md` |
| 项目从需求或存量恢复怎样推进到声明 | `docs/workflows/PROJECT_DELIVERY_WORKFLOW.md` |
| R0、S0—S7 每阶段怎样退出、失效和重开 | `docs/workflows/STAGE_EXIT_GATES.md` |
| 中文术语和稳定 term-id | `docs/governance/TERMINOLOGY.md` |
| 核心原语和架构平面 | `docs/architecture/AI_PROJECT_OS_CORE.md` |
| 四级框架版本范围 | `docs/architecture/FRAMEWORK_EDITION_MODEL.md` |
| L1/L2/L3 仓库、兼容和资产升格 | `docs/architecture/REPOSITORY_AND_LAYER_CONTRACT.md` |
| R0、S0—S7 怎么推进 | `docs/workflows/PROJECT_LIFECYCLE.md` |
| L2 接入后如何端到端推进和失败重开 | `docs/workflows/L2_PROGRESSION.md` |
| 项目类型和治理配置怎么选择 | `docs/workflows/PROJECT_TYPE_AND_GOVERNANCE_ROUTING.md` |
| 项目治理的机器路由条件 | `policies/project-governance-routing.yaml` |
| 人工治理 Markdown 规则集契约 | `policies/governance-rule-set-contract.yaml` |
| 独立 AI 自动审核裁决契约 | `policies/ai-review-verdict-contract.yaml` |
| 规则缺口异步治理契约 | `policies/rule-gap-case-contract.yaml` |
| 架构师具体做什么 | `docs/workflows/ARCHITECT_WORKFLOWS.md` |
| 文件之间如何追溯 | `docs/governance/ARTIFACTS_AND_TRACEABILITY.md` |
| 受控对象字段、类型与固定主链 | `docs/governance/CONTROLLED_OBJECT_MODEL.md` |
| 状态迁移与失效传播 | `docs/governance/STATE_TRANSITIONS_AND_INVALIDATION.md` |
| AI 执行节点与上下文治理 | `docs/architecture/AI_NATIVE_EXECUTION_MODEL.md` |
| 权限、外部副作用和项目隔离 | `docs/governance/AUTHORIZATION_SIDE_EFFECTS_AND_ISOLATION.md` |
| Run、Evidence、裁决和声明 | `docs/governance/RUN_EVIDENCE_ACCEPTANCE.md` |
| 唯一证据枚举与可重算评分 | `docs/governance/GATES_PROOF_SCORING.md` |
| 陌生领域和技术怎么研究 | `docs/research/RESEARCH_WORKFLOW.md` |
| 当前有哪些待研究选型 | `research/registry.yaml` |

主题级权威路径以 `project-os.yaml` 的 `authority` 为准。同一结论只在一个权威文件维护，其他文件只做入口或解释。

## 当前不是

- 不是运行中的工作流平台。
- 不是完整企业项目管理系统。
- 不是所有项目都必须启用的最大框架。
- 不是 LangGraph、Temporal、Spec Kit、OpenSpec 或 BMAD 的替代实现。
- 不是用文档数量证明项目完成的治理系统。

## 当前阶段

当前正在建立从人类入口到静态契约、模板、检查器和 fixture 的操作骨架。推进顺序保存在受控实施计划中；本节不维护第二份完成清单。

| 观察面 | 当前事实 | 声明上限 |
|---|---|---|
| 当前总体评分 | `not_evaluated` | 没有完整可重算评分输入，不给当前数字 |
| 设计目标分 | `95.93` | 只表示批准目标形态，不是当前证据分 |
| 静态实现证据 | 已存在部分文档、契约测试与检查器输出，但未形成当前总评分 | 只能陈述具体文件与新鲜命令结果 |
| fixture 证明 | `not_evaluated` | 不得外推成本地真实运行 |
| 本地真实证明 | `not_evaluated` | 不得外推为只读真实或生产证明 |
| 只读真实证明 | `not_evaluated` | 不得外推为生产写入或业务效果 |
| 生产证明 | `not_evaluated` | 不得声明生产就绪或业务成功 |

成熟度字段不能证明运行能力。`maturity`、静态测试、fixture、本地真实、只读真实和生产证明必须分开记录；跨项目隔离验证和第二个异构 L2 验证仍是未满足硬门禁。
