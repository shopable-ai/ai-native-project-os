# AI Project OS L1 去污染与可用性修复实施计划

> 状态：`absorbed_by` [2026-07-11-ai-project-os-operational-spine-implementation.md](2026-07-11-ai-project-os-operational-spine-implementation.md)。本文件不是活动权威，以下原内容仅作为审计输入保留。

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 清除 L1 仓库中的具体业务污染和检查器豁免漏洞，补齐权威导航、术语消歧、可复制模板与通用 L2 推进 SOP。

**Architecture:** 保持 single editable truth per topic：既有权威文件继续定义语义，新文件只承担缺失的索引或操作编排。C4 使用通用具体路径模式检查所有 L1 文本和模板，不包含任何业务名特判；模板样例使用统一占位符并明确 fixture 声明上限。

**Tech Stack:** 简体中文 Markdown、YAML、Python 3 `unittest`、现有 `linters/check_controlled_objects.py`。

---

### Task 1: C4 回归测试与通用实现

**Files:**
- Modify: `tests/test_check_controlled_objects.py`
- Modify: `linters/check_controlled_objects.py`

- [ ] 在测试中构造普通文档和 `templates/` 文档，证明 `projects/<concrete_id>/` 被 C4 报告。
- [ ] 在测试中证明 `projects/{project_id}/`、`{{l2_repo}}` 等占位符不会被报告。
- [ ] 先运行新增测试，确认旧实现因模板跳过而失败。
- [ ] 删除具体业务正则、`C4_EXEMPT_FILES` 和 `templates/` 整体跳过，仅保留通用具体 L3 路径检测。
- [ ] 运行 `python3 -m unittest tests.test_check_controlled_objects -v`，确认回归测试通过。

### Task 2: 第一波文档去污染与 N3 修复

**Files:**
- Modify: `README.md`
- Modify: `docs/workflows/L2_ONBOARDING.md`
- Modify: `docs/workflows/IMPLEMENTATION_PLAN.md`
- Modify: `docs/governance/DIAGRAM_CONVENTIONS.md`
- Modify: `templates/standard-project/README.md`
- Modify: `docs/superpowers/specs/2026-07-11-项目推进骨架设计.md`

- [ ] 统一使用 `{{l1_repo}}`、`{{l2_repo}}`、`{{project_id}}`、`{{business_term}}`、`{{spec_id}}` 等占位符。
- [ ] 删除具体渠道、领域术语、项目内部目录和单项目升格依据。
- [ ] 将 L2 接入 Evidence 留在 L2；L1 只接收通过升格门禁的匿名兼容快照。
- [ ] 保留图规范在 `docs/governance/`，把 IMPLEMENTATION_PLAN 的禁改声明收窄为“不修改计划外既有权威”。
- [ ] 运行全仓业务名和业务路径扫描，确认零残留。
- [ ] 运行 `python3 linters/check_controlled_objects.py . --report` 并保存第一波 JSON Evidence。

### Task 3: 权威导航、抬头和术语消歧

**Files:**
- Create: `policies/README.md`
- Modify: `docs/governance/GATES_PROOF_SCORING.md`
- Modify: `docs/governance/ARTIFACTS_AND_TRACEABILITY.md`
- Modify: `docs/research/RESEARCH_WORKFLOW.md`
- Modify: `AGENTS.md`
- Modify: `docs/architecture/FRAMEWORK_EDITION_MODEL.md`
- Modify: `docs/architecture/REPOSITORY_AND_LAYER_CONTRACT.md`
- Modify: `docs/governance/CONTROLLED_OBJECT_MODEL.md`
- Modify: `docs/workflows/PROJECT_TYPE_AND_GOVERNANCE_ROUTING.md`

- [ ] 用一张表说明 9 个 policy/contract 的职责、引用关系、阅读顺序和核心/扩展分类。
- [ ] 给三份缺抬头的权威文件补“权威范围、读者、阅读时机、产出”。
- [ ] 在 AGENTS 架构权威地图中补齐三份架构文件的独立职责。
- [ ] 在各自唯一权威中区分 framework edition `standard`、base governance profile `standard`、仓库层级 `L1/L2/L3` 与机器字段 `l1/l2/l3`。
- [ ] 运行检查器并确认第二波独立通过。

### Task 4: 可复制 standard-project 模板

**Files:**
- Modify: `templates/standard-project/README.md`
- Create: `templates/standard-project/domain/glossary.md`
- Create: `templates/standard-project/domain/mvp/REQ-001.md`
- Create: `templates/standard-project/specs/REQ-001/spec.md`
- Create: `templates/standard-project/specs/REQ-001/plan.md`
- Create: `templates/standard-project/specs/REQ-001/tasks.md`
- Create: `templates/standard-project/specs/REQ-001/acceptance.md`
- Create: `templates/standard-project/specs/REQ-001/traceability.md`
- Create: `templates/standard-project/reviews/REQ-001-review-evidence.yaml`

- [ ] 使用通用、非行业化样例提供一条批准 fact 和一条批准 requirement。
- [ ] 让 Spec 五件套只追溯到模板内 `domain/`，不引用 `reference/` 或外部项目。
- [ ] review evidence 明确为 fixture/captured，不签发真实 Acceptance Verdict 或 Completion Claim。
- [ ] README 展示完整目录树，并标注必需、条件启用和运行时生成。
- [ ] 运行模板检查、单元测试和第三波全仓检查器。

### Task 5: 通用 L2 推进 SOP

**Files:**
- Create: `docs/workflows/L2_PROGRESSION.md`
- Modify: `docs/workflows/L2_ONBOARDING.md`
- Modify: `README.md`
- Modify: `project-os.yaml`

- [ ] 串联 L1 锁定、L2 接入、项目类型判断、R0 与 S0-S7。
- [ ] 每阶段列出动作、产物、权威门禁和失败重开目标，但不复制状态或证据枚举。
- [ ] 在 README 和 `project-os.yaml.authority` 注册唯一入口。
- [ ] 运行第四波检查器。

### Task 6: 最终验证

**Files:**
- Verify all changed files only; do not modify unrelated `.shopme/` state.

- [ ] 运行 `python3 -m unittest discover -s tests -v`。
- [ ] 运行 `python3 linters/check_controlled_objects.py . --report` 并保存最终 JSON Evidence。
- [ ] 解析全部 YAML，检查 Markdown 相对链接和权威路径。
- [ ] 扫描具体业务名、业务路径、自然语言渠道样例和占位符风格。
- [ ] 运行 `git diff --check`，复核未覆盖或未验证边界。
