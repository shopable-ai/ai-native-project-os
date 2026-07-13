# 人机协作需求设计工作流

| 阅读契约 | 内容 |
|---|---|
| 解决的问题 | 在 AI 生成 ADR、Spec 和 Task 前，让人和受控 AI 逐步校验原始意图、功能边界、未知项，并通过合法决策门形成需求基线。 |
| 何时阅读 | 从业务链路展开功能、审查 AI 需求草稿、准备冻结需求或上游变化需要重开时。 |
| 输入 | 批准 Source/Fact/业务 Requirement、Scenario、Business Chain、Capability、Function、Unknown 和现有基线。 |
| 输出 | 经 AI 自检、独立审核和合法 Decision Gate 接受的功能需求、不可变 Requirement Baseline、上下文快照、待研究问题和 ADR/Spec 入口。 |
| 下一步 | 需求通过 `policy_certified` 或 `human_signoff` 后进入研究/ADR 和工程设计，再由[项目交付工作流](PROJECT_DELIVERY_WORKFLOW.md)生成 Spec；否则留在本工作流。 |

本文是“人怎样借助 AI 形成正确需求”的操作权威。对象字段和关系由[受控对象模型](../governance/CONTROLLED_OBJECT_MODEL.md)定义，模板结构由注册的 requirement design package contract 定义；本文不维护第二份机器枚举。复杂能力的拆分与命名示例见[能力、功能与 Spec 映射指南](../governance/CAPABILITY_FUNCTION_SPEC_MAPPING.md)。

## 1. 固定因果顺序

```text
Source → Fact / Unknown → Requirement → Scenario → Business Chain → Capability → Function → Functional Requirement → Decision Gate → Requirement Baseline → Research / ADR → Engineering Design → Spec
```

这条链把两类工作分开：

- 需求设计先回答“为什么做、为谁做、怎样才算业务正确、边界和异常是什么”；
- ADR、工程设计和 Spec 再回答“用什么方案实现、怎样拆成可测试工程工作包”。

不得从功能树直接跳到 Spec。也不得用 Spec 五件套替代人类第一次理解功能的入口。

## 2. 恢复原始意图，而不是立即解释成方案

每个目标或功能先保存四段意图：

1. `original_intent`：来自批准来源的原始目标或稳定引用；
2. `interpreted_intent`：AI 或分析者当前的候选理解；
3. `approved_intent`：由合法 Decision Gate 接受并绑定决策证据的业务意图；
4. `implementation_intent`：准备交给 ADR/Spec 的实现目标。

审核者首先检查：候选解释有没有偷换目标；成功指标和非目标是否仍符合原始意图；实现目标是否扩大、弱化或替换批准意图；哪些问题仍是 Unknown，是否阻断当前决定。相同检查规则必须进入审核策略 Context，不能只留在人脑或聊天中。

任一项无法确认时，需求保持 draft、`waiting_approval` 或 `blocked`。低风险且不扩大治理边界的对象可由当前认证策略进入 `policy_certified`；目标、责任、scope、阈值、权限、风险接受或不可逆副作用变化必须进入 `human_signoff`。生成该需求的 AI 不能给自己的策略签发独立认证，也不能把自身写成决策权威。

## 3. 从链路推导能力、功能和功能需求

推导顺序固定为：

```text
业务链路 → 业务能力树 → 用户功能树 → 单功能需求卡
```

- 业务链路描述业务状态怎样变化，包含正常、异常和恢复路径；
- 能力树描述完成链路必须具备什么稳定能力，不绑定组件；
- 功能树描述用户或调用方可以观察和使用什么；
- 功能需求卡描述一个功能的目标、触发、规则、边界、异常、输入输出、风险和业务验收方向。

一个功能只维护一份需求卡。复杂功能可以拆成多个稳定 Function 和对应卡片，但不能为同一功能复制多份可编辑需求真相。

## 4. AI 起草与自检

AI 可以读取被明确纳入 `context_snapshot` 的权威文件并生成 draft。每次起草必须同时回答：

1. 当前缺少哪些必要信息；
2. 使用了哪些假设；
3. 哪些结论最可能错误；
4. 哪些内容可由已认证规则判定，哪些必须由人类确认；
5. 与上游链路、Capability、Function 或已有 Requirement 是否冲突；
6. 建议的实现内容是已批准约束，还是尚未决策的候选方案。

聊天、`.prompts/`、临时摘要和外部零碎笔记默认排除。上下文快照只证明 AI 实际读取范围，不证明内容正确或已经批准。

## 5. Decision Gate 审查什么

独立 AI reviewer 与被路由到 `human_signoff` 的人类审查同一份功能需求卡，而不是先审查 Spec 五件套。两者使用同一组显式规则、输入边界和失败语义：

- 一句话结论是否与 `approved_intent` 一致；
- 使用者、触发条件、正常/异常/拒绝/恢复路径是否完整；
- 输入、输出和业务规则是否能被下游验证；
- 非目标、数据、权限、外部副作用和责任边界是否清楚；
- 验收方向是否检查业务结果，而不是只检查文件存在或退出码；
- “已批准实现约束”是否真的来自批准决策；
- “候选实现要点”是否仍停留在候选区，没有冒充要求；
- Unknown 和上下游影响是否有 owner 与处置路径，阻断性 Unknown 是否已经清零。

自动路径不能只靠一句 Prompt。规则、Prompt、Schema、Context 策略、模型 fingerprint、Tool/权限、改写上限和失败出口必须组成审核策略包，并先通过预注册正例、反例、边界、对抗和重复运行测试。完整规则见[审核策略认证](../governance/REVIEW_POLICY_CERTIFICATION.md)。

`policy_certified` 只适用于认证仍新鲜、scope 匹配、阈值未降低、阻断规则未减少、权限未增加、目标/责任未变化且无未决 Unknown 的范围。其他可接受变化进入 `human_signoff`；证据不足、规则冲突或无法判断时保持 blocked，不能把人工当作普通输出的默认兜底。

## 6. 冻结 Requirement Baseline

批准不是覆盖原文件中的 `draft` 字样，而是形成可重算基线：

```text
baseline_id + version + requirement stable_id/version/content_hash 集合
+ scope hash + approval_route + decision_authority_ref
+ certification_verdict_ref/approved_by + approved_at + supersedes
```

冻结后：

- 原版本和旧基线不可改写；
- 需求内容变化创建新版本，成员集合变化创建新 baseline；
- 删除、拆分、合并、退休或降权形成 scope-change 和下游影响分析；
- 旧 ADR、Spec、Task、Evidence、Verdict 和 Claim 按依赖关系进入待复核或失效；
- AI 可以提出新版本并执行已认证策略；但生成者不能自认证、修改激活 Policy 后沿用旧认证，或在没有合法 Decision Gate 时冻结需求基线。

## 7. 从批准需求进入 ADR 与 Spec

候选实现要点先进入研究、方案比较和 ADR。只有已接受 ADR 和通过 Decision Gate 的实现约束才能进入工程设计。

Spec 必须精确引用功能需求 `stable_id/version/content_hash`、当前 Requirement Baseline、适用 ADR/工程设计以及事前验收判据与失败状态。

未通过合法批准路由、认证已过期、意图未对齐、上下文不可重放或不在当前 baseline 的功能需求都必须 fail closed，不能生成 active Spec。

## 8. 项目地图与 Unknown

L2 项目地图是人类每日入口，回答：项目目标是什么、当前阶段在哪里、核心链路/能力/功能是什么、哪些需求已批准、重大决策/风险/Unknown 是什么、下一步由谁做。它只保存稳定引用和当前导航，不复制功能需求正文、机器状态枚举或 Spec 任务清单。

Unknown 必须记录 owner、影响、是否 `blocks_decision`、研究入口和期限。处置顺序沿用现有研究权威：

```text
Unknown → Research → Decision → Fact/Requirement/ADR update
```

研究输出仍是候选结论，不能绕过 Decision Gate 修改批准基线。

## 9. 变更前影响预览与变更后失效

修改需求前应生成影响预览，列出受影响 Capability、Function、ADR、Spec、Task、Test、Workflow 和 Evidence。当前 L1 只定义报告入口和失败边界，不声称已有自动 Impact Simulation 引擎。

变更批准后必须执行[状态迁移与失效传播](../governance/STATE_TRANSITIONS_AND_INVALIDATION.md)；预览不能代替实际失效闭包，实际传播也不能反向证明预览完整。

## 10. 风险自适应裁剪

`lite` 项目可以压缩中间展示，但不能省略原始/批准意图、功能需求、非目标、批准基线和验收方向。`standard` 项目使用完整链路、能力、功能和需求设计路径。高风险或生产场景使用现有 `standard + production` 及授权/审核控制，不新增第三种基础 Profile。

无论选择哪种治理配置，AI draft、审批状态、批准路由、实现状态和 proof level 都必须分别记录，不能由一个 `completed` 推导。

## 11. 复杂能力、内部状态门与 Spec 拆分

复杂业务节点可以先形成父级 Capability，再展开子 Capability 与 Function：

```text
Business Chain → CAP-root → CAP-child → FUNC → Functional Requirement
```

`CAP-root` 只是能力树根节点，不是新的 `subsystem` 对象类型；工程子系统在 ADR 后通过 Component 和 Engineering Chain 表达。

拆 Function 的主要条件：独立业务结果、独立输入输出、独立异常/恢复、独立业务验收或可被调用方单独使用。内部判断步骤不应自动升级为顶层 Function；它可以保留为某个功能中的状态门、规则或子流程。

拆 Spec 的主要条件：独立 owner、独立工程边界、独立发布节奏、独立 proof gate、独立权限/副作用或可单独替换。Function 与 Spec 不要求一一对应，但必须保留可解释映射。

复杂功能需求卡必须给出典型输入、结构化输出、正例/反例/边界例、业务状态与执行状态的区别，以及候选实现方案。候选方案只能进入 Research/ADR，不能在需求卡中被 AI 自动冻结为唯一实现。
