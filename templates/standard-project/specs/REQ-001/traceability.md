# REQ-001 追溯

| 下游对象 | 上游批准对象 | 关系 | 验收出口 |
|---|---|---|---|
| `REQ-001` | [FACT-001](../../domain/glossary.md#fact-001) | `derives_from` | `AC-001` |
| `SPEC-REQ-001` | [REQ-001](../../domain/mvp/REQ-001.md) | `governs` | `AC-001`、`AC-002` |
| `TASK-001..003` | `SPEC-REQ-001` | `implements` | `AC-001..003` |
| `REQ-001-review-evidence` | `AC-001..003` | `verified_by` | `reviews/REQ-001-review-evidence.yaml` |

本表的上游只包含 `domain/` 中已经批准的 fact/requirement。原始材料必须先升格，不能直接成为 Spec 或 Task 的实现关系上游。
