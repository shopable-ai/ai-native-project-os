# AI Project OS 术语权威

| 阅读契约 | 内容 |
|---|---|
| 解决的问题 | 为人类提供唯一中文定义和稳定 `term-id`，避免同名术语跨框架、治理、工程和证明轴混用。 |
| 何时阅读 | 新增权威文档、设计字段、评审歧义或解释项目进度时。 |
| 输入 | 现有机器字段及其唯一语义权威。 |
| 输出 | 可稳定引用的中文术语定义与边界。 |
| 下一步 | 使用 `term-id` 引用概念；需要机器枚举时回到每个条目链接的唯一权威，不在本文复制枚举。 |

框架版本等级与治理配置互相正交。生命周期阶段、工作状态、审批状态、实现状态、证据等级、失效状态互相正交。任何一个坐标都不能推出另一个坐标；“已选”“已批准”“已完成”“已实现”“已证明”和“当前有效”不是同义词。

同名消歧：裸写 `standard` 不具备完整语义。描述 L1 产品能力范围时必须写“`standard` 框架版本等级”（`framework edition`）；描述项目最低控制组合时必须写“`standard` 基础治理配置”（`base governance profile`）。

## 1. 分层与状态

### 来源
term-id: `source`

尚未升格的原始输入或历史材料，只能形成候选事实、假设、未知或研究输入。来源没有批准权，不得直接驱动 Spec、Task、Workflow 或实现。

### 业务真相
term-id: `business-truth`

经合法 Decision Gate 接受、进入受控基线的业务事实或需求，是场景、链路、Spec 与验收的追溯起点。低风险对象可由当前认证策略裁决，高风险变化由可追责人类确认；研究结论和运行输出不能自行升格。

### 研究
term-id: `research`

为解决明确未知或阻断决策而执行的可审计活动，输出研究包、Evidence、研究 Verdict 或候选 ADR。研究不等于事实批准，也不能把候选工具变成既定依赖。

### 框架版本等级
term-id: `framework-edition`

L1 产品能力范围，回答“这版 AI Project OS 设计要提供哪些通用能力”。它不表示某项目采用何种治理，也不表示能力已经实现。机器定义见[框架版本等级](../architecture/FRAMEWORK_EDITION_MODEL.md)。

### 项目治理配置
term-id: `governance-configuration`

某个项目根据风险、复杂度和运行要求选择的控制组合，包括基础配置与可叠加能力，回答“这个项目受哪些控制”。它不是框架版本等级。机器路由见[项目类型与治理配置路由](../workflows/PROJECT_TYPE_AND_GOVERNANCE_ROUTING.md)。

### 基础治理配置
term-id: `base-governance-profile`

项目必须选择的一组最低通用控制，回答“无论是否启用附加能力，最少执行哪些治理”。其中 `standard` 指治理配置，不是同名框架版本等级。

### 叠加能力
term-id: `overlay-capability`

在基础治理配置之上、因协作或生产风险按条件选择和激活的附加控制。`required`、`selected`、`enabled` 分别表示风险要求、项目选择和有效运行激活，不能互相替代。

### 仓库所有权层级
term-id: `repository-layer`

大写 `L1/L2/L3` 表示仓库所有权和依赖方向：L1 通用协议、L2 业务系统、L3 项目实例。它不表示治理范围、框架等级或生命周期。唯一机器语义见[仓库与层级契约](../architecture/REPOSITORY_AND_LAYER_CONTRACT.md)。

### 治理范围
term-id: `governance-scope`

小写 `l1/l2/l3` 只作为受控对象字段 `governance_scope` 的机器枚举值，表示对象适用的治理范围。它不是大写仓库层级的可互换写法；字段约束见[受控对象模型](CONTROLLED_OBJECT_MODEL.md)。

### 生命周期阶段
term-id: `lifecycle-stage`

受控对象当前成熟度位置，使用 R0 或 S0—S7 的坐标语义。阶段可并行、回退和重开，不是目录、工作状态或完成证明。定义见[项目生命周期](../workflows/PROJECT_LIFECYCLE.md)。

### 工作状态
term-id: `work-status`

工作项在排队、进行、阻断、暂停、失败、完成、替代或退休等处理过程中的位置。它不表达实现是否存在，也不表达验收是否通过。唯一迁移见[状态迁移与失效传播](STATE_TRANSITIONS_AND_INVALIDATION.md)。

### 审批状态
term-id: `approval-status`

治理对象或动作授权是否待处理、获批、拒绝、过期或撤销的独立坐标。审批通过不表示内容审核通过、实现完成或 Evidence 有效。

### 批准路由
term-id: `approval-route`

说明批准结果由哪一种受控路径产生：通过有效认证与激活 Policy 的策略决策，或由可验证人类完成的高风险确认。它不是审批状态、工作状态或证据等级；两条路径都必须绑定 Decision/Evidence，且不能替代外部动作授权。

### 实现状态
term-id: `implementation-status`

受控对象对应实现是否不存在、部分存在或已满足实现验收的独立坐标。文档存在、阶段前进和审批通过都不能自动提升实现状态。唯一枚举见[状态迁移与失效传播](STATE_TRANSITIONS_AND_INVALIDATION.md)。

### 证据等级
term-id: `proof-level`

某项 Claim 所依赖 Evidence 的最低证明边界。高等级不能由名称自证，且关键路径最低等级封顶声明。唯一机器枚举见[门禁、证据等级与评分](GATES_PROOF_SCORING.md)。

### 失效状态
term-id: `invalidation-status`

对象或 Evidence 对当前基线是否仍可用的独立坐标。上游变化可以使历史结果进入待复核、过期或失效，但不得改写历史 Run 或历史裁决事实。

## 2. 链、树和工程拆解

### 业务链路
term-id: `business-chain`

从批准需求、场景和触发推导的业务状态变化，包含参与者、正常、异常与恢复路径，不绑定具体代码组件。

### 工程链路
term-id: `engineering-chain`

根据已接受 ADR 和工程设计，把业务链路分配到人工、AI、代码、组件和外部系统的责任与交接，必须声明 I/O、失败、权限和回执。

### 能力树
term-id: `capability-tree`

从业务链路推导的业务能力层次，回答“业务必须具备什么”。它不是功能页面树、组件树或任务计划。

### 功能树
term-id: `function-tree`

把业务能力展开为用户或调用方可观察的功能，回答“能力以什么行为被使用”。它不产生无来源 Task。

### 意图验证
term-id: `intent-verification`

把来源中的原始意图、AI/分析者的候选解释、Decision Gate 接受意图和准备进入实现的意图分别保存并校验一致性。它防止“正确实现错误目标”，不是审批状态或实现状态。

### 功能需求
term-id: `functional-requirement`

面向单个 Function 的人类主要审查单元，说明为什么需要、谁在何时使用、正常/异常/恢复、输入输出、规则、边界、风险和业务验收方向。机器上仍使用 `object_type: requirement` 与 `requirement_kind: functional`，不是新的对象平面。

### 需求基线
term-id: `requirement-baseline`

经合法批准路由接受并锁定的需求 `stable_id/version/content_hash` 集合与范围 hash。基线同时绑定决策权威以及认证 Verdict 或人工签署；变更创建新版本并 `supersedes` 旧基线。

### 上下文快照
term-id: `context-snapshot`

记录某次 AI 起草或审查实际包含/排除的文件、理由、hash 和生成身份，使输入范围可重放。它不把聊天或提示词升格为事实，也不证明输出正确。

### 项目地图
term-id: `project-map`

L2 面向人的当前导航，聚合目标、阶段、核心链路、能力/功能、批准需求、决策、风险、Unknown 和下一步的稳定引用。它不复制需求正文、状态枚举或任务权威。

### 审核策略包
term-id: `review-policy-bundle`

由规则集、Prompt、输入输出 Schema、Context 策略、模型 fingerprint、Tool/权限边界、改写上限和失败出口共同组成的可重放审核对象。Prompt 只是装配载体，不是规则权威。

### 审核策略认证
term-id: `review-policy-certification`

针对审核策略包执行预注册正例、反例、边界、对抗和恢复测试，依据全部 Run/Evidence、指标与阈值作出有范围和有效期的认证 Verdict。认证通过只允许按激活 Policy 使用，不授予外部动作权限。

### 任务树
term-id: `task-tree`

从已批准 Spec 与验收判据生成的执行依赖图。单个 Spec 的 `tasks.md` 是该 Spec 的任务权威，跨 Spec 总树只能是可重建视图。

### 行为规格
term-id: `behavior-specification`

在 S2 从已批准 Requirement、场景和业务链路形成的执行前规格，说明为什么做、用户或调用方应观察到什么、行为规则、非目标、责任、假设与未知。Specification by Example 和 Example Mapping 可用于消除歧义；它们不把行为规格变成测试结果，也不替代 S5 的 TDD。

### 行为案例
term-id: `behavior-case`

隶属于父级行为规格、具有稳定 `case_id` 的代表性主路径、边界、反例或失败恢复目标。案例只保存执行前的用户可观察期望和覆盖目标；代码、测试、原因假设或实际结果变化不改变 `case_id`，只有批准的用户目标、范围或期望行为变化才升级父级行为规格版本。

### 测试空间建模
term-id: `test-space-modeling`

在 S4 从已批准语义清单、行为规则、等价类、边界、决策条件、组合约束和失败恢复系统派生验收覆盖的活动。它可使用 Equivalence Partitioning、Boundary Value Analysis、Decision Table、Pairwise/Combinatorial、Contrastive/Metamorphic Testing；产物是事前覆盖设计与证明上限，不是 Run、Evidence 或通过结论。

## 3. 执行资产

### Workflow
term-id: `workflow`

编排 Task 的版本化控制流，拥有步骤、分支、超时、重试、checkpoint、取消、补偿、终态和 Evidence 出口；不保存业务事实。

### Skill
term-id: `skill`

面向明确消费者的局部、可复用能力契约，声明输入输出、失败返回和权限；不得隐藏完整 Workflow 或跨阶段编排。

### Tool
term-id: `tool`

最小可审计执行接口，保证调用协议、错误分类、权限和回执可验证；不保证外部结果确定，也不能自行签发验收裁决。

### Spec
term-id: `spec`

覆盖批准范围、计划、任务、验收和追溯的控制外壳。它锁定工程工作包，不是 Run、Evidence 或业务事实源。

## 4. 执行、证据与声明

### Run
term-id: `run`

一次不可改写的执行事实，绑定版本、输入和环境指纹、执行结果、checkpoint、副作用及已知失败。执行成功不等于验收通过。

### Evidence
term-id: `evidence`

针对事前判据采集、可定位来源并声明范围与新鲜度的验证材料。Evidence 必须绑定 Run 或独立验证动作，不能仅由被验证对象自报。

### Verdict
term-id: `verdict`

授权 verifier 对明确对象、事前判据和 Evidence 做出的裁决。AI 内容审核裁决、叠加能力激活裁决和业务验收裁决职责不同，不能互相替代。

### Claim
term-id: `claim`

面向明确范围、环境和有效期的完成声明。Claim 必须引用有效 Verdict，受关键路径最低证据等级、未覆盖范围和失效传播封顶。

以上对象的字段、类型和关系以[受控对象模型](CONTROLLED_OBJECT_MODEL.md)为准；本文只维护中文定义，不复制类型矩阵。
