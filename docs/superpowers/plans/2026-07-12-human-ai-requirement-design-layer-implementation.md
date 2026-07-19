# 人机协作需求设计层实施计划

**Goal:** 在已完成的方案 B 机器操作骨架上，补齐人类从原始意图到功能需求批准基线再到 Spec 的可阅读、可追溯、可失败关闭路径。

**Architecture:** 复用现有 `requirement`、Unknown/Research、AI Review、版本/hash/supersedes、失效传播和 S7 资产演进；新增一个人类需求工作流、一个需求设计包契约和一个标准 L2 实例。功能需求卡是单功能权威，项目地图是引用视图，baseline/context 是机器记录，`generated/` 不是事实源。

**Constraints:** 当前总分保持 `not_evaluated`；不新增 `critical` 基础 Profile；不建设需求平台、工作流引擎或影响模拟器；不把聊天和 `.prompts/` 变成权威。

## 0. 开工审计

### 可直接复用

- `docs/governance/CONTROLLED_OBJECT_MODEL.md`：已有 Source、Fact、Requirement、Unknown、Scenario、Chain、Capability、Function、ADR、Spec 和公共版本/审批/失效字段。
- `docs/research/RESEARCH_WORKFLOW.md`：已有 `Unknown → Research → Decision` 和候选结论升格门禁。
- `docs/governance/STATE_TRANSITIONS_AND_INVALIDATION.md`：已有 `supersedes`、下游失效传播和上游复审请求。
- `docs/architecture/AI_NATIVE_EXECUTION_MODEL.md` 与授权文档：已有 generator/reviewer/approver/verifier 责任分离。
- S7 复盘和资产升格：已有学习回流语义。
- C9 contract-driven 模板检查器：可复用来验证新需求设计包，无需新增自然语言路由规则。

### 需要补齐

- `PROJECT_DELIVERY_WORKFLOW.md` 从功能树直接进入 ADR/Spec，缺功能需求设计和人工批准冻结。
- `STAGE_EXIT_GATES` 的 S2/S5 缺功能需求卡、意图对齐和 baseline 绑定门禁。
- 标准 L2 模板没有 `requirements/`、项目地图、功能需求卡、baseline 和 context snapshot。
- 当前匿名 E2E fixture 没有证明未批准功能需求不能进入 Spec。

### 暂缓而不伪装完成

- 自动 Impact Simulation、项目地图生成器、上下文自动打包器、真实 L2 迁移和第二异构 L2。
- 历史 `86.4/96.4/97.6` 设计估算不进入当前评分入口。

## 1. 阶段一：建立人类需求推理权威

**Files:**

- Create: `docs/workflows/REQUIREMENT_DESIGN_WORKFLOW.md`
- Modify: `docs/workflows/PROJECT_DELIVERY_WORKFLOW.md`
- Modify: `docs/workflows/L2_PROGRESSION.md`
- Modify: `docs/workflows/STAGE_EXIT_GATES.md`
- Modify: `docs/governance/CONTROLLED_OBJECT_MODEL.md`
- Modify: `docs/governance/ARTIFACTS_AND_TRACEABILITY.md`
- Modify: `docs/governance/TERMINOLOGY.md`
- Modify: `docs/architecture/AI_PROJECT_OS_OVERVIEW.md`
- Modify: `AGENTS.md`, `README.md`, `project-os.yaml`
- Test: `tests/test_requirement_design_layer.py`

1. 先写失败测试：新权威存在并注册；主追溯链包含 Functional Requirement；S2/S5 门禁包含意图、批准和 baseline；术语清单没有引入新状态轴。
2. 写需求设计工作流，固定 `Source → ... → Functional Requirement → approval/baseline → ADR → Spec`，包含人工逐步审查问题和 AI 自检。
3. 同步总览、推进工作流、L2 SOP、追溯模型、术语和 README；不得复制机器枚举。
4. 运行 `python3 -m unittest tests.test_requirement_design_layer tests.test_operational_spine_docs -v`。
5. 失败回退：只撤销本阶段权威引用，不修改既有 Run/Evidence 契约。
6. Lore 提交：说明本阶段只建立人类设计控制流，不证明模板或运行。

## 2. 阶段二：建立需求设计包契约与 L2 模板

**Files:**

- Create: `contracts/artifacts/requirement-design-package-contract.yaml`
- Create: `templates/standard-project/requirements/README.md`
- Create: `templates/standard-project/requirements/项目地图.md`
- Create: `templates/standard-project/requirements/functions/FUNC-001_功能需求卡.md`
- Create: `templates/standard-project/requirements/baselines/REQ-BASELINE-001.yaml`
- Create: `templates/standard-project/requirements/context/CTX-001.yaml`
- Create: `templates/standard-project/requirements/generated/README.md`
- Modify: `templates/standard-project/README.md`
- Modify: `templates/README.md`
- Modify: `project-os.yaml`
- Modify: `tests/test_template_packages.py`
- Modify: `tests/test_standard_project_template.py`

1. 写失败测试：第七个模板契约注册；所有真实模板文件与字段/章节完整；项目地图不成为第二份需求权威；`generated/` 只含说明。
2. 契约要求四段意图、`requirement_kind: functional`、AI 自检、人工批准、version/hash/supersedes、baseline 和 context refs。
3. baseline 列出 `stable_id/version/content_hash`；context snapshot 列出 included/excluded/reason/hash/generated/approved。
4. 功能需求卡把“已批准实现约束”与“候选实现要点”分开。
5. 运行模板正例和逐字段/逐章节 mutation 反例。
6. 失败回退以整个需求设计包为边界；不得留下注册但不存在的 authority。
7. Lore 提交：不声称生成器、影响模拟或真实 L2 已实现。

## 3. 阶段三：修正阶段机器门禁与人机需求正反例

**Files:**

- Modify: `contracts/governance/stage-exit-gates-contract.yaml`
- Create: `fixtures/requirement-design/positive/*`
- Create: `fixtures/requirement-design/negative/*`
- Extend: `tests/test_requirement_design_layer.py`

1. S0/S2/S5 机器门禁增加批准意图、功能需求 coverage、baseline 与 Spec 精确绑定。
2. 正例证明业务 Requirement → Chain → Capability → Function → Functional Requirement → ADR → Spec。
3. 负例至少拒绝：意图漂移、AI 自批、未批准需求进入 Spec、baseline 原地修改、上下文包含 `.prompts/`。
4. 运行 `python3 -m unittest tests.test_requirement_design_layer tests.test_contract_policy_boundaries tests.test_operational_spine_checker -v` 和全仓 checker。
5. 失败回退只回退新增 criterion 内容和 fixture，不削弱原九阶段 fail-closed 结构。
6. Lore 提交：证明范围限定为静态正反例 fixture。

## 4. 阶段四：证据与声明收口

**Files:**

- Create: `reviews/human-ai-requirement-design-static-evidence.yaml`
- Modify: `reviews/current-score-status.yaml`
- Modify: `README.md`, `project-os.yaml`

1. 记录新鲜 revision、命令、测试数、checker、YAML/JSON、Markdown 链接、diff check 和已知缺口。
2. 分开报告：方案 B 旧目标 `95.93`、历史讨论估算 `86.4/96.4/97.6`、当前总体 `not_evaluated`。
3. 保留硬门禁：真实人工可用性测试、真实 L2 消费、跨项目隔离、第二异构 L2、自动影响模拟和独立反方评审。
4. 全量执行：
   - `python3 -m unittest discover -s tests -v`
   - `python3 linters/check_controlled_objects.py . --report`
   - 解析所有有效 YAML/JSON
   - Markdown 链接测试
   - `python3 -m py_compile linters/check_controlled_objects.py tests/*.py`
   - `git diff --check`
   - `git status --short`
5. P0/P1 非零、反例未被拒绝或工作树混入无关文件时不得提交完成。
6. Lore 提交并推送 `main`；`Not-tested` 明确真实用户、真实 L2 和生产能力未证明。
