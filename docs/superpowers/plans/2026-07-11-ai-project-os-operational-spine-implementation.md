# AI Project OS 方案 B 项目推进操作骨架实施计划

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 在不建设完整工作流平台的前提下，补齐 AI Project OS 从需求种子到复盘升格的文档、契约、模板、检查器、正反例 fixture 与证据骨架，并保持当前总体评分为 `not_evaluated`，直到证据满足声明条件。

**Architecture:** 人类入口、机器契约和项目实例三层分离：`docs/` 解释推进控制流，`contracts/` 定义结构/I/O/manifest/失败语义，`policies/` 定义路由/风险/授权决策/门禁/声明封顶，`templates/` 提供可复制资产，`fixtures/` 与 `tests/` 证明静态闭环。生命周期、工作状态、实现状态、证据等级、框架等级和项目治理配置保持正交；任务总树只能从各 Spec 的 `tasks.md` 生成。

**Tech Stack:** 中文 Markdown、YAML、Python 3 标准库、PyYAML（仓库既有测试依赖）、`unittest`、现有 `linters/check_controlled_objects.py`、Git Lore 提交协议。

---

## 0. 开工审计与保护边界

设计输入以提交 `899253d` 中的 `docs/superpowers/specs/2026-07-11-ai-project-os-operational-spine-design.md` 为批准基线；当前分支已将它 Git rename 为 `docs/superpowers/specs/2026-07-11-项目推进骨架设计.md` 并补充可读性要求。用户本次明确要求的英文稳定输出路径优先于后续设计稿中的中文重命名建议。

### 可直接复用

- `templates/standard-project/project-os.lock.yaml`：字段边界可复用，需纳入模板完整性检查。
- `templates/standard-project/domain/README.md`：`domain/` 作为批准事实层的方向可复用，需去除“说明占位即目录”的做法并补真实模板文件。
- `docs/governance/DIAGRAM_CONVENTIONS.md`：图覆盖分类和 Mermaid 可核验原则可复用，需去除具体 L2 项目样板绑定并把 backlog 变为检查规则。
- `docs/workflows/L2_ONBOARDING.md`：L1 锁定、项目类型判断、R0 入口和 L2 Evidence 留在 L2 的原则可复用，需改为通用 SOP。
- `linters/check_controlled_objects.py` 与 `tests/test_check_controlled_objects.py`：现有 C1—C7、退出码和临时仓库测试框架可复用。
- `project-os.yaml` 新增 Evidence 槽位的意图可复用，但不能引用未成立的当前评分或具体 L2 试点。

### 需要修正

- `README.zh-CN.md`：历史 84 分、“预计 89/92”、Phase 0 已完成和具体 L2 当前位置均与 `not_evaluated`、通用 L1 边界冲突。
- `docs/workflows/IMPLEMENTATION_PLAN.md`：L1 实施计划位置错误、使用旧评分口径并绑定具体 L2；内容迁入本计划的审计记录后，旧草稿保存为明确标记 `superseded` 的历史计划，不再作为 workflow 权威。
- `reviews/phase0-checker-evidence.yaml`：记录的 55 文件/EXIT=0 已被当前 74 文件扫描和 2 个 P1 推翻，只能保留为失效历史证据，不能作为当前评分入口。
- `linters/check_controlled_objects.py` 的 C4 豁免：通过文件名豁免具体业务路径会隐藏 L1 污染；改为结构化占位符与 fixture 范围处理。
- `templates/standard-project/domain/README.md`：只有说明文件不足以构成正式模板，需要最小真实资产。
- `docs/superpowers/plans/2026-07-11-l1-decontamination-and-usability.md` 与 `tests/test_check_controlled_objects.py` 的并发差异：视为用户工作树内容，合并其通用 C4 正反例意图；不得覆盖或单独丢弃。

### 与本任务无关

- `.shopme/link-index.json`：ShopMe 生成索引更新。
- `.shopme/rules.json`：Mermaid AI 图片规则与付费生成安全策略。
- `.shopme/version.json`：ShopMe CLI 版本和生成时间更新。

以上三个文件不编辑、不暂存、不提交；每次提交前使用 `git diff --cached --name-only` 确认它们未进入提交。

## 1. 阶段一：校准人类入口、推进文档与评分真相

**Files:**

- Create: `docs/architecture/AI_PROJECT_OS_OVERVIEW.md`
- Create: `docs/workflows/PROJECT_DELIVERY_WORKFLOW.md`
- Create: `docs/workflows/STAGE_EXIT_GATES.md`
- Create: `docs/governance/TERMINOLOGY.md`
- Modify: `README.zh-CN.md`
- Modify: `project-os.yaml`
- Modify: `docs/workflows/L2_ONBOARDING.md`
- Modify: `docs/governance/DIAGRAM_CONVENTIONS.md`
- Create: `docs/superpowers/plans/2026-07-10-minimum-implementation-draft.superseded.md`
- Remove after preservation: `docs/workflows/IMPLEMENTATION_PLAN.md`
- Modify: `reviews/phase0-checker-evidence.yaml`
- Test: `tests/test_operational_spine_docs.py`

- [ ] **Step 1: 写文档权威路径和评分口径的失败测试**

  新增 `tests/test_operational_spine_docs.py`，断言四个新权威文件存在；`project-os.yaml.authority` 指向它们；README 同时包含 `not_evaluated`、`95.93`、静态实现证据、fixture 证明、本地证明、生产证明，并禁止把历史 84 或子方案 96 写成当前总分。

- [ ] **Step 2: 运行测试并确认 RED**

  Run: `python3 -m unittest tests.test_operational_spine_docs -v`

  Expected: FAIL，原因是四个权威文件或 `project-os.yaml.authority` 键尚不存在，而不是导入错误。

- [ ] **Step 3: 写人类总览和四条主线总图**

  `AI_PROJECT_OS_OVERVIEW.md` 只解释推进控制流、追溯依赖链、正交状态坐标、框架/治理配置四条主线，使用 Mermaid 引用 R0/S0—S7；阶段字段和机器枚举链接到权威文件，不在总图复制一份可编辑枚举。

- [ ] **Step 4: 写完整项目推进控制流**

  `PROJECT_DELIVERY_WORKFLOW.md` 固定：需求种子/存量系统 → 类型判断 → 治理路由 → 阶段定位 → 研究 → 链路 → ADR → 工程设计 → Spec/Task → Workflow → Skill/Tool → Run → Evidence → Verdict → Claim → 复盘升格。明确能力树从业务链路推导，任务图从批准 Spec 和验收判据推导，Workflow 编排 Task，Skill 只承担局部复用能力。

- [ ] **Step 5: 写阶段门禁人类视图和 L1 术语权威**

  `STAGE_EXIT_GATES.md` 逐阶段列输入、必需产物、出口门禁、Evidence、失效条件和重开目标；`TERMINOLOGY.md` 为 framework edition、governance profile、stage、work status、implementation status、proof level、chain/capability/function/task、Workflow/Skill/Tool、Run/Evidence/Verdict/Claim 提供唯一中文定义和稳定 `term-id`。

- [ ] **Step 6: 校准 README、机器成熟度和历史 Evidence**

  `project-os.yaml.maturity` 继续使用 `not_started/unverified` 或更保守的已验证静态状态，不从文件存在推导运行能力；`scoring_evidence.current` 指向仍为 `not_evaluated` 的入口。README 分列当前总体分、目标设计分、静态实现证据、fixture、本地、只读真实和生产证明。旧 Phase 0 Evidence 增加 `stale_status: invalidated`、失效原因和禁止声明，不再作为当前评分证据。

- [ ] **Step 7: 保存并移出旧实施草稿，去除 L2 污染**

  将旧 `IMPLEMENTATION_PLAN.md` 内容保存为 `docs/superpowers/plans/2026-07-10-minimum-implementation-draft.superseded.md`，顶部写明历史草稿、已失效评分口径和替代计划；通用 L2 SOP 与图规范改用 `{{l1_repo}}`、`{{l2_repo}}`、`{{project_id}}`，不保留具体业务项目名或路径。

- [ ] **Step 8: 运行 GREEN 与阶段验证**

  Run: `python3 -m unittest tests.test_operational_spine_docs -v`

  Run: `python3 -m unittest discover -s tests -v`

  Run: `python3 -c 'import pathlib,yaml; [yaml.safe_load(p.read_text()) for p in pathlib.Path(".").rglob("*.yaml")]'`

  Expected: 全部 EXIT=0；若失败，回退本阶段新增权威路径和 README 引用，不修改既有治理语义。

- [ ] **Step 9: Lore 提交**

  只暂存本阶段文件。提交意图：让使用者从唯一入口看到真实推进能力和声明边界。

## 2. 阶段二：迁移 contracts/policies 边界并建立阶段机器契约

**Files:**

- Create: `contracts/README.md`
- Create: `policies/README.md`
- Create: `contracts/governance/stage-exit-gates-contract.yaml`
- Git move: `policies/*-contract.yaml` → `contracts/governance/*-contract.yaml`
- Create: `decisions/ADR-0004-separate-contracts-from-policies.md`
- Modify: `policies/project-governance-routing.yaml`
- Modify: `project-os.yaml`
- Modify: all Markdown references returned by `rg -n 'policies/[^ )`]+-contract\.yaml|(?:route|control|verdict|snapshot|rule-gap)-[^ )`]*contract' .`
- Modify: `tests/test_ai_review_governance_contracts.py`
- Test: `tests/test_contract_policy_boundaries.py`

- [ ] **Step 1: 写旧路径必须失效、新路径必须解析的失败测试**

  测试断言 `policies/` 只剩决策 policy 和导航；所有 `*-contract.yaml` 位于 `contracts/governance/`；`project-os.yaml.authority` 和 policy 内 `source_contracts` 指向新路径；所有引用可解析。

- [ ] **Step 2: 运行测试并确认 RED**

  Run: `python3 -m unittest tests.test_contract_policy_boundaries -v`

  Expected: FAIL，列出仍在 `policies/` 的八个 contract 文件。

- [ ] **Step 3: 使用 Git move 迁移所有 contract**

  Run: `mkdir -p contracts/governance`

  Run: `git mv policies/acceptance-verdict-claim-contract.yaml policies/ai-review-verdict-contract.yaml policies/authorization-snapshot-contract.yaml policies/control-set-contract.yaml policies/governance-rule-set-contract.yaml policies/overlay-activation-verdict-contract.yaml policies/route-decision-contract.yaml policies/rule-gap-case-contract.yaml contracts/governance/`

  不复制旧文件，不保留双权威。

- [ ] **Step 4: 新增阶段门禁机器契约**

  契约固定 `R0,S0,S1,S2,S3,S4,S5,S6,S7` 九个 stage；每个 stage 必须有非空 `required_inputs`、`required_artifacts`、`exit_criteria`、`evidence_requirements`、`invalidation_triggers`、`reopen_targets`；记录 manifest 必须包含 scope、commands、result、gaps、waivers、approver、verifier、timestamps 和 hashes。

- [ ] **Step 5: 同步所有引用和 ADR**

  ADR 记录边界、Git move、拒绝保留兼容副本以及失败回退：若消费者尚未迁移，只能在同一提交内修正引用，不能恢复双权威。README 分别按“结构问题”和“决策问题”导航。

- [ ] **Step 6: 运行 GREEN 与引用扫描**

  Run: `python3 -m unittest tests.test_contract_policy_boundaries tests.test_ai_review_governance_contracts -v`

  Run: `rg -n 'policies/[^ )`]+-contract\.yaml' . --glob '!docs/superpowers/plans/**' --glob '!docs/superpowers/specs/**'`

  Expected: 测试通过；活动权威/代码/测试中的旧路径零命中。历史设计和计划允许保留原始路径作为证据，不作为活动引用。

- [ ] **Step 7: Lore 提交**

  只提交 Git move、ADR、导航、阶段契约和同步引用。失败时不拆分提交；恢复到移动前只能通过反向 `git mv`，不得 reset 工作树。

## 3. 阶段三：建立标准产物模板与包契约

**Files:**

- Create: `contracts/artifacts/chain-package-contract.yaml`
- Create: `contracts/artifacts/spec-package-contract.yaml`
- Create: `contracts/io/io-contract.yaml`
- Create: `contracts/execution/workflow-contract.yaml`
- Create: `contracts/execution/skill-contract.yaml`
- Create: `contracts/governance/project-instance-contract.yaml`
- Create: `templates/README.md`
- Create: `templates/chain-package/{README.md,chain.yaml,scenarios.md,triggers.yaml,business-flow.md,exceptions.md,recovery.md,responsibility-map.md,io-map.yaml,traceability.md,acceptance.md,diagrams/README.md}`
- Create: `templates/spec-package/{README.md,spec.md,plan.md,tasks.md,acceptance.md,traceability.md}`
- Create: `templates/io-contract/{README.md,io-contract.yaml}`
- Create: `templates/workflow/{README.md,workflow.yaml}`
- Create: `templates/skill/{README.md,SKILL.md,skill.yaml}`
- Create: `templates/project-instance/{README.md,project.yaml,project-os.lock.yaml,governance-route.yaml,facts/facts.yaml}`
- Modify: `templates/standard-project/README.md`
- Modify: `templates/standard-project/domain/README.md`
- Test: `tests/test_template_packages.py`

- [ ] **Step 1: 写六类模板完整性的失败测试**

  测试读取对应 contract 的 `required_files` 和 `required_fields`，断言模板文件存在、YAML 可解析、占位符只使用 `{{snake_case}}`、README 展示完整复制后目录树并标注“必需/条件启用/运行时生成”。

- [ ] **Step 2: 运行测试并确认 RED**

  Run: `python3 -m unittest tests.test_template_packages -v`

  Expected: FAIL，原因是六类模板或包契约缺失。

- [ ] **Step 3: 实现链路包和 Spec 包**

  链路包必须含正常/异常/恢复链、责任主体、I/O、追溯、验收和图入口；Spec 包五件套中 `tasks.md` 是单 Spec 任务权威，`plan.md` 只排序，不建立另一任务清单。README 明确跨 Spec 总树是生成视图。

- [ ] **Step 4: 实现 I/O、Workflow 和 Skill 模板**

  I/O 模板覆盖 producer/consumer、schema、成功/失败 envelope、错误、重试、幂等、超时、顺序、部分结果、数据分类、兼容和迁移；Workflow 引用 Task 并覆盖 checkpoint/cancel/compensation/evidence/claim ceiling；Skill 只声明局部能力，不隐藏跨阶段编排。

- [ ] **Step 5: 实现可选 L3 项目实例模板**

  模板包含 namespace、路由锁、事实和隔离边界；Run/Evidence/Verdict/Claim/交付目录只在 README 标记为运行时生成，不创建空目录。L3 只有在多实例隔离有证据时启用。

- [ ] **Step 6: 运行 GREEN 与模板 YAML 解析**

  Run: `python3 -m unittest tests.test_template_packages -v`

  Run: `python3 -c 'import pathlib,yaml; [yaml.safe_load(p.read_text()) for p in pathlib.Path("templates").rglob("*.yaml")]'`

  Expected: EXIT=0。失败回退以单个模板包为边界，不改变其他模板的已通过结构。

- [ ] **Step 7: Lore 提交**

  提交六类 contract 与对应模板；不创建顶层 `workflows/`、`skills/` 空目录，因为尚无真实运行实现。

## 4. 阶段四：以 TDD 扩展结构检查器和正反例 fixture

**Files:**

- Modify: `linters/check_controlled_objects.py`
- Modify: `tests/test_check_controlled_objects.py`
- Create: `tests/test_operational_spine_checker.py`
- Create: `fixtures/checker-negative/stage-gate-missing-evidence/contracts/governance/stage-exit-gates-contract.yaml`
- Create: `fixtures/checker-negative/template-package-missing-file/templates/chain-package/README.md`
- Create: `fixtures/checker-negative/terminology-missing-term/docs/governance/TERMINOLOGY.md`
- Create: `fixtures/checker-negative/authority-broken-reference/project-os.yaml`
- Create: `fixtures/checker-negative/diagram-coverage-missing/templates/chain-package/chain.yaml`

- [ ] **Step 1: 写 C8—C12 正反例测试**

  - C8：阶段门禁九阶段和六组非空字段完整；反例缺 Evidence。
  - C9：六类模板包与 required files 完整；反例缺文件。
  - C10：术语权威含全部稳定 `term-id`，活动文档不自建第二份术语 manifest；反例缺关键 term。
  - C11：`project-os.yaml.authority`、contract refs 和 Markdown 权威路径可解析；反例引用不存在路径。
  - C12：P0/P1 链路声明的流程图、跨节点时序图、多状态状态图覆盖完整；反例缺图。

- [ ] **Step 2: 运行新增测试并逐条确认 RED**

  Run: `python3 -m unittest tests.test_operational_spine_checker -v`

  Expected: FAIL，首先因为 `check_c8_*` 至 `check_c12_*` 尚不存在。

- [ ] **Step 3: 最小实现 C8—C12**

  实现 `check_c8_stage_gate_contract`、`check_c9_template_packages`、`check_c10_terminology_authority`、`check_c11_authority_and_contract_references`、`check_c12_diagram_coverage`。使用稳定路径、字段和枚举，不以中文/英文自然语言关键词分流。`fixtures/checker-negative/` 是显式测试输入，主仓扫描跳过它们，测试则直接把每个目录作为 repo root 调用对应函数。

- [ ] **Step 4: 收紧 C4，不增加业务名豁免**

  删除具体 L2 名称和文件级豁免；允许 `{{l2_repo}}`、`{{project_id}}` 等结构化占位符；测试源码中的故意坏例子只在临时目录动态拼接，避免主仓自检把测试定义误判为生产污染。

- [ ] **Step 5: 运行 GREEN、全仓检查器和反例断言**

  Run: `python3 -m unittest tests.test_check_controlled_objects tests.test_operational_spine_checker -v`

  Run: `python3 linters/check_controlled_objects.py . --report`

  Expected: 正例全通过；五个负例分别只产生预期规则的门禁失败；全仓 P0=0/P1=0。若失败，保留失败测试，修正最小 checker 逻辑，不放宽 contract。

- [ ] **Step 6: Lore 提交**

  提交 checker、测试和负例 fixture；提交说明声明它证明静态结构门禁，不证明生产运行。

## 5. 阶段五：端到端 fixture、失败重开/暂停恢复与证据收口

**Files:**

- Create: `fixtures/operational-spine/positive/requirement.yaml`
- Create: `fixtures/operational-spine/positive/chain/chain.yaml`
- Create: `fixtures/operational-spine/positive/spec/spec.yaml`
- Create: `fixtures/operational-spine/positive/spec/tasks.yaml`
- Create: `fixtures/operational-spine/positive/workflow.yaml`
- Create: `fixtures/operational-spine/positive/skill.yaml`
- Create: `fixtures/operational-spine/positive/tool.yaml`
- Create: `fixtures/operational-spine/positive/run.yaml`
- Create: `fixtures/operational-spine/positive/evidence.yaml`
- Create: `fixtures/operational-spine/positive/verdict.yaml`
- Create: `fixtures/operational-spine/positive/claim.yaml`
- Create: `fixtures/operational-spine/positive/recovery.yaml`
- Create: `fixtures/operational-spine/negative/missing-reopen-target/recovery.yaml`
- Create: `tests/test_operational_spine_e2e.py`
- Create: `reviews/operational-spine-static-and-fixture-evidence.yaml`
- Modify: `README.zh-CN.md`
- Modify: `project-os.yaml`

- [ ] **Step 1: 写端到端追溯和恢复失败测试**

  测试要求每个 `*_ref` 精确解析到下一对象，Claim 的 scope/proof 不超过 Verdict，Evidence 绑定 Run，Run 绑定 Workflow/Task，Task 绑定 Spec/验收，Spec 绑定链路/需求；恢复记录必须证明 `failed → reopened_target` 或 `paused → resumed_from_checkpoint`。

- [ ] **Step 2: 运行测试并确认 RED**

  Run: `python3 -m unittest tests.test_operational_spine_e2e -v`

  Expected: FAIL，原因是正例 fixture 尚未建立或负例缺少 `reopen_target` 被拒绝。

- [ ] **Step 3: 建立最小纵向 fixture**

  使用匿名通用对象，固定链：Requirement → Chain Package → Spec → Task → Workflow → Skill/Tool → Run → Evidence → Verdict → Claim。所有对象使用稳定 ID/hash 占位值和明确 proof ceiling；不伪装真实 L2、真实外部调用或生产 Evidence。

- [ ] **Step 4: 建立失败重开或暂停恢复证明**

  正例记录一次 S6 契约失败重开 S4，并从 checkpoint 产生新 Run；负例缺 `reopen_target` 必须 fail closed。旧 Run/Evidence 保持不可变，新 Evidence 不能覆盖旧失败记录。

- [ ] **Step 5: 生成当前证据快照并校准声明**

  Evidence 快照记录 Git revision、命令、输入范围、文件 hash、测试数、checker 结果和已知缺口。`project-os.yaml` 只能把静态实现与 fixture proof 标为有证据；总体分仍为 `not_evaluated`，本地真实、只读真实和生产证明仍为 `not_evaluated`。保留跨项目隔离验证和第二异构 L2 为硬门禁。

- [ ] **Step 6: 运行全量新鲜验证**

  Run: `python3 -m unittest discover -s tests -v`

  Run: `python3 linters/check_controlled_objects.py . --report`

  Run: `python3 -c 'import json,pathlib,yaml; [yaml.safe_load(p.read_text()) for p in pathlib.Path(".").rglob("*.yaml") if "fixtures/checker-negative" not in str(p)]; [json.loads(p.read_text()) for p in pathlib.Path(".").rglob("*.json")]'`

  Run: Markdown 相对链接检查脚本（在测试中实现并通过 `python3 -m unittest tests.test_operational_spine_docs -v` 执行）。

  Run: `git diff --check`

  Run: `git status --short`

  Expected: 相关测试全部通过、YAML/JSON 可解析、Markdown 链接有效、checker P0=0/P1=0、diff check EXIT=0；状态中只允许 `.shopme/*` 无关修改和本任务待提交文件。

- [ ] **Step 7: 独立只读复核 P0/P1 与声明边界**

  复核者逐项检查设计验收条件、任务总树派生规则、contract/policy 单权威、E2E trace 和 Claim ceiling。任何 P0/P1 未关闭则不得提交完成；无法在当前范围关闭时明确记录 blocker，不把测试通过外推为生产就绪。

- [ ] **Step 8: Lore 提交**

  提交 fixture、证据、最终 README/project-os 校准。提交 `Tested:` 列出完整命令；`Not-tested:` 明确跨项目隔离、第二个异构 L2、真实本地/只读/生产运行尚未完成。

## 6. 最终声明上限与交付规则

- 可以声明：人类操作骨架、机器 stage gate contract、六类模板、静态检查器、正反例 fixture、单条匿名 E2E fixture 和失败重开/暂停恢复结构已在本地验证。
- 不可声明：当前总体评分 95+、通用跨项目已证明、第二异构 L2 已验证、本地真实运行已证明、只读真实预检已通过或生产就绪。
- 当前总体评分保持 `not_evaluated`；`95.93` 只写作批准方案 B 的目标设计分。
- `cross_project_isolation` 与 `second_heterogeneous_l2` 保持未满足硬门禁，不得由匿名 fixture 推导为已完成。
- 最终用户无需通过阅读测试或控制文件判断结果；主要验收入口是 `README.zh-CN.md`、`docs/architecture/AI_PROJECT_OS_OVERVIEW.md` 和 `docs/workflows/PROJECT_DELIVERY_WORKFLOW.md`。
- 无关 `.shopme/*` 修改保持原状并明确未提交。
