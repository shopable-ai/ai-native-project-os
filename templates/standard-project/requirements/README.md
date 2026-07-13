# 人机需求设计包

| 问题 | 时机 | 输入 | 输出 | 下一步 |
|---|---|---|---|---|
| 人怎样在 Spec 前审查 AI 对能力和功能的理解？ | S0—S2 从链路展开能力和功能时 | 批准 Fact/业务 Requirement、Chain、Capability、Function 和 Unknown | 能力卡、功能需求卡、项目地图、上下文快照和需求基线草稿 | 人类批准后进入研究/ADR，再生成 Spec |

## 复制后的目录

```text
requirements/
├── README.md
├── 项目地图.md
├── capabilities/
│   └── CAP-001_能力卡.md                     # 必需：能力树节点权威
├── functions/
│   └── FUNC-001_功能需求卡.md                 # 必需：单功能需求权威
├── baselines/
│   ├── REQ-BASELINE-DRAFT-001.yaml            # 必需：新项目复制入口，draft/pending
│   └── REQ-BASELINE-001.yaml                  # 必需：已批准结构示例，不直接复制为新项目状态
├── context/
│   ├── CTX-DRAFT-001.yaml                     # 条件启用：新项目上下文捕获入口
│   └── CTX-001.yaml                           # 必需：已批准结构示例
└── generated/
    └── README.md                              # 运行时生成：派生视图说明
```

契约相对路径包含能力卡、功能需求卡、Draft/Approved Baseline 示例、Captured/Approved Context 示例和 `generated/README.md`。

为便于复制器和检查器精确核对，完整相对路径为：

```text
capabilities/CAP-001_能力卡.md
functions/FUNC-001_功能需求卡.md
baselines/REQ-BASELINE-DRAFT-001.yaml
baselines/REQ-BASELINE-001.yaml
context/CTX-DRAFT-001.yaml
context/CTX-001.yaml
```

## 权威边界

- `capabilities/*.md` 是业务能力树节点权威；复杂能力可以使用父级和子级 Capability，但不得把工程组件伪装成业务能力。
- `functions/*.md` 是单功能需求权威；一个 Function 只有一份 active 卡片版本。
- `项目地图.md` 只保存稳定引用，不复制需求正文、状态枚举或 Task。
- 新项目从 `REQ-BASELINE-DRAFT-001.yaml` 开始；`REQ-BASELINE-001.yaml` 只展示批准后结构。
- AI 起草从 `CTX-DRAFT-001.yaml` 开始；`CTX-001.yaml` 只展示人类批准后的结构。
- `generated/` 只保存可重建视图，不是能力树、需求、Spec 或影响关系的第二权威。

## 使用顺序

1. 从批准业务 Requirement、Scenario 和 Chain 推导父级/子级 Capability。
2. 从 Capability 推导可观察 Function；内部判断步骤优先保留为功能规则或状态门，不自动升级为顶层 Function。
3. 创建功能需求卡，补典型输入、输出格式、状态矩阵、正反边界例和 AI 自检。
4. 使用 Draft Context 记录 AI 实际读取范围，使用 Draft Baseline 汇总候选需求成员。
5. 人类核对四段意图、边界、异常、风险与验收方向。
6. 多种候选实现方案进入 Research/ADR；未经决策不能成为批准要求。
7. 人类批准后创建新的 approved Context 与 Requirement Baseline；AI 不能填写或冒充批准身份。
8. Spec 精确引用批准卡片版本/hash 和 approved baseline；未批准或意图不一致时 fail closed。

## 声明边界

本模板只提供静态结构。它不实现项目地图生成器、Impact Simulation、上下文自动打包、真实 L2 迁移或生产审批。已批准文件只是结构 fixture，不表示复制后的项目已经获得批准、实现或运行证明。
