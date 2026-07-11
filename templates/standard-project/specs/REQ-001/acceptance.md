# REQ-001 验收判据

| Criterion | 期望 | 验证方式 | 最低证据等级 |
|---|---|---|---|
| `AC-001` | Spec 五件套存在 | 检查五个 Markdown 文件 | `control_package` |
| `AC-002` | 追溯只指向批准对象 | 检查 `traceability.md` 不含原始来源路径 | `control_package` |
| `AC-003` | Evidence 不越界 | 检查 fixture、Verdict 和 Claim 字段 | `control_package` |

三个判据全部通过只表示模板控制包结构成立，不表示实现、运行或生产验收通过。
