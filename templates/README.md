# 模板问题导航

| 问题 | 时机 | 输入 | 输出 | 下一步 |
|---|---|---|---|---|
| 我现在缺哪类控制包？ | L2 建立或恢复项目操作骨架时 | 已批准事实、需求、现有实现和治理路由 | 可复制的最小模板包 | 选择下表入口并按包内 README 填写 |

## 选择入口

| 要解决的问题 | 模板 |
|---|---|
| 描述业务链的正常、异常、恢复、责任和 I/O | `chain-package/` |
| 在 Spec 前审查意图、功能需求和批准基线 | `standard-project/requirements/` |
| 在自动审核或低风险自动决策前固定策略包、测试集与激活边界 | `standard-project/governance/review-certification/` |
| 为一个 Spec 建立五件套 | `spec-package/` |
| 固定 producer/consumer 的 I/O 协议 | `io-contract/` |
| 编排已批准 task refs | `workflow/` |
| 定义单阶段局部 AI/代码能力 | `skill/` |
| 在有隔离证据时建立可选 L3 namespace | `project-instance/` |
| 接入新建型 L2 系统 | `standard-project/` |
| 恢复存量 L2 系统 | `brownfield-project/` |

## 完整模板树

```text
templates/
├── README.md                         # 必需：问题导航
├── chain-package/                    # 条件启用：需要批准业务链时复制
├── standard-project/requirements/    # 必需：standard L2 的人机需求设计包
├── standard-project/governance/review-certification/ # 必需：审核策略认证模板
├── spec-package/                     # 必需：每个进入实现的 Spec 使用
├── io-contract/                      # 条件启用：存在跨组件边界时复制
├── workflow/                         # 条件启用：需要可恢复编排时复制
├── skill/                            # 条件启用：需要局部可复用能力时复制
├── project-instance/                 # 条件启用：有 L3 多实例隔离证据时复制
├── standard-project/                 # 条件启用：Greenfield L2 接入入口
├── brownfield-project/               # 条件启用：Brownfield L2 恢复入口
└── Run/Evidence/Verdict/Claim/artifacts # 运行时生成：不在 L1 模板中预建
```

模板只提供结构与可校验占位符，不证明对应能力已经实现或运行。L2 默认直接使用自身根目录；没有多实例隔离证据时，不套 `projects/{project_id}/`。
