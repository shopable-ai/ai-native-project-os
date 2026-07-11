# policies/ 机器政策问题导航

本目录只保存“在什么结构化条件下选择哪条治理路线”的机器政策，不保存受控对象结构。当前唯一政策权威是 `project-governance-routing.yaml`；契约统一位于 `contracts/governance/`，不在本目录保留兼容副本。

| 问题 | 时机 | 输入 | 输出 | 文件 | 示例 | 下一步 |
|---|---|---|---|---|---|---|
| 项目应采用哪种基础治理配置、哪些 overlay 必需 | L2 接入、关键风险输入变化或人工覆盖到期时 | 项目类型、复杂度、不确定性、数据敏感度、副作用与运行环境等结构化事实 | 基础治理配置建议、逐 overlay 的 required 状态与显式 unknown | `project-governance-routing.yaml` | 未知生产副作用保持 unknown，不按低风险处理 | 按 `contracts/governance/route-decision-contract.yaml` 固定新版本路由裁决 |

## 政策与契约怎样相连

- 路由政策中的契约 ID（例如 `route-decision-contract@1`）是稳定逻辑引用；解析器应按 `project-os.yaml.authority` 将契约 ID 解析到 `contracts/governance/` 下的唯一权威文件。
- `policies/project-governance-routing.yaml` 只计算选择，不定义 route decision、control set、授权快照、审核裁决或完成声明的记录结构。
- 人类操作语义见 `docs/workflows/PROJECT_TYPE_AND_GOVERNANCE_ROUTING.md`；机器契约的问题导航见 `contracts/README.md`。
- 新增政策前先确认问题确实是“何时选择”，而不是“对象长什么样”；后者必须进入 `contracts/`。
