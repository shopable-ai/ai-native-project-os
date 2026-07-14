# 追溯

| 下游对象 | 上游批准对象 | 关系 | 验收出口 |
|---|---|---|---|
| `{{chain_id}}` | `{{requirement_ref}}` | `realizes` | `{{acceptance_ref}}` |
| `{{behavior_spec_id}}` | `{{requirement_ref}}` | `specifies_behavior_for` | `{{behavior_case_ref}}` |
| `{{behavior_case_id}}` | `{{behavior_spec_id}}` | `covered_by` | `{{coverage_ref}}` |
| `{{step_id}}` | `{{chain_id}}` | `part_of` | `{{criterion_ref}}` |
