# L2 业务系统端到端推进 SOP

本文件是“一个 L2 业务系统接入 L1 后，怎样从项目识别推进到 R0、S0—S7，并在失败时重开”的唯一操作路线图。它面向 L2 owner、架构师、执行者和 verifier；开始推进新的或存量 L2 时阅读。读完后应产出当前阶段定位、该阶段必需产物、门禁结果、Evidence 位置和失败重开目标。

本文件只编排既有权威，不复制第二套定义：

- 首次接入步骤只由 [L2_ONBOARDING.md](L2_ONBOARDING.md) 定义；
- 项目类型和治理路由只由 [PROJECT_TYPE_AND_GOVERNANCE_ROUTING.md](PROJECT_TYPE_AND_GOVERNANCE_ROUTING.md) 定义；
- R0、S0—S7 的阶段语义只由 [PROJECT_LIFECYCLE.md](PROJECT_LIFECYCLE.md) 定义；
- 工作状态和失效传播只由 [STATE_TRANSITIONS_AND_INVALIDATION.md](../governance/STATE_TRANSITIONS_AND_INVALIDATION.md) 定义；
- 门禁公式和 proof level 只由 [GATES_PROOF_SCORING.md](../governance/GATES_PROOF_SCORING.md) 定义；
- Run、Evidence、Verdict 和 Claim 只由 [RUN_EVIDENCE_ACCEPTANCE.md](../governance/RUN_EVIDENCE_ACCEPTANCE.md) 定义。

## 1. 总路线

```text
识别待推进的 L2 业务系统
→ 按 L2_ONBOARDING 锁定兼容 L1 版本
→ 建立原始来源与批准事实/需求的边界
→ 计算 project_type、base governance profile 和 required overlays
→ brownfield 先进入 R0；其他类型进入对应起点
→ 按 R0 / S0—S7 逐阶段产出和过门禁
→ 每次执行保存 Run/Evidence/Verdict，声明受最低有效 proof level 封顶
→ 失败时保留历史，做影响分析并重开正确的上游阶段
→ 运行经验留在 L2；只有通过跨项目升格门禁的结论才进入 L1
```

阶段不是必须一次走完的瀑布。多个工作包可以处于不同阶段，但每个工作包都必须记录自己的阶段、状态、批准、实现、Evidence 和失效坐标。

## 2. 进入 R0/S0 前的接入门

1. 在 L2 根目录创建并填写 `project-os.lock.yaml`，锁定 L1 版本、兼容范围和实际消费的协议。
2. 分离原始来源与批准事实/需求；Spec 不得直接追溯到未批准来源。
3. 使用结构化输入生成项目类型和治理路由裁决；信息不足时不能靠业务关键词猜测。
4. 只有存在需要独立治理的多个实例时才创建 `projects/{project_id}/` L3 namespace。
5. 运行 `--l2-mode --report`；`EXIT=0` 只是进入阶段推进的必要条件。
6. 接入检查 Evidence 保存在 L2 自己的 `reviews/`，不得把具体路径反写进 L1。

接入失败时留在接入门：修复锁定、批准对象或 traceability 后重新运行检查，不得通过 L1 白名单绕过。

## 3. R0、S0—S7 操作表

| 阶段 | 本阶段做什么 | L2 产出什么 | 卡哪个门禁 | 失败后重开 |
|---|---|---|---|---|
| `R0` | 冻结并清点现有入口、代码、契约、测试、运行资产；反向恢复来源和需求 | 当前架构、入口清单、反向需求、孤儿实现、差距矩阵、迁移计划 | `PROJECT_LIFECYCLE.md` 的 R0 退出门：关键实现有来源或明确标记为孤儿 | 发现遗漏入口、事实源或运行资产时留在 R0；不能用后续设计覆盖未知现状 |
| `S0` | 明确目标、非目标、角色、成功指标、需求分母、项目类型和治理路由初判 | 目标与范围、需求基线、owner/approver、route decision v1 | S0 退出门：目标负责人、范围和验收方向明确；路由输入未知项有处置路径 | 目标、范围或责任不清时重开 S0；商业目标变化也回到 S0 |
| `S1` | 审计来源，区分事实/假设/未知，完成阻断当前决策的研究 | 来源清单、术语、批准事实、假设、未知、研究包、研究 Verdict | S1 退出门：关键未知不再阻断当前决策，结论有来源或实验 | 新来源、法规、技术前提或反例出现时重开 S1；未解决未知只阻断所依赖的决策 |
| `S2` | 从批准需求推导场景、触发、正常/异常/恢复链路和业务能力 | 场景目录、触发档案、业务链路、责任映射、能力视图 | S2 退出门：P0/P1 需求都有场景、链路、失败出口和责任主体 | 事实不足回 S1；场景、触发或恢复链缺口留在 S2；不得直接跳到工程实现 |
| `S3` | 比较候选方案，验证质量属性，完成反方审查和架构决策 | 候选方案、实验 Evidence、评分输入、反方报告、ADR、目标架构 | S3 退出门：关键选择有证据、后果、退出和重审条件 | 证据不足回 S1；业务链错误回 S2；方案被反证时在 S3 新建替代 ADR，不改写历史 |
| `S4` | 定义组件、工程链路、I/O、失败语义、权限、隔离、兼容和验收判据 | 组件边界、engineering chain、I/O contract、权限模型、acceptance criteria | S4 退出门：接缝、失败态、权限、兼容和回滚可验证 | 架构前提错误回 S3；契约或边界不完整留在 S4；外部接口变化重开受影响的 S4 对象 |
| `S5` | 从 Spec 和验收倒推任务，建立 Workflow、Skill/Tool 和最小纵向实现 | Spec 五件套、Task 依赖图、Workflow、Skill/Tool、实现与 checkpoint 方案 | S5 退出门：无孤儿任务，工作包可执行、暂停、恢复和失败返回 | 契约不足回 S4；任务或实现问题留在 S5；依赖阻断记录为 blocked，不伪造 completed |
| `S6` | 执行测试和 Run，收集 Evidence，完成 AI 审核、验收裁决、发布与回滚决定 | 测试报告、Run、Evidence、AI Review Verdict、Acceptance Verdict、发布决定 | S6 退出门：结构与语义断言、P0/P1、追溯、新鲜度和 proof level 全部满足声明 | 契约失败回 S4；实现失败回 S5；目标错误回 S0；Evidence 过期则重跑验证，不改写旧 Run |
| `S7` | 观察真实结果、成本、事故与恢复，做复盘、升降级和资产演进 | 指标、事故/恢复记录、复盘、迁移、废弃或资产升格申请 | S7 运行门：真实结果、责任、恢复和声明边界持续成立 | 假设错误回 S1/S2；架构反证回 S3；接口变化回 S4；事故使相关 Evidence/Verdict/Claim 失效 |

## 4. 每阶段统一执行循环

```text
确认阶段输入和治理路由仍有效
→ 产生或更新该阶段受控对象
→ 做影响分析，标记受影响下游
→ 执行事前定义的检查和审核
→ 保存不可改写 Run 与原始 Evidence
→ 依据判据形成 Verdict
→ 只在 Verdict 接受且 Evidence 新鲜时签发受限 Claim
→ 记录下一阶段或重开目标
```

门禁通过必须调用 `GATES_PROOF_SCORING.md` 的统一公式。不能用文件存在、`EXIT=0`、AI 自评或人工口头确认替代语义不变量、追溯完整性和 Evidence 新鲜度。

## 5. 失败、重开与恢复

失败不是删除历史后重来。每次失败至少记录：失败对象和版本、当前阶段、失败 Run/Evidence、影响范围、owner、修复阶段、重开条件和禁止继续的声明。

```text
失败或上游变化
→ 计算有类型关系的下游影响闭包
→ unaffected / review_required / invalidated 分类
→ 撤销或挂起受影响 Verdict/Claim
→ 回到最早被反证的阶段修正
→ 生成新版本、新 Run 和新 Evidence
→ 全部门禁重新成立后恢复声明
```

`retry` 必须创建新 Run；`resume` 必须重新验证 checkpoint、输入、权限和外部状态。未知外部副作用先对账，不得自动重发。

## 6. Evidence 和资产所有权

Evidence 保存在 L2 自己的 `reviews/`、`runs/` 或该 L2 正式定义的等价位置。L1 不读取具体 L2 仓库，也不登记具体业务路径。

L2 经验要升格为 L1 通用资产，必须具备至少两个异构消费者、跨项目隔离证据、通用命名、反例测试、维护责任、兼容范围和独立反方审查。单项目通过只能证明该范围内的 L2 结果。

## 7. 完成边界

走到某个阶段不自动表示实现、验证或生产就绪。完成声明必须绑定对象版本、需求基线、环境、route/control set、Evidence、Verdict、验证命令、有效期和禁止外推范围；其上限取关键路径最低有效 proof level、Verdict ceiling 和降级 ceiling 的最小值。

接入完成后，从本 SOP 定位当前阶段；阶段内具体对象和机器字段继续回到各自权威文件，不在本文件维护副本。
