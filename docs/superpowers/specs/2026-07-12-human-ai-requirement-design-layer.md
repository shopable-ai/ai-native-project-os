# 人机协作需求设计层：方案 B 纠偏设计

- 状态：已批准纠偏范围
- 日期：2026-07-12
- 作用范围：L1 通用方法、机器结构和 L2 标准模板
- 前置设计：`2026-07-11-项目推进骨架设计.md`

## 1. 核心判断

现有方案 B 已补齐从 Requirement 到 Claim 的机器推进骨架，但它仍不足以回答：当 AI 的理解可能持续出错时，人怎样逐步确认原始意图、审查功能需求、冻结批准基线，再允许 AI 生成 ADR、Spec 和执行资产。

本次不推翻现有受控对象、阶段和证据协议，而是在业务链路、能力树、功能树与 Spec 之间补入人类优先的需求设计层：

```text
Source
→ candidate Fact / Unknown
→ approved Fact / objective or business Requirement
→ Scenario / Business Chain
→ Capability
→ Function
→ Functional Requirement draft
→ AI self-review
→ Human approval + immutable Requirement Baseline
→ Research / ADR / Engineering Design
→ Spec → Task → Workflow → Skill/Tool
```

`.prompts/`、聊天摘录和未经批准的 AI 输出不能成为这条链的权威。

## 2. 十项盲区处理矩阵

| 候选盲区 | 当前仓库事实 | 本次处理 |
|---|---|---|
| Human-AI Reasoning Layer | Source、Fact、Requirement、Scenario、Capability、Function 已有，Functional Requirement 人类工作台缺失 | 补需求设计工作流和功能需求卡 |
| Intent Verification | 没有原始、解释、批准、实现四段意图绑定 | 本次补齐并要求人工批准 |
| Decision Baseline | 已有 version/hash/supersedes 和 requirement baseline 语义，缺标准清单模板 | 复用现有机制，补不可变 baseline manifest；不增加平行状态轴 |
| Context Governance | 没有可重放的 AI 输入快照 | 补最小 `context_snapshot` 模板；明确聊天不是事实源 |
| Unknown Register | `unknown` 对象与研究流程已有，L2 人类入口不足 | 在项目地图登记未知、owner、阻断决策与研究入口 |
| Project Map | L1 有总览，L2 缺每日阅读的项目地图 | 补 L2 项目地图模板，内容以稳定引用为主 |
| Generation Review Loop | AI Review 契约已有，需求草稿的自检问题缺失 | 功能需求卡增加假设、缺口、可能错误和待人工确认 |
| Impact Simulation | 已有失效传播，缺变更前预测实现 | 只定义生成报告入口和声明边界；本次不声称已有模拟器 |
| AI Role Contract | executor/approver/reviewer/verifier 已分离 | 明确 AI 可起草和建议，不能批准、冻结或静默改需求基线 |
| Learning Loop | S7、复盘、资产升格已有 | 复用并建立需求反例回流入口，不新增第二套循环 |

## 3. 不新增第二套对象体系

功能级需求继续使用 `object_type: requirement`，通过 `requirement_kind` 区分：

```yaml
requirement_kind:
  - objective
  - business
  - functional
  - quality_attribute
  - constraint
```

这不是新的状态轴。`requirement_kind` 只表达需求语义类别；`approval_status`、`work_status`、`implementation_status`、`proof_level`、框架等级和治理配置继续互相独立。

## 4. 意图验证

每个功能需求必须保存四段意图：

```yaml
intent:
  original_intent: "来自批准来源的原始目标，或其稳定引用"
  interpreted_intent: "AI/分析者当前怎样理解"
  approved_intent: "人类责任人批准的业务意图"
  implementation_intent: "准备交给 ADR/Spec 的实现目标"
```

规则：

1. `original_intent` 必须能追溯到 Source、Fact 或上游 Requirement；
2. `interpreted_intent` 是候选解释，不能冒充批准事实；
3. `approved_intent` 只能由可验证人类责任人批准；
4. `implementation_intent` 不得扩大、替换或弱化 `approved_intent`；
5. 无法证明一致时保持 `waiting_approval` 或 `blocked`，不得生成 active Spec。

## 5. 功能需求卡

每个功能只有一份人类主要审查卡，不复制 Spec 五件套。机器 frontmatter 至少包含：

- 稳定 ID、`object_type: requirement`、`requirement_kind: functional`、版本和 canonical path；
- Function、Capability、业务 Requirement、业务链和场景引用；
- 四段意图、上下文快照引用、owner、approver、审批状态；
- `content_hash`、`supersedes`、基线与 Spec 引用。

正文固定回答：一句话结论、为什么需要、使用者与触发、正常流程、异常/拒绝/恢复、输入、输出、业务规则、非目标、数据/权限/风险、验收方向、已批准实现约束、候选实现要点、已有资产、未知与待确认、上下游影响、AI 生成自检和 Spec 映射。

“已批准实现约束”和“候选实现要点”必须分开。候选方案只有经过研究、比较和 ADR 才能进入工程设计。

## 6. 批准基线与禁止静默修改

项目级 Requirement Baseline 保存稳定 baseline ID、版本、状态、批准者、批准时间、需求 `stable_id/version/content_hash` 列表、范围 hash 和 `supersedes`。

基线一旦 approved：

- 不得原地改写需求内容、hash 或成员集合；
- 变更必须创建新需求版本或新 baseline，并用 `supersedes` 保留历史；
- 下游 ADR、Spec、Task、Evidence、Verdict、Claim 必须绑定精确 baseline；
- 删除、拆分、合并或降权必须形成 scope-change 和影响报告；
- AI 不能填写人类批准身份或把 draft 自动升格为 approved。

## 7. 上下文快照

`context_snapshot` 记录一次 AI 起草或审查实际使用的受控上下文：

```yaml
context_snapshot_id: CTX-001
included_files: []
excluded_files: []
exclusion_reasons: []
source_hashes: {}
generated_by: ai-node-id
approved_by: human-or-null
created_at: timestamp
content_hash: sha256
```

它只证明“本次 AI 看到了什么”，不证明内容正确。聊天、临时提示词和零碎笔记默认在 `excluded_files`；只有已经升格的正式资产才能驱动批准基线和下游 Spec。

## 8. L2 最小目录

标准 L2 模板新增：

```text
requirements/
├── README.md                              # 需求权威与操作说明
├── 项目地图.md                            # 人类每日入口；只引用正式资产
├── functions/
│   └── FUNC-001_功能需求卡.md             # 单功能需求权威
├── baselines/
│   └── REQ-BASELINE-001.yaml              # 批准需求集合与 hash
├── context/
│   └── CTX-001.yaml                       # AI 上下文快照
└── generated/
    └── README.md                           # 派生视图说明，不是事实源
```

`generated/` 未来可以生成当前审查队列、覆盖矩阵、Spec 状态和变更影响报告，但本次不实现生成器，也不预先创建伪造结果。

## 9. 阶段门禁调整

- S0：批准目标/业务需求和 `approved_intent`，建立第一版需求基线；
- S1：关键 Unknown 进入研究、决定或显式风险接受；
- S2：场景、链路、能力、功能和功能需求卡覆盖 P0/P1，功能需求完成 AI 自检与人工批准；
- S3：候选实现要点经研究与 ADR 转为已批准决策；
- S4：工程设计和 I/O 只能消费批准功能需求与 ADR；
- S5：Spec 必须引用功能需求版本/hash 和 Requirement Baseline；未批准、过期或意图不一致时 fail closed；
- S6/S7：运行反例、事故和学习进入上游复审，不直接覆写批准需求。

## 10. 风险自适应而不是全部项目重治理

- `lite`：允许 Goal/Requirement/Spec/Task/Test 的紧凑路径，但仍保留意图、批准基线、非目标和验收；
- `standard`：启用完整 Source/Fact/Unknown/Scenario/Chain/Capability/Function/Functional Requirement/ADR/Spec 追溯；
- 高风险或生产控制：使用现有 `standard + production` 及授权/审核控制，不新增 `critical` 基础 Profile。

## 11. 评分边界

历史讨论中的 `86.4`、`96.4` 和 `97.6` 都是不同范围下的专家设计估算，不是仓库当前总分，也不是已经形成的独立 Evidence。原方案 B 的 `95.93` 仍只代表当时批准设计目标。

本次实施后仍必须保持：

```yaml
current_overall_score: not_evaluated
general_95_plus: false
```

只有完整可重算维度、独立反方审查、跨项目隔离和第二异构 L2 等硬门禁满足后，才能形成新的当前数字。

## 12. 验收条件

1. 人类能从项目地图进入功能需求卡，不必先读 Spec 五件套；
2. 功能需求明确区分批准需求、批准实现约束和候选实现方案；
3. 四段意图、AI 自检、人工批准、版本/hash、baseline 和 supersedes 可静态验证；
4. Spec 不能引用未批准、过期或意图未对齐的功能需求；
5. 上下文快照不能把聊天或 `.prompts/` 自动升格为权威；
6. 正例覆盖完整人机需求链，反例覆盖意图漂移、未批准 Spec、静默基线修改和错误上下文；
7. 不新增平行状态轴、第三种基础 Profile、完整工作流平台或自动影响模拟器；
8. 当前总体评分保持 `not_evaluated`，不因文档或 fixture 通过而提升。
