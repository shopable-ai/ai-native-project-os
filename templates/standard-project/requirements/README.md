# 人机需求设计包

| 问题 | 时机 | 输入 | 输出 | 下一步 |
|---|---|---|---|---|
| 人怎样在 Spec 前审查 AI 对能力和功能的理解？ | S0—S2 从链路展开能力和功能时 | 批准 Fact/业务 Requirement、Chain、Capability、Function 和 Unknown | 能力卡、功能需求卡、项目地图、上下文快照和需求基线草稿 | 人类批准后进入研究/ADR，再生成 Spec |

## 复制后的目录

```text
requirements/
├── README.md                                  # 必需：本目录操作说明
├── 项目地图.md                                # 必需：人类每日引用入口
├── capabilities/
│   └── CAP-001_能力卡.md                     # 必需：能力树节点权威
├── functions/
│   └── FUNC-001_功能需求卡.md                 # 必需：单功能需求权威
├── baselines/
│   └── REQ-BASELINE-001.yaml                  # 必需：需求版本/hash 集合；复制时为 draft
├── context/
│   └── CTX-001.yaml                           # 条件启用：AI 起草/审查时的上下文快照；复制时为 captured
└── generated/
    └── README.md                              # 运行时生成：派生视图说明；当前无生成结果
```

契约相对路径：`capabilities/CAP-001_能力卡.md`、`functions/FUNC-001_功能需求卡.md`、`baselines/REQ-BASELINE-001.yaml`、`context/CTX-001.yaml`、`generated/README.md`。

## 权威边界

- `capabilities/*.md` 是业务能力树节点权威；复杂能力可以使用父级和子级 Capability，但不得把工程组件伪装成业务能力。
- `functions/*.md` 是单功能需求权威；一个 Function 只有一份 active 卡片版本。
- `项目地图.md` 只保存稳定引用，不复制需求正文、状态枚举或 Task。
- `baselines/*.yaml` 在人工批准前保持 `draft/pending`；批准后锁定需求 `stable_id/version/content_hash`，不得原地改写。
- `context/*.yaml` 复制时保持 `captured/pending`；它只证明 AI 实际读取范围，不证明输入或输出正确。
- `generated/` 只保存可重建视图，不是能力树、需求、Spec 或影响关系的第二权威。

## 使用顺序

1. 从批准业务 Requirement、Scenario 和 Chain 推导父级/子级 Capability。
2. 从 Capability 推导可观察 Function；内部判断步骤优先保留为功能规则或状态门，不自动升级为顶层 Function。
3. 创建或更新功能需求卡，补典型输入、输出格式、状态矩阵、正反边界例和 AI 自检。
4. 人类核对四段意图、边界、异常、风险与验收方向。
5. 多种候选实现方案进入 Research/ADR；未经决策不能成为批准要求。
6. 人类批准需求版本并创建新 baseline；AI 不能填写或冒充批准身份。
7. Spec 精确引用卡片版本/hash 和 baseline；未批准或意图不一致时 fail closed。

## 声明边界

本模板只提供静态结构。它不实现项目地图生成器、Impact Simulation、上下文自动打包、真实 L2 迁移或生产审批。`必需` 表示结构必须存在，`条件启用` 表示触发后创建，`运行时生成` 不表示已有运行能力。复制模板产生的是草稿，不是批准事实、批准需求或运行证明。
