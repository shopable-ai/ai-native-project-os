# AI 项目推进操作系统

> 目标框架版本等级：`standard`。
>
> 当前成熟度：设计待复核；实现未开始；运行与生产证明均不存在。

AI 项目推进操作系统用于把模糊需求转化为可研究、可决策、可执行、可验证、可恢复和可演进的项目。它不是某个业务项目，也不是某个智能体框架的包装层。

## 当前决策

- 目标框架版本等级采用 `standard`，最高等级 `enterprise` 本阶段不建设。
- 项目治理由 `lite|standard` 基础配置叠加 `multi_agent|production` 能力，不与框架等级混用。
- 采用自研薄内核，外部能力通过适配器接入。
- 通用方法和协议保存在本仓库。
- 具体业务能力保存在业务系统仓库。
- 具体项目事实、运行记录和交付物保存在对应 L2 约定的 `projects/{project_id}/` namespace，不在 L1 预建实例目录。
- 外部开源能力通过适配器接入，不成为内核语义。
- 研究材料不是事实源；只有通过门禁后才能升格为事实、决策、契约或正式资产。
- 人类批准并维护版本化 Markdown 规则；普通内容由独立 AI 依据规则自动审核，不等待人工逐条批准。
- AI 审核通过不授予发送、付款、删除或生产发布权限；不可逆动作仍使用独立人工授权。

## 第一次阅读

1. [核心架构](docs/architecture/AI_PROJECT_OS_CORE.md)
2. [框架版本等级](docs/architecture/FRAMEWORK_EDITION_MODEL.md)
3. [仓库与层级契约](docs/architecture/REPOSITORY_AND_LAYER_CONTRACT.md)
4. [受控对象模型](docs/governance/CONTROLLED_OBJECT_MODEL.md)
5. [项目生命周期](docs/workflows/PROJECT_LIFECYCLE.md)
6. [项目类型与治理配置路由](docs/workflows/PROJECT_TYPE_AND_GOVERNANCE_ROUTING.md)
7. [状态迁移与失效传播](docs/governance/STATE_TRANSITIONS_AND_INVALIDATION.md)
8. [AI 原生执行模型](docs/architecture/AI_NATIVE_EXECUTION_MODEL.md)
9. [权限、副作用与隔离](docs/governance/AUTHORIZATION_SIDE_EFFECTS_AND_ISOLATION.md)
10. [Run、Evidence、验收裁决](docs/governance/RUN_EVIDENCE_ACCEPTANCE.md)
11. [门禁、唯一证据枚举与评分](docs/governance/GATES_PROOF_SCORING.md)
12. [研究工作流与登记表](docs/research/RESEARCH_WORKFLOW.md)

## 权威文件

| 问题 | 权威文件 |
|---|---|
| 核心原语和架构平面 | `docs/architecture/AI_PROJECT_OS_CORE.md` |
| 四级框架版本范围 | `docs/architecture/FRAMEWORK_EDITION_MODEL.md` |
| L1/L2/L3 仓库、兼容和资产升格 | `docs/architecture/REPOSITORY_AND_LAYER_CONTRACT.md` |
| R0、S0—S7 怎么推进 | `docs/workflows/PROJECT_LIFECYCLE.md` |
| 项目类型和治理配置怎么选择 | `docs/workflows/PROJECT_TYPE_AND_GOVERNANCE_ROUTING.md` |
| 项目治理的机器路由条件 | `policies/project-governance-routing.yaml` |
| 架构师具体做什么 | `docs/workflows/ARCHITECT_WORKFLOWS.md` |
| 文件之间如何追溯 | `docs/governance/ARTIFACTS_AND_TRACEABILITY.md` |
| 受控对象字段、类型与固定主链 | `docs/governance/CONTROLLED_OBJECT_MODEL.md` |
| 状态迁移与失效传播 | `docs/governance/STATE_TRANSITIONS_AND_INVALIDATION.md` |
| AI 执行节点与上下文治理 | `docs/architecture/AI_NATIVE_EXECUTION_MODEL.md` |
| 权限、外部副作用和项目隔离 | `docs/governance/AUTHORIZATION_SIDE_EFFECTS_AND_ISOLATION.md` |
| Run、Evidence、裁决和声明 | `docs/governance/RUN_EVIDENCE_ACCEPTANCE.md` |
| 唯一证据枚举与可重算评分 | `docs/governance/GATES_PROOF_SCORING.md` |
| 人工治理规则集机器契约 | `policies/governance-rule-set-contract.yaml` |
| AI 自动审核裁决机器契约 | `policies/ai-review-verdict-contract.yaml` |
| 规则缺口异步治理机器契约 | `policies/rule-gap-case-contract.yaml` |
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

```text
✅ 分类维度修订草案已形成
✅ 反方复核与设计验收（见 reviews/p0-design-review-*.yaml）
✅ 设计基线复核（设计态评分 84，见 reviews/p0-design-revision-score.yaml）
✅ 编写最小实现计划（见 docs/workflows/IMPLEMENTATION_PLAN.md）
✅ 实现最小检查器（linters/check_controlled_objects.py，EXIT=0，见 reviews/phase0-checker-evidence.yaml）
✅ 标准版骨架目录契约（templates/standard-project/ + templates/brownfield-project/）
→ 使用当前业务项目完成 L2 存量架构恢复试点   ← 当前位置
    入口：docs/workflows/L2_ONBOARDING.md
    试点项目：operate-auto-customer（brownfield）
    验收目标：L2 项目 project-os.lock 存在 + 检查器 --l2-mode EXIT=0
```

Phase 0 完成后预计评分：89（"无跨项目隔离"89 封顶接着咬）。
Phase 2（L2 试点）完成后预计评分：92。

实时状态只读取 `project-os.yaml.maturity`。当前实现分：Phase 0 完成；本地运行证明和生产证明均不存在。
