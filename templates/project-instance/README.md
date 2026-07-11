# 可选 L3 项目实例模板

| 问题 | 时机 | 输入 | 输出 | 下一步 |
|---|---|---|---|---|
| 何时需要 `projects/{project_id}/` namespace？ | L2 已有多实例隔离证据且治理路由批准启用 L3 时 | namespace、route lock、批准 facts 和 data boundaries | 隔离的 L3 实例事实根 | 填写锁定文件并验证隔离；否则继续使用 L2 根目录 |

## 复制后的完整树

```text
projects/{{project_id}}/
├── README.md                    # 必需：实例入口与完整树
├── project.yaml                 # 必需：namespace、owner 和数据边界
├── project-os.lock.yaml         # 必需：消费的 L1 协议版本锁
├── governance-route.yaml        # 必需：route lock 与治理范围
├── facts/facts.yaml              # 必需：实例批准事实
├── adapters/                    # 条件启用：实例专属外部适配
├── Run/                         # 运行时生成：执行记录，不预建
├── Evidence/                    # 运行时生成：证据，不预建
├── Verdict/                     # 运行时生成：裁决，不预建
├── Claim/                       # 运行时生成：声明，不预建
└── artifacts/                   # 运行时生成：验收交付物，不预建
```

L2 默认不套 `projects/`。只有 route lock 和跨实例隔离 Evidence 同时有效时启用本模板；模板本身不创建任何运行时目录，也不证明隔离成立。
