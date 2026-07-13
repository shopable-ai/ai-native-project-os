# AI 项目推进操作系统

> 目标框架版本等级：`standard`。
>
> 当前成熟度：设计已批准、实现部分完成；全局真实验证仍未完成，精确状态见 `project-os.yaml.maturity`。
>
> 当前总体评分：`not_evaluated`。设计目标分：`95.93`，只描述目标方案，不是当前得分；当前评分边界见 [current-score-status](reviews/current-score-status.yaml)。

讨论中出现的 `86.4`、`96.4` 和 `97.6` 是不同方案切片的专家估算，均为非官方、未独立复算的设计参考；它们不替代当前总体评分，也不解除任何硬门禁。

AI 项目推进操作系统用于把模糊需求转化为可研究、可决策、可执行、可验证、可恢复和可演进的项目。它不是某个业务项目，也不是某个智能体框架的包装层。

## 当前决策

- 目标框架版本等级采用 `standard`，最高等级 `enterprise` 本阶段不建设。
- 项目治理由 `lite|standard` 基础配置叠加 `multi_agent|production` 能力，不与框架等级混用。
- 采用自研薄内核，外部能力通过适配器接入。
- 人类治理目标、责任和不可自动放宽的边界；Markdown 规则与完整审核策略包经测试认证后，独立 AI 负责日常内容、Evidence、风险和质量审核；人工不逐条审核普通业务输出。
- 审核失败自动进入有界改写、重新审核、规则缺口或安全阻断；高风险动作授权与内容审核互不替代。
- 通用方法和协议保存在本仓库。
- 具体业务能力保存在业务系统仓库。
- 项目事实、Run、Evidence 和交付物默认保存在 L2 自身的约定目录。
- `projects/{project_id}/` 仅在多实例隔离有证据时启用，作为可选 L3 namespace；L1 不预建实例目录。
- 外部开源能力通过适配器接入，不成为内核语义。
- 研究材料不是事实源；只有通过门禁后才能升格为事实、决策、契约或正式资产。
- AI 可以起草并自检功能需求；低风险对象只有在审核策略认证和激活 Policy 同时允许时才能自动通过决策门，高风险目标/范围/责任变化仍需人工确认；未通过合法决策门的需求不能进入 active Spec。

## 第一次阅读

1. [人类总览与四条主线](docs/architecture/AI_PROJECT_OS_OVERVIEW.md)
2. [项目交付工作流](docs/workflows/PROJECT_DELIVERY_WORKFLOW.md)
3. [人机协作需求设计工作流](docs/workflows/REQUIREMENT_DESIGN_WORKFLOW.md)
4. [R0 与 S0—S7 阶段退出门禁](docs/workflows/STAGE_EXIT_GATES.md)
5. [术语权威](docs/governance/TERMINOLOGY.md)
6. [核心架构](docs/architecture/AI_PROJECT_OS_CORE.md)
7. [框架版本等级](docs/architecture/FRAMEWORK_EDITION_MODEL.md)
8. [仓库与层级契约](docs/architecture/REPOSITORY_AND_LAYER_CONTRACT.md)
9. [受控对象模型](docs/governance/CONTROLLED_OBJECT_MODEL.md)
10. [L2 端到端推进 SOP](docs/workflows/L2_PROGRESSION.md)
11. [项目类型与治理配置路由](docs/workflows/PROJECT_TYPE_AND_GOVERNANCE_ROUTING.md)
12. [Run、Evidence、验收裁决](docs/governance/RUN_EVIDENCE_ACCEPTANCE.md)
13. [门禁、唯一证据枚举与评分](docs/governance/GATES_PROOF_SCORING.md)
14. [审核策略认证与条件式决策门](docs/governance/REVIEW_POLICY_CERTIFICATION.md)

## 模板入口

| 现在要解决的问题 | 模板入口 |
|---|---|
| 选择业务链、Spec、I/O、Workflow、Skill 或可选 L3 实例模板 | [模板问题导航](templates/README.md) |
| 在 Spec 前审查意图、功能需求和批准基线 | [标准 L2 需求设计包](templates/standard-project/requirements/README.md) |
| 在自动审核或低风险自动决策前固定策略包、测试集与激活边界 | [审核策略认证模板](templates/standard-project/governance/review-certification/审核策略包说明.md) |
| 接入新建型 L2 系统 | [标准版 L2 项目模板](templates/standard-project/README.md) |
| 恢复存量 L2 系统 | [Brownfield R0 模板](templates/brownfield-project/README.md) |

模板是结构起点，不代表实现或运行证明；L2 默认直接落在自身仓库根目录，只有多实例隔离证据成立时才启用 `projects/{project_id}/`。

## 权威文件

| 问题 | 权威文件 |
|---|---|
| 人如何理解整套系统和四条主线 | `docs/architecture/AI_PROJECT_OS_OVERVIEW.md` |
| 项目从需求或存量恢复怎样推进到声明 | `docs/workflows/PROJECT_DELIVERY_WORKFLOW.md` |
| 人和受控 AI 如何校验意图、审查功能需求并冻结需求基线 | `docs/workflows/REQUIREMENT_DESIGN_WORKFLOW.md` |
| R0、S0—S7 每阶段怎样退出、失效和重开 | `docs/workflows/STAGE_EXIT_GATES.md` |
| 中文术语和稳定 term-id | `docs/governance/TERMINOLOGY.md` |
| 核心原语和架构平面 | `docs/architecture/AI_PROJECT_OS_CORE.md` |
| 四级框架版本范围 | `docs/architecture/FRAMEWORK_EDITION_MODEL.md` |
| L1/L2/L3 仓库、兼容和资产升格 | `docs/architecture/REPOSITORY_AND_LAYER_CONTRACT.md` |
| R0、S0—S7 怎么推进 | `docs/workflows/PROJECT_LIFECYCLE.md` |
| L2 接入后如何端到端推进和失败重开 | `docs/workflows/L2_PROGRESSION.md` |
| 项目类型和治理配置怎么选择 | `docs/workflows/PROJECT_TYPE_AND_GOVERNANCE_ROUTING.md` |
| 项目治理的机器路由条件 | `policies/project-governance-routing.yaml` |
| R0、S0—S7 阶段退出门禁机器契约 | `contracts/governance/stage-exit-gates-contract.yaml` |
| 项目治理路由裁决契约 | `contracts/governance/route-decision-contract.yaml` |
| 控制集合机器契约 | `contracts/governance/control-set-contract.yaml` |
| 受控 Markdown 规则集与条件式批准契约 | `contracts/governance/governance-rule-set-contract.yaml` |
| 审核策略预注册测试集契约 | `contracts/governance/review-policy-test-suite-contract.yaml` |
| 审核策略认证 Verdict 契约 | `contracts/governance/review-policy-certification-contract.yaml` |
| 审核策略激活路由 Policy | `policies/review-policy-activation-routing.yaml` |
| 独立 AI 自动审核裁决契约 | `contracts/governance/ai-review-verdict-contract.yaml` |
| 规则缺口异步治理契约 | `contracts/governance/rule-gap-case-contract.yaml` |
| 叠加能力激活裁决契约 | `contracts/governance/overlay-activation-verdict-contract.yaml` |
| 授权快照机器契约 | `contracts/governance/authorization-snapshot-contract.yaml` |
| 业务验收裁决与完成声明契约 | `contracts/governance/acceptance-verdict-claim-contract.yaml` |
| Run 与 Evidence 最小机器结构契约 | `contracts/governance/run-evidence-contract.yaml` |
| 功能需求卡、项目地图、baseline 与 context 模板契约 | `contracts/artifacts/requirement-design-package-contract.yaml` |
| 架构师具体做什么 | `docs/workflows/ARCHITECT_WORKFLOWS.md` |
| 文件之间如何追溯 | `docs/governance/ARTIFACTS_AND_TRACEABILITY.md` |
| 受控对象字段、类型与固定主链 | `docs/governance/CONTROLLED_OBJECT_MODEL.md` |
| 状态迁移与失效传播 | `docs/governance/STATE_TRANSITIONS_AND_INVALIDATION.md` |
| AI 执行节点与上下文治理 | `docs/architecture/AI_NATIVE_EXECUTION_MODEL.md` |
| 权限、外部副作用和项目隔离 | `docs/governance/AUTHORIZATION_SIDE_EFFECTS_AND_ISOLATION.md` |
| Run、Evidence、裁决和声明 | `docs/governance/RUN_EVIDENCE_ACCEPTANCE.md` |
| 唯一证据枚举与可重算评分 | `docs/governance/GATES_PROOF_SCORING.md` |
| 审核规则、Prompt 和 reviewer 怎样经测试认证后激活 | `docs/governance/REVIEW_POLICY_CERTIFICATION.md` |
| 陌生领域和技术怎么研究 | `docs/research/RESEARCH_WORKFLOW.md` |
| 当前有哪些待研究选型 | `research/registry.yaml` |

主题级权威路径以 `project-os.yaml` 的 `authority` 为准。同一结论只在一个权威文件维护，其他文件只做入口或解释。

## 当前不是

- 不是运行中的工作流平台。
- 不是完整企业项目管理系统。
- 不是所有项目都必须启用的最大框架。
- 不是 LangGraph、Temporal、Spec Kit、OpenSpec 或 BMAD 的替代实现。
- 不是用文档数量证明项目完成的治理系统。

## 现在已经能做什么

匿名 operational-spine fixture 已把 `Requirement → Chain → Spec → Task → Workflow → Skill/Tool → Run → Evidence → Verdict → Claim` 的稳定引用闭合，并以正反例验证 hash、subject、proof、scope 和失败恢复不变量。它还能重放一条受控恢复路径：失败 Run 保持不可改写，S6 契约失败重开 S4，暂停 checkpoint 通过新 Run 恢复，新 Evidence 只绑定新 Run。

这项能力的证明上限是 `fixture_runtime_proven`（受控样例运行已证明），只覆盖匿名 fixture。它不是完整 Workflow engine，也不是 C13 运行时检查器。

人机协作需求设计层已经形成可复制的标准 L2 模板、机器契约和静态正反例：固定 `Source → Fact / Unknown → Requirement → Scenario → Business Chain → Capability → Function → Functional Requirement → Decision Gate → Requirement Baseline → ADR → Spec`，并拒绝意图漂移、无合法路由、AI 自认证、未决 Unknown、baseline 静默改写和 `.prompts/` 权威绕过。该证据范围严格限定为 `human_requirement_design_static_fixture_only`。

审核策略认证静态闭环已经建立：完整策略包覆盖规则、Prompt、I/O Schema、Context、模型、Tool 和权限指纹；测试集在运行前固定类别、预期、指标、阈值和重复次数；C14 使用三条正例验证低风险 `policy_certified`、高风险 `human_signoff` 与 Rule Gap 恢复，并用七条反例阻断类别缺失、重复不足、自认证、hash 漂移、错误自动路由、阈值失败和认证越权授权。它的证明范围仅是 `static_contract_and_synthetic_fixture_only`，可重算快照见 [review-policy-certification-static-evidence](reviews/review-policy-certification-static-evidence.yaml)。

## 仍然不能做什么

- 不能把匿名 fixture 外推为本地真实运行、真实环境只读预检或生产证明。
- 尚未完成真实人工可用性测试，也没有把一个真实 L2 需求迁移到该结构并由其 Spec 消费。
- 尚未执行真实模型多轮评测，也没有“真实 L2 策略消费”Evidence 来证明审核策略认证能推进需求 Baseline；synthetic attempt count 不是模型稳定性 Evidence。
- 项目地图和 context snapshot 目前是模板，不是自动生成器；自动影响模拟也尚未实现。
- 不能声明生产就绪、业务效果成功或通用 95+。
- 跨项目隔离验证和第二个异构 L2 真实验证两项硬门禁仍未满足。
- 独立反方 94 分门禁仍未解除；当前总体评分继续是 `not_evaluated`。

## 当前阶段

方案 B 的操作骨架、人机需求设计层和审核策略认证静态闭环已经落入受控文档、契约、模板、检查器与 fixture；真实模型多轮评测、真实 L2 消费、运行时和生产验证仍待完成。推进边界保存在受控实施计划与证据快照中；本节不维护第二份完成清单。

| 观察面 | 当前事实 | 声明上限 |
|---|---|---|
| 当前总体评分 | `not_evaluated` | 没有完整可重算评分输入，不给当前数字 |
| 设计目标分 | `95.93` | 只表示批准目标形态，不是当前证据分 |
| 静态实现证据 | 已存在部分文档、契约测试与检查器输出，但未形成当前总评分 | 只能陈述具体文件与新鲜命令结果 |
| 人机需求设计静态证明 | `human_requirement_design_static_fixture_only` | 只证明模板、契约和正反例失败关闭；不证明真实人工或真实 L2 |
| 审核策略认证静态证明 | `static_contract_and_synthetic_fixture_only` | 只证明策略包、预注册测试、认证/激活路由与反例门禁；不证明真实模型或真实 L2 |
| fixture 证明 | `fixture_runtime_proven` | 仅匿名 operational-spine fixture；不得外推成本地真实运行 |
| 本地真实证明 | `not_evaluated` | 不得外推为只读真实或生产证明 |
| 只读真实证明 | `not_evaluated` | 不得外推为生产写入或业务效果 |
| 生产证明 | `not_evaluated` | 不得声明生产就绪或业务成功 |

成熟度字段不能证明运行能力。`maturity`、静态测试、fixture、本地真实、只读真实和生产证明必须分开记录；跨项目隔离验证和第二个异构 L2 验证仍是未满足硬门禁。
