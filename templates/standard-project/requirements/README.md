# 人机需求设计包

| 问题 | 时机 | 输入 | 输出 | 下一步 |
|---|---|---|---|---|
| 人怎样在 Spec 前审查 AI 对功能的理解？ | S0—S2 从链路展开功能时 | 批准 Fact/业务 Requirement、Chain、Capability、Function 和 Unknown | 功能需求卡、项目地图、上下文快照和批准需求基线 | 人类批准后进入研究/ADR，再生成 Spec |

## 复制后的目录

```text
requirements/
├── README.md                                  # 必需：本目录操作说明
├── 项目地图.md                                # 必需：人类每日引用入口
├── functions/
│   └── FUNC-001_功能需求卡.md                 # 必需：单功能需求权威
├── baselines/
│   └── REQ-BASELINE-001.yaml                  # 必需：批准需求版本/hash 集合
├── context/
│   └── CTX-001.yaml                           # 条件启用：AI 起草/审查时的上下文快照
└── generated/
    └── README.md                              # 运行时生成：派生视图说明；当前无生成结果
```

契约相对路径：`functions/FUNC-001_功能需求卡.md`、`baselines/REQ-BASELINE-001.yaml`、`context/CTX-001.yaml`、`generated/README.md`。

## 权威边界

- `functions/*.md` 是单功能需求权威；一个 Function 只有一份 active 卡片版本。
- `项目地图.md` 只保存稳定引用，不复制需求正文、状态枚举或 Task。
- `baselines/*.yaml` 锁定已批准需求的 `stable_id/version/content_hash`，批准后不得原地改写。
- `context/*.yaml` 只证明 AI 实际读取范围，不证明输入或输出正确。
- `generated/` 只保存可重建视图，不是需求、功能树、Spec 或影响关系的第二权威。

## 使用顺序

1. 从批准业务 Requirement、Scenario 和 Chain 推导 Capability、Function。
2. 创建或更新功能需求卡，AI 同时填写自检、假设、可能错误和待确认项。
3. 人类核对四段意图、边界、异常、风险与验收方向。
4. 研究候选实现要点；经 ADR 接受后才成为工程输入。
5. 人类批准需求版本并创建新 baseline；AI 不能填写或冒充批准身份。
6. Spec 精确引用卡片版本/hash 和 baseline；未批准或意图不一致时 fail closed。

## 声明边界

本模板只提供静态结构。它不实现项目地图生成器、Impact Simulation、上下文自动打包、真实 L2 迁移或生产审批。`必需` 表示结构必须存在，`条件启用` 表示触发后创建，`运行时生成` 不表示已有运行能力。
