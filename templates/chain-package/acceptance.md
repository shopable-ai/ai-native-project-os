# 验收判据

## Test Space Model

| `test_space_id` | `behavior_spec_ref` | `semantic_inventory_ref` | `inventory_hash` | `inventory_partition_refs` | `inventory_members_json` | `coverage_obligations_json` | `dimension_refs` | `dimension_domains_json` | `forbidden_assignments_json` | `constraints` | `generator_kind` | `interaction_strength` | `generation_budget` | `upgrade_triggers` | `uncovered_scope` |
|---|---|---|---|---|---|---|---|---|---|---|---|---:|---:|---|---|
| `{{test_space_id}}` | `{{behavior_spec_ref}}` | `{{semantic_inventory_ref}}` | `{{inventory_hash}}` | `{{inventory_partition_refs}}` | `{"{{inventory_partition_ref}}":["{{inventory_member_ref}}"]}` | `[{"obligation_id":"{{coverage_obligation_id}}","scope":"per_member","partition_refs":["{{inventory_partition_ref}}"],"required_relation":"{{case_relation}}"}]` | `{{dimension_refs}}` | `{"{{dimension_id}}":["{{dimension_value}}"]}` | `[]` | `{{combination_constraints}}` | `{{generator_kind}}` | `{{interaction_strength}}` | `{{generation_budget}}` | `{{upgrade_triggers}}` | `{{uncovered_scope}}` |

测试空间必须从已批准且带版本/hash 的 inventory 动态派生。AI 可以生成候选反例，不得批准新的业务语义。`pairwise` 必须验证全部允许二元组合；安全、授权、不可逆副作用、已知交互缺陷、未知/冲突约束或预算内可承受时升级为受约束全组合。

## Derived Combination Registry

| `combination_id` | `test_space_ref` | `dimension_assignment_json` | `source_inventory_members` | `derivation_status` |
|---|---|---|---|---|
| `{{combination_id}}` | `{{test_space_id}}` | `{"{{dimension_id}}":"{{dimension_value}}"}` | `{{source_inventory_members}}` | `{{derivation_status}}` |

`inventory_members_json` 与 `coverage_obligations_json` 把 L2 批准 inventory 的成员及 `per_partition`/`per_member` 义务绑定为通用机器输入；具体义务名称和语言例句只存在于 L2。`dimension_domains_json` 与 `dimension_assignment_json` 是机器重算面；`forbidden_assignments_json` 只允许由维度名和值组成的通用禁配列表。任何 inventory/hash 变化都必须重新生成本表并检查全部义务和允许二元组合，不能保留手工抽样计数。

## Acceptance Coverage Matrix

| `coverage_id` | `behavior_case_ref` | `semantic_inventory_ref` | `inventory_partition_refs_json` | `inventory_member_refs_json` | `obligation_refs_json` | `equivalence_class_or_boundary` | `combination_constraints` | `case_relations` | `case_relation` | `input_boundary` | `governed_intermediate_boundary` | `expected_transition_or_decision` | `observable_output_boundary` | `boundary_binding_profile` | `verification_method` | `minimum_proof_scope` | `coverage_status` |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| `{{coverage_id}}` | `{{behavior_case_ref}}` | `{{semantic_inventory_ref}}` | `["{{inventory_partition_ref}}"]` | `["{{inventory_member_ref}}"]` | `["{{coverage_obligation_id}}"]` | `{{equivalence_class_or_boundary}}` | `{{combination_constraints}}` | `{{case_relations}}` | `{{case_relation}}` | `{{input_boundary}}` | `{{governed_intermediate_boundary}}` | `{{expected_transition_or_decision}}` | `{{observable_output_boundary}}` | `{{boundary_binding_profile}}` | `{{verification_method}}` | `{{minimum_proof_scope}}` | `{{coverage_status}}` |

`coverage_status` 只能使用 `planned`、`implemented_unverified`、`verification_mapped`、`not_applicable` 或 `blocked`；它不是执行结果。`not_applicable` 必须附 owner、理由和重开条件。

## Failure Recovery Oracle

仅 `failure_recovery` coverage row 必填；这些字段仍是事前 oracle。

| `coverage_ref` | `pre_failure_state` | `failure_terminal` | `recovery_action` | `post_recovery_invariants` | `idempotency_or_side_effect_oracle` | `compensation_ref` |
|---|---|---|---|---|---|---|
| `{{coverage_ref}}` | `{{pre_failure_state}}` | `{{failure_terminal}}` | `{{recovery_action}}` | `{{post_recovery_invariants}}` | `{{idempotency_or_side_effect_oracle}}` | `{{compensation_ref}}` |

| 判据 ID | 范围 | 期望 | 验证命令/方法 | 最低证据等级 |
|---|---|---|---|---|
| `{{criterion_id}}` | `{{subject_ref}}` | `{{expected_result}}` | `{{verification_method}}` | `{{required_proof_level}}` |

正常、异常、恢复、责任、I/O、追溯和必需图任一缺失时，本链包验收失败。

实际 observation、执行 pass/fail、Run 和 Evidence 只能由执行后对象保存，不得回填本事前覆盖设计。fixture、local、UI simulation、readonly real、platform accepted、terminal delivered 和 production proof 不得混写。
