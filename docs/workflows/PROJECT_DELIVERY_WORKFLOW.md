# 项目交付工作流

| 阅读契约 | 内容 |
|---|---|
| 解决的问题 | 把需求种子或存量系统转换为可追溯的工程交付与完成声明。 |
| 何时阅读 | 启动项目、恢复存量架构、拆解 Spec、执行验收或上游变化需要重开时。 |
| 输入 | 受控来源或存量资产、项目约束、未知项、当前需求基线和 Evidence。 |
| 输出 | 类型与治理路由、阶段位置、业务/工程链、通过决策门的功能需求、Spec/Task、执行记录、裁决与复盘去向。 |
| 下一步 | 先按本文定位工作节点，再到[阶段退出门禁](STAGE_EXIT_GATES.md)判断是否允许推进。 |

本文是推进控制流的人类权威视图。对象字段与固定关系以[受控对象模型](../governance/CONTROLLED_OBJECT_MODEL.md)为准；本文不建立第二份对象枚举。

## 1. 固定推进顺序

```text
来源/存量恢复 → 项目类型 → 治理路由 → 生命周期阶段 → 研究 → 业务链路 → 能力树 → 功能树 → 功能级需求 → 决策门与需求基线 → 行为规格 → 按需 ADR → 测试空间/工程链路 → Spec/Task → Workflow → Skill/Tool → Run → Evidence → Verdict → Claim → 复盘/升格
```

这是一条依赖链，不是阶段瀑布。没有未知项时研究可以记录为不适用；只有存在架构选择、既有决策变化或需要替代关系时才产生/更新 ADR，没有架构选择时 S3 记录 `not_applicable` 理由后继续。任何节点都不能通过省略上游引用来制造孤儿交付物。

## 2. 从入口到治理路由

1. **批准需求或存量恢复**：新建型项目从已批准需求进入；存量恢复型项目先做 R0，识别活动入口、现状架构、历史来源、孤儿实现和迁移差距。
2. **项目类型**：根据工作对象判断 `greenfield`、`brownfield`、`research_only` 等类型。类型只回答“当前工作是什么”。
3. **治理路由**：根据风险、敏感度、外部副作用和运行要求选择基础治理配置与叠加能力。路由只回答“采用哪些控制”，不表示控制已实现或激活。
4. **生命周期阶段**：把每个受控对象定位到 R0 或 S0—S7。阶段回答成熟度位置，不代替工作状态、实现状态或 Evidence。

类型与路由的机器条件只由[项目类型与治理配置路由](PROJECT_TYPE_AND_GOVERNANCE_ROUTING.md)定义。

## 3. 从认知到业务设计

1. 把原始来源分成候选事实、假设和未知；只有通过合法 Decision Gate 后才形成受控事实或需求。
2. 研究只解决明确阻断的决策，输出研究 Evidence、研究 Verdict 或候选 ADR；研究不能自行批准业务事实。
3. 场景和触发从批准需求推导，业务链路描述参与者、状态变化、正常分支、异常分支与恢复路径。
4. **能力树从业务链路推导**：它表达业务为了完成链路必须具备什么，不先绑定组件、模型、工具或目录。
5. 功能树把业务能力转成用户可观察功能；它仍不等于任务清单。
6. 每个 Function 展开为一份人类优先的功能需求卡，先确认意图、触发、规则、边界、异常、输入输出、风险和验收方向。
7. AI 生成的 draft 不能自行升格。AI 先报告缺口、假设、可能错误和待确认项，再由独立审核与 Decision Gate 选择 `policy_certified`、`human_signoff` 或 blocked。低风险自动路径必须引用当前审核策略认证；高风险变化仍由人类确认。
8. 决策门批准功能需求并形成当前 Requirement Baseline 后，S2 形成父级 **Behavior Specification** 与稳定 **Behavior Case** 总表：前者说明问题、用户可观察目标、行为规则、非目标、owner/approver、假设/未知和适用性；后者按主路径、边界、反例、失败恢复记录代表性触发、预期用户可观察行为和覆盖目标。
9. Specification by Example 与 Example Mapping 用于精炼规则、案例和未知；BDD/ATDD/TDD 在后续消费稳定 Behavior Case ID，不能自行批准新的业务语义。brownfield 或需求变更可增加可选 As-Is/To-Be Gap Analysis，但它不是新阶段。

Behavior Specification 和 Behavior Case 都是执行前对象，禁止写入 `actual_result`、`passed`、`evidence_ref` 或 Run ID。代码、测试、原因假设、验证方法和实际结果变化不改稳定 Behavior Case ID；只有批准的用户目标、范围或期望行为变化才升级父级行为规格版本，新增独立边界优先新增案例。

固定推导顺序是：`业务链路 → 能力树 → 功能树 → 功能级需求 → 决策门与需求基线 → 行为规格 → 按需 ADR → 测试空间/工程链路 → Spec`。详细审查步骤见[人机协作需求设计工作流](REQUIREMENT_DESIGN_WORKFLOW.md)，审核策略怎样测试和认证见[审核策略认证](../governance/REVIEW_POLICY_CERTIFICATION.md)。

研究方法见[研究工作流](../research/RESEARCH_WORKFLOW.md)。

## 4. 从行为到验收与可执行工作包

1. S3 只有存在架构选择时才用 ADR 记录候选、取舍、Evidence、后果、退出条件和替代关系；行为规格本身不强制制造 ADR。
2. S4 把 Behavior Case 与已批准 `semantic_inventory_ref`、规则和约束输入 **Test Space Modeling**，使用等价类、边界值、决策表、pairwise/受约束组合、对比/变形关系和失败恢复 oracle 形成验收覆盖矩阵。每个覆盖项声明输入、中间治理对象、预期决策、可观察输出、验证方法、最低证明范围和未覆盖空间。
3. L2 profile 把已批准清单绑定为通用 `inventory partition/member` 与 `per_partition/per_member` 覆盖义务；checker 对每个适用成员逐项闭合，再从维度 domain、通用禁配和派生 combination registry 重算全部允许二元组合，不得只挑 canonical example 或保留固定计数。AI 可依据批准语义生成候选反例，但不能批准新业务语义。风险、约束冲突或低成本全组合触发时，从 pairwise 升级到受约束全组合。
4. 工程链路根据批准功能需求、当前架构约束和适用时的已接受 ADR 分配人工、AI、代码与外部系统职责，配套 I/O、失败、权限、兼容和验收出口。
5. S5 的 Spec 是批准范围、计划、任务、验收与追溯的控制外壳；它必须精确绑定功能需求版本/hash 和当前 Requirement Baseline，并让 Spec、Task、BDD/ATDD/TDD 引用稳定 Behavior Case ID 与 coverage/criterion。它们都不是运行节点。
6. **任务树从已批准的 Spec 与验收判据推导**。每个 Task 必须引用具体需求、Behavior Case、判据、输入输出、依赖、失败路由和 Evidence 出口；禁止从能力树、功能树或头脑风暴直接生成无来源 Task。

能力树回答“业务需要什么”，任务树回答“为了满足已批准 Spec 要做什么”；两者不能互相替代。

验收覆盖矩阵只记录预定方法、`coverage_status` 和最低证明范围；`verification_mapped` 仅表示已有验证实现映射，不表示本次执行通过。实际 observation、pass/fail 和证据引用只在 S6 进入 Run/Evidence/Verdict/Claim。fixture、local、UI simulation、readonly real、platform accepted、terminal delivered 与 production proof 不得互相替代。

## 5. Workflow、Skill 与 Tool 的边界

- **Workflow 编排 Task**：拥有步骤图、顺序、分支、超时、重试、暂停、恢复、取消、补偿与终态；不得保存业务事实。
- **Skill 是局部、可复用的能力**：声明消费者、输入输出、权限和失败返回，可以组合代码或模型推理，但不得隐藏跨阶段控制流。
- **Tool 是最小可审计执行接口**：负责具体调用协议、错误分类、权限和回执；外部结果可能非确定，因此 Tool 自报成功不等于验收通过。

普通 Workflow、Skill 或 Tool 均不能自行签发业务 Acceptance Verdict 或 Completion Claim。

## 6. 从执行到声明

1. **Run** 保存一次不可改写的执行事实，记录版本、输入与环境指纹、执行结果、检查点、副作用和已知失败。
2. **Evidence** 根据事前判据收集可重放材料；它必须绑定 Run 或独立验证动作，并记录范围与新鲜度。
3. **Verdict** 由授权且满足职责分离的 verifier 对判据和 Evidence 裁决；执行成功不自动等于验收接受。
4. **Claim** 只能引用有效 Verdict，且不得超过关键路径最低证据边界。
5. **复盘/升格** 记录结果、成本、失败和候选改进。通用资产只有经过跨项目升格门禁，才能从下层项目进入 L1。

Run、Evidence、Verdict 与 Claim 的字段只由[Run、Evidence、验收裁决与完成声明](../governance/RUN_EVIDENCE_ACCEPTANCE.md)定义。

## 7. 失败、暂停和重开

失败 Run 不得原地改成成功。重试创建新 Run；暂停必须形成 checkpoint；恢复前重新验证输入、版本、授权和外部状态。上游事实、需求、路由、契约或 Evidence 变化时，沿依赖闭包标记下游待复核或失效，并重开最早受影响目标。具体传播规则见[状态迁移与失效传播](../governance/STATE_TRANSITIONS_AND_INVALIDATION.md)。
