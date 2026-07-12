# REQ-FUNC-001 追溯

| 下游对象 | 上游批准对象 | 关系 | 验收出口 |
|---|---|---|---|
| `REQ-001` | [FACT-001](../../domain/glossary.md#fact-001) | `derives_from` | `AC-001` |
| `REQ-FUNC-001` | [REQ-001](../../domain/mvp/REQ-001.md) + [功能需求卡](../../requirements/functions/FUNC-001_功能需求卡.md) | `derives_from` / `approved_by` | `REQ-BASELINE-001` |
| `SPEC-REQ-FUNC-001` | [REQ-FUNC-001](../../requirements/functions/FUNC-001_功能需求卡.md) + [REQ-BASELINE-001](../../requirements/baselines/REQ-BASELINE-001.yaml) | `governs` / `bound_by_baseline` | `AC-001`、`AC-002` |
| `TASK-001..003` | `SPEC-REQ-FUNC-001` | `implements` | `AC-001..003` |
| `REQ-FUNC-001-review-evidence` | `AC-001..003` | `verified_by` | `reviews/REQ-FUNC-001-review-evidence.yaml` |

本表的上游只包含已经批准的 fact、业务 requirement、功能 requirement 和 baseline。原始材料、项目地图、生成视图或聊天必须先升格，不能直接成为 Spec 或 Task 的实现关系上游。
