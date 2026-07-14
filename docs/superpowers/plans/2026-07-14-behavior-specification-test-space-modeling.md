# Behavior Specification + Test Space Modeling 实施计划

> **Status:** implemented_pending_final_independent_audit

> **Goal:** 在不增加生命周期阶段的前提下，让 L2 在 S2 形成行为规格/稳定案例，在 S4 从批准语义清单派生可检查测试空间，在 S5 由 Spec/Task/Test 引用案例，并把实际结果严格留在 S6。
>
> **Design authority for this change:** `docs/superpowers/specs/2026-07-14-行为规格与测试空间建模设计.md`
>
> **Execution rule:** 测试先行；每个生产修改前必须先观察对应测试以预期原因失败。不得修改只读 L2 仓库，不得触碰或提交当前无关 `.gitignore` / `.shopme` 变化。

## Task 1：锁定术语、阶段责任与证明边界

**测试文件：**
- Modify: `tests/test_l2_progression_document.py`
- Modify: `tests/test_operational_spine_docs.py`

**实现文件：**
- Modify: `docs/governance/TERMINOLOGY.md`
- Modify: `project-os.yaml`
- Modify: `docs/workflows/PROJECT_DELIVERY_WORKFLOW.md`
- Modify: `docs/workflows/L2_PROGRESSION.md`
- Modify: `docs/workflows/STAGE_EXIT_GATES.md`
- Modify: `docs/governance/STATE_TRANSITIONS_AND_INVALIDATION.md`

1. 先添加失败测试，断言稳定 term-id、S2/S3/S4/S5/S6 分层、可选 As-Is/To-Be、稳定案例 ID 和 Run/Evidence 隔离。
2. 运行：`python3 -m unittest tests.test_l2_progression_document tests.test_operational_spine_docs -v`，确认因缺少新语义 RED。
3. 最小修改现有权威文件；不新增生命周期阶段或第二份主题权威。
4. 重新运行同一测试至 GREEN。

## Task 2：锁定 chain/spec v2 模板和机器表格

**测试文件：**
- Modify: `tests/test_template_packages.py`

**实现文件：**
- Modify: `templates/chain-package/README.md`
- Modify: `templates/chain-package/chain.yaml`
- Modify: `templates/chain-package/scenarios.md`
- Modify: `templates/chain-package/acceptance.md`
- Modify: `templates/chain-package/traceability.md`
- Modify: `templates/spec-package/README.md`
- Modify: `templates/spec-package/spec.md`
- Modify: `templates/spec-package/tasks.md`
- Modify: `templates/spec-package/acceptance.md`
- Modify: `templates/spec-package/traceability.md`
- Modify: `contracts/artifacts/chain-package-contract.yaml`
- Modify: `contracts/artifacts/spec-package-contract.yaml`

1. 先添加失败测试，断言 Contract major v2、显式 `contract_ref`、唯一 Markdown registry/matrix、精确列名/枚举/主键、执行后字段禁止、S5 `behavior_case_refs` 和四个 validation profile。
2. 加入合成中立 inventory 的 CA₂ 测试：验证 `A×P`、`A×K`、`P×K` 全覆盖和由当前输入动态得到的下限；测试数据不得出现任何 L2 项目词面或固定业务门槛。
3. 运行：`python3 -m unittest tests.test_template_packages -v`，确认 RED。
4. 最小更新模板与两个 Contract；L1 只使用通用 boundary/inventory/dimension 占位符。
5. 重新运行同一测试至 GREEN。

## Task 3：让控制对象 checker 执行 v2 Markdown/profile 约束

**测试文件：**
- Modify: `tests/test_operational_spine_checker.py`
- Add/Modify only if needed: `tests/fixtures/checker/*`

**实现文件：**
- Modify: `linters/check_controlled_objects.py`

1. 先添加失败测试，覆盖缺表、列漂移、重复主键、禁用执行字段、错误 profile/contract 组合、未解析 canonical ref 和 profile 继承失败。
2. 运行：`python3 -m unittest tests.test_operational_spine_checker -v`，确认每类失败均由缺少 checker 能力触发。
3. 在 C9 内复用现有 package validation，增加通用 Markdown table parser 与 contract-driven 规则，不加入业务关键词或新依赖。
4. 返回稳定错误语义，未知 schema/规则 fail-closed；重新运行至 GREEN。

## Task 4：迁移 L1 正例 fixture 到 package contract v2

**实施决策更新：** 未改写现有正例 fixture。它继续作为真实 `@1` 历史只读样本，由 `historical_read_v1` shape 解析；新的 S2/S4/S5 门禁只接受 `@2`。这比把历史样本就地迁移更能锁住兼容边界，也避免重算并改写旧 hash 链。另用临时渲染的 v2 chain/spec package 测试当前 stage exit、动态覆盖和跨包引用。

**测试文件：**
- Existing: `tests/test_operational_spine_e2e.py`
- Existing: `tests/test_operational_spine_checker.py`

**实现/fixture 文件：**
- Modify: `fixtures/operational-spine/positive/control-set.yaml`
- Modify: only hash-bound files under `fixtures/operational-spine/positive/` required by canonical hash propagation

1. 在 Contract 升级后先运行 E2E，观察 `@1/@2` 或 canonical hash 预期失败。
2. 将控制集的 chain/spec 引用升级为 `@2`，重算其 canonical content hash。
3. 只更新直接绑定该 hash 的 L1 fixture；不得改写历史 Run 语义或扩大 proof level。
4. 运行：`python3 -m unittest tests.test_operational_spine_e2e tests.test_operational_spine_checker -v` 至 GREEN。

## Task 5：定向验证、全量验证与污染扫描

1. 定向测试：
   `python3 -m unittest tests.test_l2_progression_document tests.test_operational_spine_docs tests.test_template_packages tests.test_operational_spine_checker tests.test_operational_spine_e2e -v`
2. 控制对象检查：
   `python3 linters/check_controlled_objects.py . --report`
3. Python 静态解析：
   `python3 -m py_compile linters/check_controlled_objects.py`
4. 全量测试：
   `python3 -m unittest discover -s tests -v`
5. YAML/Markdown、diff 与 L1 去污染：解析所有修改 YAML；`git diff --check`；扫描模板、Contract、Python/JS 不含只读 L2 项目名、具体语言词面或业务 selector 分流。
6. 只读复算 L2 当前 inventory，记录当次动态基础下限；必要时重跑其现有组件测试，但不修改文件。若提示词计数与当前配置不同，以当前配置和选择器门禁为准。
7. 再执行两个仓库的 `git status --short`，证明 L2 零写入并区分原有无关脏文件。

## Task 6：实施后独立自动专家复核

1. 将最终 diff、测试输出、Contract v2、checker 和证明边界交给独立 AI 子代理只读审计。
2. 按相同 100 分 rubric 记录 P0/P1/P2、输入 hash、可复现命令和 claim limits。
3. 若有 P0 或核心维度未达标，回到对应 TDD Task 修复并重验；只有 P0=0 且总分 >=95 才报告本次变更审计 95+。

## 提交策略

本任务不自动创建提交：当前 index 已包含与本任务无关的 `.shopme` 删除，直接提交有夹带风险。完成时提供精确修改清单和验证证据；如用户后续要求提交，再使用路径级暂存与 Lore Commit Protocol。
