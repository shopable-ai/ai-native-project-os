# 业务链包模板

| 问题 | 时机 | 输入 | 输出 | 下一步 |
|---|---|---|---|---|
| 一条 P0/P1 业务链如何完整表达并可验收？ | 场景、触发、责任和失败路径已能被批准时 | 批准需求、场景、角色、触发和 I/O 边界 | 可追溯的业务链控制包 | 填写所有必需文件并运行契约测试 |

## 复制后的完整树

```text
{{chain_package_root}}/
├── README.md                 # 必需：入口与复制树
├── chain.yaml                # 必需：链标识、优先级、路径和图要求
├── scenarios.md              # 必需：场景与非目标
├── triggers.yaml             # 必需：结构化触发条件
├── business-flow.md          # 必需：正常路径
├── exceptions.md             # 必需：异常路径
├── recovery.md               # 必需：恢复路径
├── responsibility-map.md     # 必需：角色、职责和交接
├── io-map.yaml               # 必需：producer/consumer 与输入输出
├── traceability.md           # 必需：需求到链路与验收的追溯
├── acceptance.md             # 必需：事前验收判据
├── diagrams/README.md        # 必需：P0/P1 图要求与图产物落点
└── Run/Evidence/Verdict/Claim # 运行时生成：不随模板预建
```

## 使用边界

- P0/P1 链必须产出与文本同源的图；较低优先级是否绘图由 L2 决定。
- 正常、异常、恢复路径都必须有终点、责任人和 I/O；缺失任一项时不得进入实现。
- 条件启用的外部适配器和补偿步骤只登记引用，不复制其政策定义。
