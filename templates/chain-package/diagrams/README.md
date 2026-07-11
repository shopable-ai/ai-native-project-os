# 业务链图入口

| 问题 | 时机 | 输入 | 输出 | 下一步 |
|---|---|---|---|---|
| 哪些链必须画图，图和文本如何防漂移？ | P0/P1 链包进入批准前 | `chain.yaml`、三类路径、责任与 I/O | 与链包同版本的源图和渲染图 | 校验图覆盖全部节点、终点与恢复边 |

## 完整复制树

```text
{{chain_package_root}}/
├── README.md                         # 必需：链包入口
├── chain.yaml                        # 必需：P0/P1 图需求机器字段
├── scenarios.md                      # 必需：场景
├── triggers.yaml                     # 必需：触发
├── business-flow.md                  # 必需：正常路径
├── exceptions.md                     # 必需：异常路径
├── recovery.md                       # 必需：恢复路径
├── responsibility-map.md             # 必需：责任
├── io-map.yaml                       # 必需：I/O
├── traceability.md                   # 必需：追溯
├── acceptance.md                     # 必需：验收
├── diagrams/
│   ├── README.md                     # 必需：本说明
│   ├── {{chain_id}}.mmd              # 条件启用：可编辑图源
│   └── {{chain_id}}.svg              # 运行时生成：渲染图
└── Evidence/Verdict                  # 运行时生成：图一致性证据与裁决
```

P0/P1 必须有图；图源和渲染图不得成为独立业务事实源。链路变化先改批准链包，再重新生成图和 Evidence。
