# 人工治理规则、AI 自动审核设计

## 1. 目标与适用范围

本设计把 AI Project OS 的通用审核模型调整为：人类提前定义、批准、发布和维护版本化 Markdown 规则；独立 AI 在运行期间依据已批准规则审核内容、证据、风险和质量；普通业务流程不等待人工逐条审核；只有规则治理、例外与高风险外部动作授权进入人工决定。

这是 L1 通用系统能力。L1 只定义对象、关系、状态、机器契约、门禁和模板，不包含项目类型、业务术语、固定回复或任何语言的关键词分流。L2/L3 提供具体规则正文、项目事实、运行记录和证据。

本设计只建立规范、机器契约、模板和静态检查能力，不声称已经实现模型调用、持久工作流运行器、本地真实运行或生产验证。

## 2. 设计决议

采用“契约优先的三类职责模型”：

1. 人工规则治理：人类批准规则、业务事实、需求、例外和高风险授权。
2. AI 自动审核：独立 AI 或确定性 gate 按已批准规则审核每个受控输出。
3. 高风险动作授权：人类只为不可逆外部动作、剩余风险接受和临时例外签发受限授权。

拒绝只修改术语而不增加机器约束，因为它无法阻止普通 Workflow 继续使用 `waiting_approval` 等待人工内容审核。拒绝在 L1 直接建设完整模型运行时，因为当前仓库成熟度是 `design_only`，且尚未锁定模型、存储或工作流依赖。

## 3. 三类职责的唯一语义

### 3.1 人工规则治理

人工治理对象包括：

- 版本化 Markdown 规则集；
- 批准事实与需求；
- 规则适用范围和优先级；
- 允许的例外与剩余风险；
- 不可逆外部动作授权；
- 规则替代、撤销和失效决定。

规则治理只在规则或授权发生变化时执行，不是逐条内容审核。AI 可以提出规则修订建议或创建规则缺口记录，但不得自行批准、发布、撤销或静默修改权威规则。

### 3.2 AI 自动审核

AI 自动审核适用于：

- 回复与生成内容质量；
- 事实、来源和 Evidence 支持；
- 隐私、敏感数据和秘密泄漏风险；
- 承诺、价格、时效和能力边界；
- 与项目事实、需求和已批准规则的一致性；
- 发布前内容规则；
- 多语言表达是否满足规则约束；
- Run、Evidence、Verdict 和 Claim 的语义完整性。

审核器必须与被审核输出的生成者在 `actor_id`、Run step 和 prompt/context role 上独立。相同基础模型可以在低风险场景承担不同角色，但必须有不同节点、提示、上下文和 attempt 记录；高风险场景由路由策略要求更强的模型、供应商或 gate 独立性。

每项审核发现必须引用精确的 `rule_ref`。不能只给出“看起来安全”“质量较好”或无规则来源的自由判断。

### 3.3 高风险动作授权

高风险授权只控制动作权限，不替代内容质量审核。以下事项保留人工决定：

- 不可逆真实发送、付款、删除和生产发布；
- 明确的安全、隐私或合规例外；
- 剩余风险接受；
- 规则集发布、撤销和紧急替换；
- 无法由已批准规则安全决定的授权升级。

AI 审核通过不自动产生 Capability Grant、Approval Ticket 或 Secret Lease。反之，人工授权存在也不能使违反规则的内容绕过 AI 审核。

## 4. 受控对象与机器契约

### 4.1 `governance_rule_set`

版本化 Markdown 规则集至少包含：

```yaml
rule_set_id: stable-id
version: 1
canonical_path: governance/rules/content-review.md
content_hash: sha256
scope:
  governance_scope: l3
  artifact_classes: [content, evidence]
rule_ids: []
status: draft
approved_by: human-principal-id
approved_at: timestamp-or-null
effective_from: timestamp-or-null
expires_at: timestamp-or-null
supersedes: null
```

状态使用 `draft/approved/active/superseded/revoked`。只有绑定人类 principal、非空规则列表、内容 hash、适用范围和有效期的 `active` 版本可驱动运行审核。

规则正文使用 Markdown，机器层只读取稳定规则 ID、结构化元数据和内容指纹。L1 不规定具体语言词面；L2/L3 可提供多语言规则正文或由权威规则生成的本地化阅读视图。

### 4.2 `ai_review_verdict`

AI 审核裁决至少包含：

```yaml
review_verdict_id: stable-id
subject_ref: stable-id/version/content-hash
generator_run_ref: run-id
review_run_ref: run-id
reviewer_actor_id: actor-id
reviewer_execution_node_ref: node-id/version
rule_set_ref: rule-set-id/version
rule_set_hash: sha256
finding_refs: []
evidence_refs: []
decision: pending
rewrite_attempt: 0
max_rewrite_attempts: 2
claim_ceiling: control_package
decided_at: timestamp
```

`decision` 使用：

- `pending`：输入、规则或审核尚不完整；
- `allow`：全部强制规则通过，可以进入下一节点；
- `rewrite_required`：发现可自动修复问题，进入有界改写循环；
- `blocked`：发现不可自动修复、禁止发布或高风险违规；
- `rule_gap`：现有规则不足以安全裁决，记录缺口并阻断当前输出。

每个 finding 至少包含 `finding_id`、`rule_ref`、`severity`、`subject_location`、`evidence_refs`、`explanation` 和 `recommended_action`。`allow` 必须有非空规则集、审核覆盖清单和审核 Evidence，禁止空集合真值。

### 4.3 `rule_gap_case`

规则缺口记录至少包含：

- 触发它的 subject、Run 和 Review Verdict；
- 不足以裁决的规则范围；
- 当前输出的安全处置；
- 影响范围和重复次数；
- 人类规则 owner；
- 修订期限和候选规则建议；
- 新规则发布后需要重开的对象闭包。

`rule_gap_case` 不把普通 Run 转为逐条人工内容审核。当前输出保持 blocked；人类异步完善规则，随后由新 Run 重新生成或重新审核。

## 5. 固定运行链路

```text
人工发布 active Markdown 规则集
  → AI 生成候选输出
  → 独立 AI 加载规则集、项目事实和 Evidence
  → 产生 ai_review_verdict
      ├─ allow → 进入后续确定性门禁
      ├─ rewrite_required → 自动改写 → 新审核 Run
      ├─ blocked → 安全终止并保存 Evidence
      └─ rule_gap → 创建 rule_gap_case → 安全终止
  → 若下一步包含不可逆副作用，再验证人工 authorization_snapshot
  → 执行动作或保持阻断
```

改写循环必须使用新 attempt 或新 Run，保存所有失败输出，不得只保留最佳结果。达到 `max_rewrite_attempts` 后仍不通过时转 `blocked`；不能转为 `waiting_approval` 请求人工逐条润色。

## 6. 状态与责任边界

公共 `work_status` 不新增内容审核专用枚举。`reviewing/rewrite_pending/blocked/rule_gap` 由 `ai_review_verdict.decision` 和类型专属状态表达，避免把审核细节污染所有受控对象。

`waiting_approval` 只适用于：

- 规则集发布或变更；
- 事实、需求和范围批准；
- 权限、例外和剩余风险接受；
- 不可逆外部动作授权。

普通内容、Evidence 和质量审核不得以 `waiting_approval` 作为默认或降级路径。

`human_decision` 收窄为规则治理、事实/需求批准、例外、剩余风险接受和不可逆动作授权。普通 Acceptance Verdict 由独立 AI 或确定性 gate 按已批准判据作出；若 Verdict 会直接触发高风险动作，动作仍需独立人工授权快照。

## 7. 失败与安全策略

- 规则集缺失、未批准、过期、hash 不匹配或 scope 不覆盖：`rule_gap` 或 `blocked`。
- 审核输出无法解析、Evidence 不足或 reviewer 身份不独立：`blocked`。
- 规则冲突：按规则集声明的优先级解决；优先级缺失时 `rule_gap`。
- 可修复内容问题：`rewrite_required`，受最大次数限制。
- 禁止项、安全风险或秘密泄漏：立即 `blocked`，不得通过改写掩盖原始 Evidence。
- reviewer、Tool 或模型失败：按预注册 retry policy 重试；预算耗尽后 `blocked`。
- 人工授权过期或输入 hash 改变：只阻断对应副作用，不回写 AI 审核为失败。

## 8. 权威文件与策略影响

实施必须同步以下现有权威面，保持同一语义：

- `docs/architecture/AI_PROJECT_OS_CORE.md`：把规则治理与 AI 审核加入薄内核控制/执行/证据平面。
- `docs/architecture/AI_NATIVE_EXECUTION_MODEL.md`：收窄 `human_decision`，定义独立 AI reviewer 节点。
- `docs/governance/CONTROLLED_OBJECT_MODEL.md`：增加三类对象、关系和不变量。
- `docs/governance/AUTHORIZATION_SIDE_EFFECTS_AND_ISOLATION.md`：分离内容审核与动作授权。
- `docs/governance/RUN_EVIDENCE_ACCEPTANCE.md`：加入 AI review 的 Run/Evidence/Verdict 绑定。
- `docs/governance/GATES_PROOF_SCORING.md`：增加规则引用、自动审核和有界改写门禁。
- `docs/governance/STATE_TRANSITIONS_AND_INVALIDATION.md`：限定 `waiting_approval`。
- `docs/workflows/ARCHITECT_WORKFLOWS.md`：把“人工审批”改为三类职责检查。
- `project-os.yaml` 与 `README.zh-CN.md`：增加权威入口和准确成熟度说明。

策略层新增规则集与 AI 审核契约，并调整 control set、routing、acceptance 和 authorization 契约。模板层增加通用 Markdown 规则包入口。历史 `reviews/` 只作为证据保留，不回写其结论。

重大架构语义变化必须新增 ADR，记录为何日常审核从人工等待改为基于已批准规则的 AI 独立审核。

## 9. 静态检查与测试

实施遵循 TDD，先加入失败测试，再扩展检查器。至少验证：

1. active 规则集有稳定 ID、非空规则、hash、scope 和人工批准身份。
2. `allow` Verdict 引用 active 规则集和至少一项审核覆盖 Evidence。
3. 每个 finding 引用可解析的精确 `rule_ref`。
4. generator 与 reviewer 不能是同一执行节点或同一 Run step。
5. `rewrite_required` 有正整数上限，达到上限后只能 blocked。
6. `rule_gap` 创建缺口记录并阻断当前输出。
7. 普通内容 Workflow 不得把 `waiting_approval` 作为审核节点或失败降级路径。
8. 不可逆外部动作仍要求有效人工授权快照。
9. 人工授权不能覆盖 AI 审核的 blocked Verdict。
10. 通用 L1 规则和检查器不得通过自然语言关键词分流业务场景。
11. P0/P1 任一发现都使检查器退出非零，消除当前“P1 仍 pass”的门禁矛盾。

测试只使用 synthetic、无 PII、无业务专用自然语言关键词的 fixture。不得把 fixture 通过解释为真实人工审核、真实发送或生产证明。

## 10. 评分与完成声明

本设计目标分为 96，但分层声明如下：

- 设计目标分：权威语义、契约和测试设计经独立反方复核后可评 95+。
- 实现分：只有检查器、契约解析和回归测试实际通过后才计算。
- 本地运行证明：需要 AI reviewer 运行器、真实模型指纹和有界改写 Run/Evidence。
- 通用 95+ 证明：需要至少两个业务和语言特征不同的 L2/L3 项目验证。
- 生产证明：需要经批准生产 Run、外部副作用回执、恢复和责任链，不属于本次设计优化。

缺少独立反方审计时不得超过 94；缺少异构真实项目验证时不得声称已经证明通用 95+。本次工作可以把设计和静态实现推进到 95+ 目标形态，但不能用文档或 fixture 冒充运行与生产证据。

## 11. 非目标

- 不在 L1 编写业务项目专用规则或固定回复。
- 不在代码中加入中文、英文或其他语言关键词判断。
- 不选择或锁定具体模型供应商。
- 不建设完整持久工作流平台。
- 不允许 AI 自行发布治理规则或扩大权限。
- 不移除不可逆外部动作的人工授权。
- 不修改历史审查 Evidence 来制造更高分数。
