---
stable_id: REQ-FUNC-001
object_type: requirement
requirement_kind: functional
function_id: FUNC-001
canonical_path: requirements/functions/FUNC-001_功能需求卡.md
version: 1
governance_scope: l2
lifecycle_stage: S2
priority: p1
work_status: in_progress
approval_status: pending
implementation_status: not_started
owner: human-template-owner
executor: ai-template-author
approver: human-template-owner
verifier: independent-template-reviewer
capability_refs: [CAP-001]
business_requirement_refs: [REQ-001]
business_chain_refs: [CHAIN-001]
scenario_refs: [SCENARIO-001]
intent:
  original_intent: "{{approved_source_or_original_intent_ref}}"
  interpreted_intent: "{{ai_candidate_interpretation}}"
  approved_intent: null
  implementation_intent: "{{candidate_implementation_intent}}"
context_snapshot_ref: CTX-DRAFT-001
baseline_ref: REQ-BASELINE-DRAFT-001
content_hash: "{{functional_requirement_content_hash}}"
supersedes: null
candidate_solution_status: candidate
spec_refs: []
output_contract_refs: ["{{output_contract_ref}}"]
stale_status: fresh
---

# 功能名称（FUNC-001）

## 一句话结论

说明调用方能够获得什么业务结果，不要先写技术方案。

## 为什么需要

说明本功能来自哪个批准业务 Requirement、业务链路节点和 Capability；解释缺失本功能会造成什么业务断点。

## 使用者与触发条件

- 使用者/调用方：`{{actor_or_consumer}}`
- 触发条件：`{{trigger}}`
- 前置状态：`{{precondition}}`

## 正常流程

```text
批准输入 → 业务判断/处理 → 结构化输出 → 下游验收或交接
```

## 异常、拒绝和恢复

分别说明业务不可用、权限阻断、执行失败、部分结果、未知状态和恢复入口。不要把这些状态混成一个 `failed`。

## 输入

```yaml
input_id: INPUT-001
subject_ref: "{{subject_ref}}"
request_context: {}
```

## 输出

- 主要业务输出：`{{business_output}}`
- 输出契约：`{{output_contract_ref}}`
- 下游消费者：`{{consumer_ref}}`

## 输出格式示例

```yaml
result_id: RESULT-001
business_status: accepted
execution_status: completed
reason_codes: []
next_action: continue
traceability_ref: REQ-FUNC-001
```

示例用于帮助人理解执行结果；正式字段由输出 Contract 唯一维护。

## 状态矩阵

| 业务状态 | 执行状态 | 含义 | 下游动作 |
|---|---|---|---|
| `available` | `completed` | 业务条件成立且执行完成 | 进入下游 |
| `unavailable` | `not_attempted` | 业务条件本身不成立 | 正常终止 |
| `available` | `failed` | 业务条件成立但执行失败 | 重试或修复 |
| `unknown` | `blocked` | 无法安全判断 | fail closed / 人工确认 |
| `available` | `partial` | 只获得部分结果 | 按契约决定是否交接 |

业务状态描述现实条件，执行状态描述本次动作结果，两者不得合并。

## 典型示例

- 正例：输入满足业务前置条件，输出通过 Contract 校验并可被下游消费。
- 反例：缺少批准事实或权限，却返回成功结果。
- 边界例：业务对象存在但本次执行超时，应表达 `available + failed`，不能伪装成业务不可用。

## 业务规则

- `implementation_intent` 不得扩大 `approved_intent`；
- 未批准需求不得进入 active Spec；
- 输出必须符合指定 Contract；
- 未知状态默认 fail closed；
- 生成视图和示例不能替代本卡或输出 Contract。

## 非目标与边界

明确不属于本功能的业务责任、下游动作和工程实现范围。

## 数据、权限与风险

说明输入数据分类、授权要求、外部副作用、项目隔离和责任边界。

## 验收方向

从业务结果、状态语义、输入输出和异常恢复判断功能是否正确；不能只检查文件存在、测试退出码或代码已经生成。

## 已批准实现约束

只保存已经由事实、规则或 ADR 批准的约束；未批准技术偏好不得写在这里。

## 候选实现要点

| 方案 | 优点 | 风险/限制 | 当前状态 |
|---|---|---|---|
| `OPTION-A` | `{{benefit}}` | `{{risk}}` | candidate |
| `OPTION-B` | `{{benefit}}` | `{{risk}}` | candidate |

候选方案不是批准要求。

## 方案选择入口

候选方案进入 Research/ADR。需求卡只固定各种方案都必须满足的业务结果、状态语义、边界和验收方向。

## 已有资产

列出可复用的 Contract、Workflow、Skill、Tool、代码、测试和现有 Proof，并明确各自证明边界。

## 未知与待确认

每个 Unknown 写明 owner、影响、是否 `blocks_decision`、研究入口和期限。

## 上下游影响

上游：业务 Requirement、Chain、Capability、Function。下游：ADR、Spec、Task、Test、Workflow、Evidence、Verdict 和 Claim。

## AI 生成自检

- 缺少哪些必要信息；
- 使用了哪些假设；
- 哪些结论最可能错误；
- 哪些内容需要人类确认；
- 是否把内部判断步骤错误提升为顶层 Function；
- 是否把候选方案冒充批准要求；
- 是否与上游或已有功能冲突。

## Spec 映射

人工批准并写入 Requirement Baseline 后，再记录一个或多个 Spec。Spec 必须精确引用本卡 `stable_id/version/content_hash` 与当前 baseline；本模板初始 `spec_refs: []`。
