# Framework Edition and Project Governance Alignment Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 逐文件消除框架版本等级、项目治理配置、叠加能力、生命周期和证据成熟度之间的语义漂移。

**Architecture:** `project-os.yaml` 保存机器目录和当前状态；框架等级与项目治理分别拥有独立权威文件。其他文档只引用权威语义，历史 ADR、设计记录和审查 Evidence 通过替代关系保留。

**Tech Stack:** YAML、Markdown、Git、PyYAML 验证命令。

---

### Task 1: 建立唯一分类模型

**Files:**
- Create: `docs/architecture/FRAMEWORK_EDITION_MODEL.md`
- Modify: `project-os.yaml`
- Modify: `docs/architecture/AI_PROJECT_OS_CORE.md`

- [x] 定义 `minimal/standard/platform/enterprise` 四级框架范围。
- [x] 将项目治理拆成 `lite|standard` 基础配置和 `multi_agent|production` 叠加能力。
- [x] 删除 `selected_profile` 和无语义层次的 `enabled`。
- [x] 明确 design、implementation、verification 和 claim ceiling。

### Task 2: 修正项目路由和消费者契约

**Files:**
- Move: `docs/workflows/PROJECT_TYPE_AND_PROFILE_ROUTING.md` → `docs/workflows/PROJECT_TYPE_AND_GOVERNANCE_ROUTING.md`
- Modify: `docs/architecture/REPOSITORY_AND_LAYER_CONTRACT.md`
- Modify: `docs/governance/RUN_EVIDENCE_ACCEPTANCE.md`
- Create: `policies/route-decision-contract.yaml`
- Create: `policies/control-set-contract.yaml`
- Create: `policies/overlay-activation-verdict-contract.yaml`
- Create: `policies/authorization-snapshot-contract.yaml`
- Create: `policies/acceptance-verdict-claim-contract.yaml`

- [x] 定义版本化 `route_decision`、基础配置、逐 overlay 状态和 control set hash。
- [x] 定义 control set 必需控制类别与叠加能力激活裁决机器契约。
- [x] 定义授权快照与业务验收/声明机器契约，阻断非空字符串授权和空证据接受。
- [x] 修改 `project-os.lock` 和 L3 示例，删除单值 `profile`。
- [x] 让 Run、Evidence、Verdict 和 Claim 绑定同一路由与控制集。

### Task 3: 修正状态、权限和追溯引用

**Files:**
- Modify: `docs/workflows/PROJECT_LIFECYCLE.md`
- Modify: `docs/workflows/ARCHITECT_WORKFLOWS.md`
- Modify: `docs/governance/CONTROLLED_OBJECT_MODEL.md`
- Modify: `docs/governance/STATE_TRANSITIONS_AND_INVALIDATION.md`
- Modify: `docs/governance/AUTHORIZATION_SIDE_EFFECTS_AND_ISOLATION.md`
- Modify: `docs/governance/ARTIFACTS_AND_TRACEABILITY.md`

- [x] 将生命周期、工作、审批、失效、实现和 proof 字段明确分离。
- [x] 增加 route/control set 引用和变化传播范围。
- [x] 明确 external side effect 不等于 production 叠加能力。

### Task 4: 修正入口、决策和研究语义

**Files:**
- Modify: `README.md`
- Modify: `decisions/ADR-0001-standard-profile-thin-kernel.md`
- Create: `decisions/ADR-0002-separate-framework-edition-and-project-governance.md`
- Modify: `docs/research/RESEARCH_WORKFLOW.md`
- Modify: `research/registry.yaml`
- Create: `reviews/profile-taxonomy-alignment-resolution.yaml`

- [x] README 只摘要目标等级和真实成熟度。
- [x] ADR-0001 标记被替代，ADR-0002 保存新决策。
- [x] 把 production Profile 研究项改成具体生产准入/分发决策。
- [x] 保留旧审查原文，在新 resolution 中记录当前处理状态。

### Task 5: 验证和评分边界

**Files:**
- Create: `reviews/profile-taxonomy-alignment-score.yaml`
- Modify: `project-os.yaml`

- [x] 解析全部 YAML 并检查所有登记路径。
- [x] 检查 Markdown 链接、旧分类规范残留、单值 Profile 和 `enabled: true`。
- [x] 验证历史 Evidence 未被当作当前权威。
- [x] 运行 `git diff --check`，记录实现、本地运行和生产证明仍为 0。
