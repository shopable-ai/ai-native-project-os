# Spec 五件套模板

| 问题 | 时机 | 输入 | 输出 | 下一步 |
|---|---|---|---|---|
| 一个批准行为如何形成唯一、可追溯的实现任务包？ | 行为案例、测试空间、链路和验收方向已批准时 | 批准需求、Behavior Case、Coverage、链包与约束 | 带稳定案例引用的 Spec 五件套 | 在 `tasks.md` 定义任务，再让 plan 引用排序 |

## 复制后的完整树

```text
specs/{{spec_id}}/
├── README.md              # 必需：职责与复制树
├── spec.yaml              # 必需：v2 contract 与跨包稳定引用
├── spec.md                # 必需：范围、非目标、约束、失败状态
├── plan.md                # 必需：只排序 task_refs
├── tasks.md               # 必需：单个 Spec 任务的唯一权威
├── acceptance.md          # 必需：事前验收判据
├── traceability.md        # 必需：批准对象到任务和验收的追溯
├── task-tree.md           # 条件启用：跨 Spec task-tree 只生成视图，不可编辑
└── Evidence/Verdict/Claim # 运行时生成：不随模板预建
```

跨 Spec task-tree 只生成视图，不能定义或改写任务。任何任务变更先改对应 Spec 的 `tasks.md`，再重算计划和视图。

Spec、Task、Acceptance 和 Traceability 都引用稳定 Behavior Case ID。实现或测试变化不复制/改版案例；实际执行结果由 S6 的 Run/Evidence/Verdict/Claim 保存。
