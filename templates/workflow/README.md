# Workflow 模板

| 问题 | 时机 | 输入 | 输出 | 下一步 |
|---|---|---|---|---|
| 已批准任务如何形成有界、可取消、可恢复的执行图？ | Spec tasks 已批准且存在多步依赖时 | task refs、I/O 契约、权限和资源边界 | Workflow 声明 | 验证所有 refs、失败路由与终态 |

## 复制后的完整树

```text
{{workflow_root}}/
├── README.md                     # 必需：问题导航与完整树
├── workflow.yaml                 # 必需：task refs、step graph 和执行边界
├── adapters/                     # 条件启用：外部执行器适配器
├── checkpoints/                  # 运行时生成：恢复点，不随模板预建
└── Run/Evidence/Verdict/artifacts # 运行时生成：执行记录、证据、裁决和产物
```

Workflow 只编排 `tasks.md` 的 task refs，不拥有任务定义。权限、预算、超时、取消或补偿缺失时不得启动有副作用的执行。
