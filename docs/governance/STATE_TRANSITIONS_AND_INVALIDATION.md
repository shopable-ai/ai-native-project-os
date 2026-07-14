# 状态迁移与失效传播

本文件是工作状态、合法迁移、证据过期、影响闭包和声明撤销的唯一权威源。

## 1. 六个正交坐标

- 生命周期位置：`R0`、`S0`—`S7`；成熟度坐标，可并行和重开。
- 工作状态：`not_applicable`、`queued`、`in_progress`、`waiting_approval`、`blocked`、`paused`、`failed`、`completed`、`superseded`、`retired`。其中 `waiting_approval` 只服务被路由到 `human_signoff` 的高风险治理、例外、剩余风险和动作授权；低风险对象走已认证策略或 blocked。
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
| `in_progress` | `waiting_approval` / `blocked` / `paused` / `failed` / `completed` / `superseded` | 只有治理或授权对象可以进入 `waiting_approval`；其他对象声明的 gate 已通过后按类型专属状态继续 |
| `waiting_approval` | `in_progress` / `blocked` / `failed` / `superseded` | 仅在 `human_signoff`、例外、剩余风险或动作授权完成后恢复；拒绝保留理由和决策证据 |
| `blocked` | `queued` / `in_progress` / `failed` / `superseded` | 阻断项关闭并重新校验输入 |
| `paused` | `queued` / `in_progress` / `superseded` | checkpoint、输入、权限和证据仍有效 |
| `failed` | `queued` / `superseded` | 创建带因果关系的重试或修订；失败历史不改写 |
| `completed` | `in_progress` / `superseded` | 仅因上游变化、Evidence 失效或 Verdict 撤销重开 |
| `superseded` | `retired` | 已有明确后继对象且消费者迁移完成 |
| `retired` | 无 | 终态；恢复必须新建版本 |

非法迁移包括：从 `not_applicable` 迁移；从 `queued`、`blocked`、`paused` 或 `failed` 直接到 `completed`；从 `retired` 恢复；把失败 Run 原地改成成功；审批过期后继续执行副作用。

普通内容审核不得使用 `waiting_approval`。AI 审核使用 `ai_review_verdict.decision` 表达 `allow/rewrite_required/blocked/rule_gap`；可修复问题自动改写并重新审核，规则不足或达到改写上限时阻断当前输出。不得以人工逐条润色或临时批准作为默认降级路径。

每次迁移记录对象版本、前后状态、发起者、时间、原因、前置 Evidence、审批引用和 checkpoint。

`resume` 和 `retry` 是必须记录的迁移事件，不是掩盖历史的新稳定状态：`resume` 从 `paused` 恢复到 `queued/in_progress`；`retry` 从 `failed` 创建新 Run 并回到 `queued`。事件记录必须引用原状态、原 Run、checkpoint、重试原因和预算。

## 3. 失败、重试、暂停和恢复

失败记录不可删除。重试必须使用新 Run ID、引用原失败 Run、声明幂等键和重试预算。暂停必须生成 checkpoint 和未完成副作用清单；恢复前重新验证输入摘要、工具/策略版本、审批有效期和外部系统状态。

未知外部写入结果不得盲重试，必须先查询回执或真实状态。取消不等于回滚；撤销/补偿结果需要独立 Evidence。

## 4. 失效传播

触发源包括：通过决策门的事实/需求/Behavior Specification 变化、semantic inventory 的类别/成员/阻断集合/组合模式/资源约束新增删除或修改、active 规则集变更/过期/撤销、项目类型或版本化治理路由/control set 变化、契约/策略/权限变化、内容或环境指纹变化、Evidence 过期、Verdict 撤销、生产事故或新反例。

审核策略认证使用更严格的完整绑定。规则、Prompt、输入/输出 Schema、Context 选择与截断策略、模型 fingerprint、Tool、权限、测试集、指标定义、阈值、scope、项目 namespace 或 verifier 独立性任一变化，都必须使旧 `review_policy_certification` 进入 `review_required`、`expired` 或 `invalidated`，而不是只比较 Prompt 文本。

认证失效至少传播到使用它的 Requirement Baseline、Spec、Workflow、AI Review Verdict、Acceptance Verdict 和 Claim。自动批准路由立即失去资格并转 blocked；只有新策略包、新测试 Run/Evidence 和新认证 Verdict 通过后，才能用新 Run 重开。外部动作授权始终单独失效和重验，不能从认证恢复中继承。
传播语义：

1. 上游变更产生新版本或 `supersedes`，不得覆写历史批准内容。
2. 按受控对象模型为每类关系登记传播方向；至少沿 `derives_from`、`implements`、`consumes`、`produces/produced_by`、`governed_by`、`verified_by`、判据/Verdict/Claim 引用和版本锁定计算传递下游闭包。未知关系 fail-closed。
3. 每个下游对象先用独立字段 `impact_classification` 做影响分类：`unaffected`、`review_required`、`invalidated`；必须记录理由和分析者。它不是 Evidence 的状态枚举。
4. 未完成对象转 `blocked` 或待复核；已完成对象重开为 `in_progress`；Evidence.stale_status 仍只使用 `fresh/stale/expired/invalidated`，按影响转为 `stale`、`expired` 或 `invalidated`，不得写入 `review_required`，也不得改写其历史 `verification_status`。
5. 相关 Verdict 转 `revoked/pending`；Completion Claim 转 `withdrawn/expired`。
6. 审核策略包或认证变化使引用旧版本/hash 的 AI Review Verdict 进入 `revoked/pending`，相关输出重新审核；开放的 `rule_gap_case` 只有在新规则、新认证和新 Run 完成后才能关闭。
7. 传播只在版本隔离证据充分、边界明确不受影响，且受控影响分析通过合法 Decision Gate 时停止。
8. 下游只能发起 `requests_review_of`；上游 owner 和 Decision Gate 决定是否修订受控事实、需求、契约或决策。
9. 新 Evidence 和新 Verdict 通过全部受影响门禁后，才可重新签发声明。
10. semantic inventory 或派生约束变化时先重算 Test Space 与组合差异；Behavior Case、Coverage、Spec/Task/Test 和依赖旧 inventory/hash 的 Evidence/Verdict/Claim 沿闭包进入待复核或失效。传播只能因版本隔离或已批准 `unaffected` 分析停止。

历史 Run 是不可改写的执行事实。失效传播不改写历史 Run，只会使旧 Evidence 对当前要求变为不足、待复核或失效，并撤销相应 Verdict/Claim；不得把旧 Run 改写为符合新控制集或新策略包。

本文件定义后续实现必须满足的语义；当前尚无自动失效引擎或运行证明。
