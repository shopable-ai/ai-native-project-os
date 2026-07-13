# Run、Evidence、验收裁决与完成声明

本文件是 Run、Evidence、Acceptance Verdict 和 Completion Claim 最小语义的唯一权威源；Run 与 Evidence 的机器字段由 [run-evidence-contract](../../contracts/governance/run-evidence-contract.yaml) 固定，Acceptance Verdict 与 Completion Claim 的机器字段和不变量由 [acceptance-verdict-claim-contract](../../contracts/governance/acceptance-verdict-claim-contract.yaml) 固定。

## 1. 固定顺序

```text
事前规则与验收判据 → 审核策略包与预注册测试集
→ 认证 Run/Evidence → Certification Verdict 与激活路由
→ 生成 Run → AI 审核 Run/Evidence → AI Review Verdict
→ 验收 Evidence → Acceptance Verdict → Completion Claim
```

验收判据在执行前批准；Run 记录发生了什么；Evidence 保存可复现观察；Verdict 由责任主体依据判据和 Evidence 作出；Claim 只能基于有效 Verdict 签发。`EXIT=0` 只是进程级必要条件。

以下 Run、Evidence、Verdict 和 Claim 示例都 `extends: controlled_object_base/v1`，必须合并受控对象模型中的稳定 ID、scope、生命周期、工作、审批、实现、失效和责任字段。类型专属字段不能覆盖公共坐标。

## 2. 最小 Run

```yaml
extends: controlled_object_base/v1
run_id: run_YYYYMMDD_HHMMSS_suffix
project_id: project-id
route_decision_ref: route-id
control_set_ref: control-set-id
control_set_hash: sha256
workflow_ref: workflow-id
workflow_version: version
spec_and_task_refs: []
input_fingerprints: []
code_fingerprint: sha256
dependency_fingerprint: sha256
config_fingerprint: sha256
model_fingerprints: []
prompt_fingerprints: []
context_fingerprints: []
tool_fingerprints: []
policy_fingerprints: []
governance_rule_set_refs: []
review_mode: not_applicable
executor: actor-id
environment: environment-id
started_at: timestamp
finished_at: timestamp
exit_code: 0
execution_outcome: success
semantic_result: passed
checkpoint: null          # null 或严格的 checkpoint 引用
approval_and_permission_refs: []
attempt_manifest: []
fallback_events: []
evidence_refs: []
uncovered_scope: []
known_failures: []
```

`execution_outcome` 使用 `success/failure/partial/unknown`，表达执行器是否完成；`semantic_result` 使用 `passed/failed/partial/unknown/not_evaluated`，表达 Run 内预注册语义断言的执行者观察。二者都不等于验收通过。Run 完成后由 Evidence 独立验证 criterion result，再由 Verdict 决定是否接受。Run 历史不可改写；重试创建新 Run 并引用原 Run。

`checkpoint` 为 null 或引用包含 `checkpoint_id`、Run/Workflow/版本、step cursor、状态和输入指纹、已完成/待处理副作用、审批/权限、外部回执、时间、内容 hash、恢复兼容范围和 `consumed_by_run` 的受控记录。恢复创建新 Run，不能把原 Run 原地继续为成功。

`attempt_manifest` 不可变地列出全部模型、Tool、重试、超时和被拒绝输出，不能只保存最佳结果。每个 `fallback_event` 记录节点、正常/降级路径及版本、触发原因、丢失能力和 effective claim ceiling；缺少降级遥测或出现未知路径时，上限降为 `control_package`。

## 3. 最小 Evidence

```yaml
extends: controlled_object_base/v1
evidence_id: evidence-id
project_id: project-id
route_decision_ref: route-id
control_set_hash: sha256
subject_refs: []
run_ref: run-id
proof_level: control_package
criterion_results: []
artifact_refs: []
content_and_environment_fingerprints: []
collector: actor-or-tool
captured_at: timestamp
expires_at: timestamp-or-null
verification_status: verified
stale_status: fresh
uncovered_scope: []
evidence_selection_policy: policy-id
ai_review_verdict_ref: null
included_attempt_refs: []
excluded_attempts_and_reasons: []
```

每个 `criterion_result` 记录 `criterion_id`、期望、观察、pass/fail、验证命令和原始 Evidence 引用。总结不得替代原始输出；截图不得替代可机器读取结果（除非对象本身是视觉行为）。

Evidence 必须验证 attempt manifest 完整性并说明所有排除项。关键评测的抽样和选择规则必须在 Run 前注册；原始输出使用内容 hash 和 append-only custody 记录，执行者不得选择性丢弃失败尝试。`verification_status` 只使用 `captured/verified/rejected`；新鲜度、过期和失效只使用公共 `stale_status`。

## 4. 审核策略认证 Run、Evidence 与 Verdict

审核策略认证 Run 必须在执行前绑定完整策略包和测试集：

```yaml
review_mode: independent_ai_review
review_policy_bundle_fingerprints:
  rule_set_hash: sha256
  prompt_template_hash: sha256
  input_schema_hash: sha256
  output_schema_hash: sha256
  context_policy_hash: sha256
  model_fingerprint: model/revision/parameters
  tool_set_hash: sha256
  permission_set_hash: sha256
review_policy_test_suite_refs: [review-policy-test-suite-id/version]
review_policy_certification_refs: [review-policy-certification-id/version]
attempt_manifest: []
```

每个非确定性 case 按预注册次数生成 attempt。Evidence 使用 `included_attempt_refs` 和 `excluded_attempts_and_reasons` 对账全部 attempt；排除项必须写明原因并仍留在指标分母中，不能只保留最佳输出或只展示成功 Run。

认证 Verdict 同时绑定策略包/test suite 版本与 hash、全部 Run/Evidence、`metric_results`、`threshold_results`、独立 verifier、未覆盖范围、有效期和失效条件。任何必需阈值失败、attempt 缺失、hash 不匹配、verifier 不独立或 scope 不匹配，都不能签发可用于 `policy_certified` 的结论。

认证只允许激活 Policy 选择 `policy_certified`、`human_signoff` 或 blocked。它不授予 Capability Grant、Approval Ticket、Secret Lease 或外部动作权限，也不证明真实模型在未测试输入或生产环境中的表现。

## 5. AI Review Verdict

AI 审核裁决的机器字段只由 `contracts/governance/ai-review-verdict-contract.yaml` 定义。它必须精确绑定被审核对象/hash、生成 Run、独立审核 Run/节点、reviewer 模型指纹、active 规则集/hash、逐规则结果、finding 和 Evidence。

```yaml
extends: controlled_object_base/v1
review_verdict_id: ai-review-verdict-id
subject_ref: stable-id/version
subject_hash: sha256
generator_run_ref: run-generator-id
review_run_ref: run-reviewer-id
reviewer_actor_id: reviewer-actor-id
reviewer_execution_node_ref: reviewer-node-id/version
rule_set_ref: governance-rule-set-id/version
rule_set_hash: sha256
rule_results: []
finding_refs: []
evidence_refs: []
evidence_hashes: []
decision: pending
rewrite_attempt: 0
max_rewrite_attempts: 2
claim_ceiling: control_package
decided_at: null
```

`allow` 需要非空规则覆盖和审核 Evidence；`rewrite_required` 创建新 attempt/Run 并重新审核；`blocked` 阻止发布和副作用；`rule_gap` 按 `contracts/governance/rule-gap-case-contract.yaml` 创建规则缺口记录并阻断当前对象。普通内容审核不得转 `waiting_approval`。人工授权不能覆盖 `blocked/rule_gap`，审核通过也不能替代动作授权。

## 6. Overlay Activation Verdict

叠加能力激活裁决的机器字段只由 `contracts/governance/overlay-activation-verdict-contract.yaml` 定义。其 subject 必须是具体 overlay module 与 control set 版本/hash，只回答“该控制模块能否在指定环境激活”。它在路由 v1（selected、未 enabled）下通过隔离测试产生 Evidence，接受后由新路由 v2 引用 `overlay_activation_verdict_ref` 并把 `enabled` 改为 true。它不能接受业务需求、签发业务完成声明或替代生产证明。

## 7. 最小 Acceptance Verdict

```yaml
extends: controlled_object_base/v1
verdict_id: verdict-id
project_id: project-id
route_decision_ref: route-id
overlay_status_snapshot_ref: route-id#overlays
overlay_status_snapshot_hash: sha256
control_set_ref: control-set-id
control_set_hash: sha256
subject_refs: []          # stable_id/version/content_hash
requirement_baseline_id: baseline-id
subject_and_scope: description
criteria_refs: []
evidence_refs: []
evidence_hashes: []
ai_review_verdict_refs: []
ai_review_verdict_hashes: []
environment_and_input_class: description
approval_and_permission_snapshot_refs: []
approval_and_permission_snapshot_hashes: []
decision: pending
claim_ceiling: control_package
conditions: []
expires_at: timestamp-or-null
decided_by: independent-ai-or-deterministic-gate
decided_at: timestamp
signature_ref: signature-id
reason: description
```

`decision` 为 `pending/accepted/rejected/conditional/revoked`。`conditional` 必须列责任人、期限和禁止声明，且不能绕过 P0/P1、安全、隐私、不可逆副作用或生产证明门禁。

Verdict 必须精确绑定对象版本/hash、需求基线、判据版本、Evidence hash、适用的 AI Review Verdict/hash、环境/输入类别、治理路由中的 overlay 状态快照、control set 和权限快照。普通 Acceptance Verdict 可以由独立 AI 或确定性 gate 依据已批准规则与判据作出，不要求人工逐条验收；规则、事实和需求使用 `policy_certified` 或 `human_signoff` 的合法 Decision Gate，例外、剩余风险和不可逆动作仍保留人工治理。任一 `required: true` 但 `enabled: false` 的叠加能力必须降低 claim ceiling 或阻断裁决。

存在 `execution_outcome: unknown` 的外部副作用时必须建立对账记录，包含 owner、外部标识、查询 Evidence、影响范围和期限；在独立 Evidence 证明最终状态前，Verdict 不得为 `accepted`，依赖动作保持 blocked。

## 8. Completion Claim

```yaml
extends: controlled_object_base/v1
claim_id: claim-id
claim_status: draft
subject_refs: []          # stable_id/version/content_hash
requirement_baseline_id: baseline-id
scope: {}
environment: environment-id
input_classes: []
route_decision_ref: route-id
overlay_status_snapshot_ref: route-id#overlays
overlay_status_snapshot_hash: sha256
control_set_ref: control-set-id
control_set_hash: sha256
proof_level: control_package
verdict_ref: verdict-id
evidence_hashes: []
ai_review_verdict_refs: []
ai_review_verdict_hashes: []
approval_and_permission_snapshot_refs: []
approval_and_permission_snapshot_hashes: []
verification_commands: []
issued_by: authorized-policy-or-human
issued_at: timestamp
expires_at: timestamp
uncovered_scope: []
prohibited_extrapolations: []
```

Claim 必须包含对象稳定 ID/版本/hash、需求基线、范围、环境/输入类别、`route_decision_ref`、overlay 状态快照、`control_set_hash`、proof_level、Acceptance Verdict、AI Review Verdict/hash、Evidence hash、权限快照、验证命令、签发主体、时间、有效期、未覆盖边界和禁止外推范围。日常 Claim 可由满足契约的授权策略签发；人类不是逐条签发的默认前置条件。Claim 上限为关键路径最低有效 proof_level、Verdict `claim_ceiling` 和所有节点降级上限三者的最小值。

Run 成功但必需判据失败、Evidence 不新鲜、Verdict 未接受、审批过期或存在未关闭 P0/P1 时，不得签发 Claim。Evidence 失效或 Verdict 撤销必须使 Claim `withdrawn/expired`。
