# 受控对象模型

本文件是受控对象类型、公共字段、有类型关系和固定主追溯链的唯一权威源。

## 1. 固定主关系

```text
来源→批准事实/需求→人工批准治理规则→场景/触发→业务链路→业务能力/功能
→架构决策/技术能力/组件/工程链路→I/O与验收判据→Spec→Task
→Workflow→Skill/Tool→Run→Evidence→AI审核裁决→验收裁决→完成声明
→复盘与资产演进
```

R0、S0—S7 是成熟度坐标，不是这条因果链的节点或固定目录。Spec 是覆盖批准范围、计划、任务、验收和追溯的控制外壳，不是普通运行产物。

原始来源只能形成候选事实、假设或未知；经人类责任人批准后才可成为事实或需求。下游失败只能创建上游复审请求，不能直接修改批准事实。

关系边采用 allowlist：`source` 只能指向候选事实、假设、未知或研究输入；不得被 Spec、Task、Workflow、Skill、Tool 或执行节点直接 `consumes/implements/governed_by`。研究沙箱可以读取来源，但输出仍是候选对象，不能自行升格。

## 2. 公共字段

每个受控对象必须提供或明确标记不适用：

```yaml
stable_id: stable-id
object_type: requirement
canonical_path: path/to/authority
version: 1
governance_scope: l3
lifecycle_stage: S4
work_status: in_progress
approval_status: pending
implementation_status: not_started
owner: role-or-human-id
executor: role-or-tool-id
approver: human-or-policy-id
verifier: independent-role-or-gate-id
required_inputs: []
outputs: []
typed_relations: []
gate: gate-id
failure_routes: []
content_hash: sha256
route_decision_ref: route-id-or-null
control_set_ref: control-set-id-or-null
control_set_hash: sha256-or-null
proof_refs: []
stale_status: fresh
supersedes: null
```

`governance_scope` 使用 `l1/l2/l3`。仅 L3 执行和验收对象强制绑定项目路由；L1/L2 通用对象使用 null，靠自身版本、消费者和兼容契约治理。`route_decision` 自身不得引用自己，必须引用 routing policy、control set 和前一版本。

`lifecycle_stage`、`work_status`、`approval_status`、`implementation_status` 和 `stale_status` 的枚举与迁移只引用状态权威，不在本文件复制。实现状态不得由阶段、批准状态或 proof level 推导。普通对象只保存 `proof_refs`，有效 proof level 由 Evidence、Verdict 和 Claim 计算，禁止对象自证。

`owner` 对对象生命周期负责；`executor` 产生或修改内容；`approver` 批准规则、事实、需求、例外或动作权限进入受控状态；`verifier` 独立检验证据。普通运行内容由独立 AI reviewer 按已批准规则审核，不把 `approver` 解释为逐条内容审核者。高风险对象不得由同一 AI 同时承担生成、审核、验证和声明责任。

## 3. 类型矩阵

| `object_type` | 对象 | 关键关系与约束 | 类型专属状态字段（不代替公共坐标） |
|---|---|---|---|
| `source` | 原始来源 | 无权直接 `implements` Task/代码 | source_state: captured / quarantined / superseded |
| `fact` | 批准事实 | `derives_from source`；必须有 approver | —（使用公共审批、工作和失效坐标） |
| `requirement` | 批准需求 | `derives_from fact`；锁定验收分母 | —（使用公共审批、工作和失效坐标） |
| `assumption` | 假设 | 必须有验证期限和失败影响 | assumption_state: open / supported / rejected |
| `unknown` | 未知 | 必须有 owner、影响和处置路径 | unknown_state: open / researching / resolved / accepted_risk |
| `research` | 研究 | 服务明确 `blocks_decision`，报告不自动成为事实 | research_state: planned / active / decided / archived |
| `route_decision` | 项目治理路由裁决 | 绑定基础配置、逐 overlay 状态、routing policy 和 control set；不得自引用 | route_state: proposed / approved / expired / superseded |
| `control_set` | 项目控制集合 | 组合基础配置、overlay 模块、策略、契约和实现证据 | control_set_state: draft / approved / superseded |
| `governance_rule_set` | 人工治理规则集 | 权威正文为版本化 Markdown；active 版本必须绑定人类批准身份、scope、规则 ID 和内容 hash | rule_set_state: draft / approved / active / superseded / revoked |
| `scenario` | 场景 | `derives_from requirement` | —（使用公共坐标） |
| `trigger` | 触发 | 声明 actor、条件、入口和权限 | —（使用公共坐标） |
| `business_chain` | 业务链路 | 从场景/触发推导业务状态变化 | —（使用公共坐标） |
| `business_capability` | 业务能力 | 从业务链路推导，不含实现选择 | asset_state: candidate / active / deprecated / retired |
| `function` | 用户功能 | `implements business_capability` | asset_state: candidate / active / deprecated / retired |
| `architecture_decision` | 架构决策 | 记录选项、证据、后果、重审和替代 | decision: proposed / accepted / rejected / superseded |
| `technical_capability` | 技术能力 | 由决策和质量属性形成，不代替业务能力 | asset_state: candidate / active / deprecated / retired |
| `component` | 架构组件 | 实现技术能力，声明职责、接口、所有权和依赖 | asset_state: candidate / active / deprecated / retired |
| `engineering_chain` | 工程链路 | 分配代码、AI、人工和外部系统职责 | —（使用公共坐标） |
| `io_contract` | I/O 契约 | 版本化 Schema、失败语义和兼容规则 | contract_state: draft / active / deprecated |
| `acceptance_criterion` | 事前验收判据 | 先于 Run；映射需求和契约 | —（使用公共坐标） |
| `spec` | 规格控制外壳 | 不保存运行代码、真实数据、Run 或 Evidence | —（使用公共工作、审批和失效坐标） |
| `task` | 执行任务 | `implements spec`；不得凭空新增 | —（使用公共工作、审批和失效坐标） |
| `workflow` | 有状态编排 | 消费契约并声明恢复/取消路径 | asset_state: candidate / active / deprecated / retired |
| `skill` | 可复用局部能力 | 声明消费者、I/O、失败返回和权限 | asset_state: candidate / active / deprecated / retired |
| `tool` | 确定性执行器 | 受能力授权和副作用级别限制 | tool_registration_state: registered / enabled / disabled / revoked |
| `capability_grant` | 能力授权 | 精确绑定主体、资源、操作、项目路由与控制集；默认拒绝 | grant_state: pending / active / expired / revoked / consumed |
| `approval_ticket` | 审批票据 | 绑定一次具体副作用和不可变输入；禁止跨路由或重复消费 | ticket_state: pending / approved / consumed / expired / revoked |
| `secret_lease` | 秘密租约 | 短时、最小权限并绑定项目、主体、环境和控制集 | lease_state: pending / active / expired / revoked |
| `authorization_snapshot` | 授权快照 | 聚合并锁定主体、Grant/Ticket/Lease、职责分离、路由/control set、有效期与签名 | verification_status: pending / verified / rejected |
| `checkpoint` | 恢复检查点 | 引用原 Run、步骤位置、状态指纹和副作用账本；恢复创建新 Run | checkpoint_state: created / eligible / consumed / invalidated |
| `side_effect_operation` | 外部副作用操作 | 稳定 operation 与独立 attempt；未知结果先对账，禁止盲重试 | operation_state: prepared / approved / dispatched / acknowledged / reconciled / unknown / compensated |
| `run` | 一次执行事实 | 不可改写历史结果 | run_state: created / running / waiting_approval / succeeded / failed / cancelled |
| `evidence` | 可复现证据 | `produced_by run/verification`；有新鲜度 | verification_status: captured / verified / rejected |
| `ai_review_verdict` | AI 自动审核裁决 | 独立审核节点依据 active 规则集逐项引用 `rule_ref`；人工授权不能覆盖 blocked 结论 | decision: pending / allow / rewrite_required / blocked / rule_gap |
| `rule_gap_case` | 规则缺口记录 | 规则不足时阻断当前对象，异步路由给人类规则 owner，不转为逐条人工内容审核 | gap_state: open / rule_revision_active / resolved / superseded |
| `overlay_activation_verdict` | 叠加能力激活裁决 | 只裁决 control set 是否可激活，不代替业务验收 | decision: pending / accepted / rejected / revoked |
| `acceptance_verdict` | 事后验收裁决 | 只引用事前判据和 Evidence | decision: pending / accepted / rejected / conditional / revoked |
| `completion_claim` | 完成声明 | 受 Verdict 和最低 proof_level 封顶 | claim_status: draft / issued / expired / withdrawn |
| `retrospective` | 复盘 | 记录结果、反例、成本和改进候选 | retrospective_state: draft / accepted / archived |
| `asset_lifecycle` | 资产生命周期记录 | 管理模板/Workflow/Skill/Tool 的升降级 | lifecycle_record_state: candidate / active / deprecated / invalidated / superseded / retired |

## 4. 关系类型

`derives_from`、`governed_by`、`implements`、`consumes`、`produces`、`produced_by`、`reviewed_by`、`verified_by`、`authorized_by`、`approved_by`、`identifies_gap_in`、`checkpoint_of`、`resumes_from`、`attempt_of`、`invalidates`、`supersedes`、`requests_review_of`。

每个活跃对象只有一个 `canonical_path`，但可以有多个有类型上游。禁止把“唯一权威位置”误解为“只能有一个父节点”。

## 5. 检查器不变量

1. `stable_id + version` 唯一且 `canonical_path` 存在；L3 执行/验收对象绑定当前有效路由裁决和控制集，L1/L2 对象不得伪造项目路由引用。
2. 来源不得绕过批准事实/需求直接驱动 Spec、Task、Workflow、Skill、Tool 或实现。
3. P0/P1 需求必须覆盖场景、链路、验收判据、Spec、Evidence 出口和 Verdict。
4. 业务能力与技术能力不得使用同一对象类型。
5. Task 必须来自已批准 Spec；Run 必须引用 Task/Workflow 及版本。
6. Completion Claim 必须引用有效 Verdict，且不得超过关键路径最低 proof_level。
7. 上游变化必须触发下游闭包影响分析。
8. L3 的 Capability Grant、Approval Ticket、Secret Lease、Checkpoint 和 Side-effect Operation 必须绑定当前 `route_decision_ref`、`control_set_ref` 与 `control_set_hash`；引用过期路由时禁止继续授权、恢复或执行副作用。
9. 授权快照只有在底层授权全部有效、引用/hash 一一对应、职责分离通过且验证 Evidence 新鲜时才可供激活或验收使用；非空引用不代表有效。
10. active `governance_rule_set` 必须引用 Markdown 权威、非空规则 ID、精确 scope、内容 hash 和可验证的人类批准 principal。
11. `ai_review_verdict=allow` 必须绑定 subject/rule set hash、非空规则覆盖和新鲜 Evidence；每项 finding 必须引用可解析的 `rule_ref`。
12. `rewrite_required` 必须有正整数上限并保留全部 attempt；上限耗尽只能转 blocked。
13. `rule_gap` 必须创建 `rule_gap_case` 并阻断当前对象；人工授权不得覆盖 blocked AI Review Verdict。

## 6. Spec 包和需求分母

Spec 包使用一个 `spec_id/version` 覆盖 `spec.md`、`plan.md`、`tasks.md`、`acceptance.md`、`traceability.md`。包级批准必须绑定所有成员文件的内容 hash；任一成员变化都使包进入待复核，禁止局部批准后仍沿用旧完成声明。

风险自适应裁剪必须记录省略项、理由、批准者和 claim ceiling。无论如何不得省略批准需求分母、非目标、事前验收判据、需求到 Task/Evidence 的追溯和禁止声明。

每次验收和声明绑定不可变 `requirement_baseline_id`、需求版本集合与权重 hash。P0/P1 需求不得为零权重。批准需求集合的新增、删除、拆分、合并、退休或权重变化必须产生 scope-change 记录，包含人工批准、前后分母差异和 Claim 影响；未批准删减仍留在分母并视为未完成。Task 取消不能静默删除或降权需求；变更后旧 Evidence、Verdict 和 Claim 按失效传播处理。

## 7. Task、Workflow、Skill 和 Tool 边界

Task 至少记录：`task_id`、`spec_ref/version`、`requirement_refs`、`criterion_refs`、输入/输出契约、依赖、executor、权限、失败路由和 Evidence 出口。孤儿 Task 或无 Task 覆盖的 P0/P1 需求必须阻断门禁。

Workflow manifest 至少记录：`workflow_id/version`、trigger、Task、step graph、每步 execution node、输入/输出/失败契约、权限、超时、重试、checkpoint、取消、补偿、终态、Evidence 出口和 claim ceiling。Workflow 拥有控制流，不保存业务事实，也不把完整工作流隐藏成一个 Tool。

声明 `review_mode: ai_automated` 的 Workflow 必须引用 `governance_rule_set` 与 `ai-review-verdict-contract`，并提供 allow、自动改写、安全阻断和规则缺口四条终止路径。普通审核不得进入 `waiting_approval`；人工等待只用于规则/事实/需求批准、例外、剩余风险和动作授权。

Skill 是版本化局部能力契约，可以组合确定性代码或模型推理，但不得隐藏跨阶段编排、无限重试、未声明权限或验收裁决。Tool 是最小可审计执行接口，保证调用协议、错误分类、权限和回执可验证；外部结果本身可能非确定。Skill/Tool 均不能签发 Verdict 或 Claim。

## 8. I/O 和失败契约

I/O Contract 至少包含：`contract_id/version`、producer/consumer、request/event/result Schema、成功/失败 envelope、错误分类、`retryable`、幂等作用域、timeout、ordering/delivery、partial/null 语义、数据分类、兼容范围、contract test 和迁移规则。

`failure_routes` 的每项至少包含：`failure_class`、`source_step`、`condition`、`error_contract_ref`、`retryable`、`max_attempts`、`backoff`、`next_state`、checkpoint policy、approval requirement、compensation、claim ceiling 和 terminality。业务拒绝、契约错误、技术失败、预算耗尽、权限拒绝和未知外部结果不得混成一个“成功但无结果”。
