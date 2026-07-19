# 审核策略认证与条件式决策门实施计划

**目标：** 在 `agent/capability-function-pilot` 最新基线上，把固定人工批准修正为风险自适应决策门，并建立审核策略测试、认证、激活、失效和重开静态闭环。

**架构：** 复用现有 Governance Rule Set、AI Review Verdict、Rule Gap、Run/Evidence、状态失效和授权协议；新增测试集 Contract、认证 Contract 和激活路由 Policy。Prompt 只装配规则。低风险对象可由有效认证策略自动决策，高风险变化和不可逆动作保留人工确认/授权。

**约束：** 中文为面向人的第一语言；不创建新分支；不安装第三方运行依赖；不建设完整审核平台；当前总分保持 `not_evaluated`；任何 P0/P1、正反例漏检或并行分支漂移都阻断完成提交。

## 0. 基线审计与既有失败关闭

**远端基线：** `agent/capability-function-pilot@c060ebc`，相对 `main` ahead 2 / behind 0。

**已确认可复用：**

- Capability 卡、Function 需求卡和映射指南；
- Draft/Approved Baseline 与 Context 分离；
- C13 Capability/Function 专用检查器；
- 人工治理规则、AI 自动审核、有界改写和 Rule Gap 契约。

**必须先修复的既有失败：**

- `templates/standard-project/requirements/README.md` 缺契约要求的完整相对路径文本，导致 6 个模板测试失败；
- `tests/test_capability_function_mapping.py` 中测试 YAML 被主检查器误识别为正式 stable ID，导致 C1 P0=2。

**文件：**

- Modify: `templates/standard-project/requirements/README.md`
- Modify: `tests/test_capability_function_mapping.py`

**测试：** 全量 unittest、主检查器、C13 检查器。

**失败回退：** 只调整 README 导航和测试字符串表达，不改变远端分支新增对象语义。

**提交边界：** 单独 Lore 提交，明确这是关闭继承失败，不冒充本次新能力。

## 1. 保存认证权威与机器注册

**文件：**

- Create: `docs/governance/REVIEW_POLICY_CERTIFICATION.md`
- Modify: `docs/architecture/AI_NATIVE_EXECUTION_MODEL.md`
- Modify: `docs/governance/CONTROLLED_OBJECT_MODEL.md`
- Modify: `docs/governance/TERMINOLOGY.md`
- Modify: `docs/workflows/STAGE_EXIT_GATES.md`
- Modify: `project-os.yaml`
- Modify: `AGENTS.md`, `README.md`
- Test: `tests/test_review_policy_certification.py`

**步骤：**

1. 先写失败测试：新权威被 `project-os.yaml` 注册；术语只有一处定义；approval route 不成为新状态轴；Prompt 不是规则权威。
2. 用中文定义审核策略包、测试类别、多轮指标、认证 Verdict、风险路由和失效传播。
3. 把固定 `Human Approval` 改为 Decision Gate 的人类视图，但保留 human_signoff 的高风险边界。
4. 同步 README/AGENTS 入口，不复制机器枚举。

**失败回退：** 若条件式路由无法与既有 approval_status 正交，保留原字段并撤销新术语注册，不修改历史 Evidence。

**提交边界：** 只提交权威文档、入口和权威测试。

## 2. 建立测试、认证与激活路由契约

**文件：**

- Create: `contracts/governance/review-policy-test-suite-contract.yaml`
- Create: `contracts/governance/review-policy-certification-contract.yaml`
- Create: `policies/review-policy-activation-routing.yaml`
- Modify: `contracts/governance/governance-rule-set-contract.yaml`
- Modify: `contracts/governance/stage-exit-gates-contract.yaml`
- Modify: `contracts/governance/run-evidence-contract.yaml`
- Modify: `project-os.yaml`
- Modify: `contracts/README.md`, `policies/README.md`
- Test: `tests/test_contract_policy_boundaries.py`
- Test: `tests/test_review_policy_certification.py`

**步骤：**

1. Test Suite Contract 固定 case 预期、类别、repeat、metrics、thresholds 和版本/hash。
2. Certification Contract 固定策略包 hash、Run/Evidence、独立 verifier、结果、ceiling、有效期和失效条件。
3. Activation Policy 只保存风险路由决策，不承载结构字段定义。
4. Rule Set 的 active 条件改为 `policy_certified | human_signoff` 二选一；AI 自认证、阈值降低自动激活和 scope 扩大自动激活必须 fail closed。

**失败回退：** 两个新 Contract 与 Policy 作为一个原子边界；注册或引用不完整时整体不提交，绝不留下双权威。

**提交边界：** 只提交 Contract/Policy、注册、边界测试和导航。

## 3. 修正需求与 Baseline 的固定人工批准

**文件：**

- Modify: `docs/workflows/REQUIREMENT_DESIGN_WORKFLOW.md`
- Modify: `docs/governance/CAPABILITY_FUNCTION_SPEC_MAPPING.md`
- Modify: `contracts/artifacts/requirement-design-package-contract.yaml`
- Modify: `templates/standard-project/requirements/README.md`
- Modify: `templates/standard-project/requirements/functions/FUNC-001_功能需求卡.md`
- Modify: `templates/standard-project/requirements/baselines/REQ-BASELINE-DRAFT-001.yaml`
- Modify: `templates/standard-project/requirements/context/CTX-DRAFT-001.yaml`
- Modify: `linters/check_capability_function_mapping.py`
- Modify: `tests/test_capability_function_mapping.py`

**步骤：**

1. 先把“approved 必须 human”测试改为“approved 必须有合法 decision route”。
2. 模板增加 `approval_route`、`decision_authority_ref`、`certification_verdict_ref`，但 approved fixture 不伪装为复制后的新项目状态。
3. C13 接受有效 policy_certified 或 human_signoff；拒绝 AI 自认证、缺 Verdict、风险路由不匹配和未决 Unknown。
4. Spec 仍只消费当前 Baseline 中精确版本/hash；自动决策不削弱意图一致性和失效传播。

**失败回退：** 保留 Capability/Function/Spec 映射与 Draft/Approved 分离；只回退新的决策路由字段和检查逻辑。

**提交边界：** 需求权威、模板、C13 与正反测试一起提交。

## 4. 建立可复制认证模板与正反例

**文件：**

- Create: `templates/standard-project/governance/review-certification/审核策略包说明.md`
- Create: `templates/standard-project/governance/review-certification/审核策略测试集.yaml`
- Create: `templates/standard-project/governance/review-certification/审核策略激活策略.yaml`
- Create: `fixtures/review-policy-certification/positive/*`
- Create: `fixtures/review-policy-certification/negative/*`
- Modify: `templates/standard-project/README.md`
- Modify: `templates/README.md`
- Modify: `linters/check_controlled_objects.py`
- Test: `tests/test_review_policy_certification.py`
- Test: `tests/test_operational_spine_checker.py`
- Test: `tests/test_template_packages.py`

**正例：**

- 低风险策略完整测试后 policy_certified；
- 高风险策略测试通过但路由 human_signoff；
- Rule Gap 通过新规则、新认证和新 Run 重开。

**反例至少覆盖：**

- 缺 positive/negative/boundary/adversarial 类别；
- 非确定性 reviewer 只有一次运行；
- reviewer 自认证；
- Prompt/model/context/schema hash 漂移仍使用旧认证；
- 阈值降低或 scope 扩大自动激活；
- 测试失败仍 active；
- 认证通过后越权获得外部动作权限。

**失败回退：** 模板、fixture、C14 检查规则和测试作为一个提交边界；不得保留无检查器消费的空模板。

**提交边界：** 声明只证明静态认证闭环，不证明真实模型多轮表现。

## 5. 失效传播、证据与最终校准

**文件：**

- Modify: `docs/governance/STATE_TRANSITIONS_AND_INVALIDATION.md`
- Modify: `docs/governance/RUN_EVIDENCE_ACCEPTANCE.md`
- Create: `reviews/review-policy-certification-static-evidence.yaml`
- Modify: `reviews/current-score-status.yaml`
- Modify: `project-os.yaml`, `README.md`
- Extend: `tests/test_review_policy_certification.py`

**步骤：**

1. 绑定规则、Prompt、模型、Schema、Context、测试集、指标与阈值 hash 的失效传播。
2. Evidence 保存全部重复尝试、排除项和指标结果；禁止选择性丢弃失败输出。
3. 分开报告静态、fixture、真实模型、本地真实、只读真实和生产证明。
4. 当前总体评分继续为 `not_evaluated`；真实多轮模型、真实 L2、跨项目和生产继续作为硬门禁。

**最终验证：**

- `python3 -m unittest discover -s tests -v`
- `python3 linters/check_controlled_objects.py . --report`
- `python3 linters/check_capability_function_mapping.py templates/standard-project`
- 全部有效 YAML/JSON 解析
- Markdown 相对链接测试
- `python3 -m py_compile linters/*.py tests/*.py`
- `git diff --check`
- 重新读取远端 `agent/capability-function-pilot` HEAD，确认没有并行漂移

**失败回退：** P0/P1、反例未被拒绝、远端分支新增未知提交或证据范围不一致时不得更新远端。

**提交边界：** Evidence、评分边界和 README 校准单独提交；`Not-tested` 明确真实模型、真实人工、真实 L2 与生产均未证明。

## 6. 发布规则

- 所有远端提交直接进入 `agent/capability-function-pilot`，不创建第三层分支；
- 每阶段独立 Lore 提交；
- 写入远端前再次比较 `c060ebc..branch HEAD`，并把并行变化整合到当前阶段，而不是 force push；
- 不修改 `main`，不创建 PR，除非用户另行指示；
- 完成报告先列实际能力、仍不能做什么和用户是否需要操作，再列工程证据。
