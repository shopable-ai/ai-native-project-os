# 状态迁移与失效传播

本文件是工作状态、合法迁移、证据过期、影响闭包和声明撤销的唯一权威源。

## 1. 六个正交坐标

- 生命周期位置：`R0`、`S0`—`S7`；成熟度坐标，可并行和重开。
- 工作状态：`not_applicable`、`queued`、`in_progress`、`waiting_approval`、`blocked`、`paused`、`failed`、`completed`、`superseded`、`retired`。
- 审批状态：`not_required`、`pending`、`approved`、`rejected`、`expired`、`revoked`。
- 实现状态：`not_applicable`、`not_started`、`partial`、`implemented`；只表达实现事实，不能由阶段或审批推导。
- 证据等级：只引用 `GATES_PROOF_SCORING.md` 的机器枚举，不在本文件复制。
- 失效状态：`fresh`、`review_required`、`expired`、`invalidated`；只表达当前可用性，不改写历史验证结果。

禁止用一个 `completed` 同时表达成熟度、审批、实现、证明和当前可用性。

## 2. 合法工作状态迁移

| 当前 | 允许迁移到 | 必要条件 |
|---|---|---|
| `queued` | `in_progress` / `blocked` / `paused` / `superseded` | 输入、责任和权限已验证，或记录阻断/替代原因 |
| `not_applicable` | 无 | 非工作型记录使用类型专属状态；不得借此绕过其签名、审批或证据门禁 |
| `in_progress` | `waiting_approval` / `blocked` / `paused` / `failed` / `completed` / `superseded` | 对象声明的 gate 已通过；只有 gate 类型为 acceptance 时才要求有效 Acceptance Verdict |
| `waiting_approval` | `in_progress` / `blocked` / `failed` / `superseded` | 批准后恢复；拒绝保留理由 |
| `blocked` | `queued` / `in_progress` / `failed` / `superseded` | 阻断项关闭并重新校验输入 |
| `paused` | `queued` / `in_progress` / `superseded` | checkpoint、输入、权限和证据仍有效 |
| `failed` | `queued` / `superseded` | 创建带因果关系的重试或修订；失败历史不改写 |
| `completed` | `in_progress` / `superseded` | 仅因上游变化、Evidence 失效或 Verdict 撤销重开 |
| `superseded` | `retired` | 已有明确后继对象且消费者迁移完成 |
| `retired` | 无 | 终态；恢复必须新建版本 |

非法迁移包括：从 `not_applicable` 迁移；从 `queued`、`blocked`、`paused` 或 `failed` 直接到 `completed`；从 `retired` 恢复；把失败 Run 原地改成成功；审批过期后继续执行副作用。

每次迁移记录对象版本、前后状态、发起者、时间、原因、前置 Evidence、审批引用和 checkpoint。

`resume` 和 `retry` 是必须记录的迁移事件，不是掩盖历史的新稳定状态：`resume` 从 `paused` 恢复到 `queued/in_progress`；`retry` 从 `failed` 创建新 Run 并回到 `queued`。事件记录必须引用原状态、原 Run、checkpoint、重试原因和预算。

## 3. 失败、重试、暂停和恢复

失败记录不可删除。重试必须使用新 Run ID、引用原失败 Run、声明幂等键和重试预算。暂停必须生成 checkpoint 和未完成副作用清单；恢复前重新验证输入摘要、工具/策略版本、审批有效期和外部系统状态。

未知外部写入结果不得盲重试，必须先查询回执或真实状态。取消不等于回滚；撤销/补偿结果需要独立 Evidence。

## 4. 失效传播

触发源包括：批准事实/需求变化、项目类型或版本化治理路由/control set 变化、契约/策略/权限变化、内容或环境指纹变化、Evidence 过期、Verdict 撤销、生产事故反证。

传播语义：

1. 上游变更产生新版本或 `supersedes`，不得覆写历史批准内容。
2. 按受控对象模型为每类关系登记传播方向；至少沿 `derives_from`、`implements`、`consumes`、`produces/produced_by`、`governed_by`、`verified_by`、判据/Verdict/Claim 引用和版本锁定计算传递下游闭包。未知关系 fail-closed。
3. 每个下游对象先做影响分类：`unaffected`、`review_required`、`invalidated`；必须记录理由和分析者。
4. 未完成对象转 `blocked` 或待复核；已完成对象重开为 `in_progress`；Evidence 的 `stale_status` 转为 `expired/invalidated`，不改写其历史 `verification_status`。
5. 相关 Verdict 转 `revoked/pending`；Completion Claim 转 `withdrawn/expired`。
6. 传播只在版本隔离证据充分、边界明确不受影响或人工影响分析批准处停止。
7. 下游只能发起 `requests_review_of`；上游 owner/approver 决定是否修订批准事实、需求、契约或决策。
8. 新 Evidence 和新 Verdict 通过全部受影响门禁后，才可重新签发声明。

历史 Run 是不可改写的执行事实。控制集升级只会使旧 Evidence 对当前要求变为不足、待复核或失效，并撤销相应 Verdict/Claim；不得把旧 Run 改写为符合新控制集。

本文件定义后续实现必须满足的语义；当前尚无自动失效引擎或运行证明。
