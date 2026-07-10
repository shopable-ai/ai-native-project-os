# 项目类型与治理配置路由

本文件是项目类型、基础治理配置、可叠加能力和版本化路由裁决的唯一权威源。项目类型回答“当前工作是什么”；基础治理配置回答“最低采用哪组通用控制”；叠加能力回答“是否需要多智能体协作或生产运行控制”。它们都不是框架版本等级、R0/S0—S7 阶段或 proof level。

## 1. 通用项目类型

| 类型 | 判定 | 起点 |
|---|---|---|
| `greenfield` | 新建系统、产品或独立能力 | S0 |
| `brownfield` | 修改、恢复或迁移已有实现 | 先 R0，再回到相应成熟度 |
| `research_only` | 只为明确待决问题形成研究裁决 | S1，结束于研究 Verdict/ADR，不自动进入实现 |
| `governance_only` | 只修改协议、控制基线或治理语义 | 按受影响对象定位，不产生运行就绪声明 |

L2 可以扩展项目类型，但 L1 禁止硬编码行业、地区、渠道或自然语言关键词。

## 2. 路由输入

每次选择必须记录：`project_type`、`complexity`、`uncertainty`、`data_sensitivity`、`external_side_effect`、`reversibility`、`regulatory_impact`、`availability_requirement`、`agent_collaboration_complexity`、`execution_topology`、`production_tier`、选择理由和未知项。

- 风险量表：`low/medium/high/critical`；
- `external_side_effect`：引用权限权威的四级枚举；
- `reversibility`：`full/partial/none`；
- `execution_topology`：`single_agent/multi_agent`；
- `production_tier`：`development/test/staging/production`。

机器路由条件只由 `policies/project-governance-routing.yaml` 定义；路由裁决和逐 overlay 必填字段只由 `policies/route-decision-contract.yaml` 定义。本文解释语义，不维护第二份阈值。不得用业务关键词猜测。人工覆盖必须记录原路由、覆盖值、理由、批准者和有效期。

## 3. 基础治理配置与叠加能力

基础治理配置必须且只能选择一个：

| 基础配置 | 允许条件 | 不得省略的控制 |
|---|---|---|
| `lite` | 低复杂、低不确定、低敏感、无外部写、完全可逆、非生产，且裁剪经批准 | 最小来源批准、需求分母、Spec、验收判据、Run/Evidence/Verdict 和声明封顶 |
| `standard` | 默认；信息不足、中高风险、需要正式追溯、契约、恢复、隔离或外部副作用治理 | 全部 P0 设计协议、项目隔离、权限和副作用门禁 |

可叠加能力可以独立或同时要求：

| 叠加能力 | 要求条件 | 增量控制 |
|---|---|---|
| `multi_agent` | 执行拓扑确实存在多智能体并行、委派、身份隔离或冲突恢复 | 委派身份、消息/锁、所有权、冲突和恢复控制集 |
| `production` | 目标环境是正式生产，要求发布、SLA、监控、值守、恢复和真实责任链 | 生产准入、变更、观测、恢复、回滚、事故和生产 Evidence 控制集 |

外部副作用、数据敏感性和法规影响在任何环境都必须触发相应安全控制，不能用 `production` 叠加能力替代。`production_proof` 是证据等级，也不表示 `production` 已激活。

信息不足时基础配置默认 `standard` 并登记未知风险，不能自动降为 `lite`。命中叠加条件只会把相应 overlay 标记为 `required: true`；是否已选择、启用、实现和验证必须分别记录。

## 4. 版本化路由裁决

```yaml
extends: controlled_object_base/v1
route_decision_id: route-id
version: 1
project_type: brownfield
route_inputs:
  complexity: medium
  uncertainty: medium
  data_sensitivity: low
  external_side_effect: none
  reversibility: full
  regulatory_impact: low
  availability_requirement: medium
  agent_collaboration_complexity: high
  execution_topology: multi_agent
  production_tier: production
route_input_contract_ref: project-governance-routing@1#route_input_required_fields
route_input_contract_hash: sha256
routing_policy_ref: project-governance-routing@1
routing_policy_hash: sha256
routing_reason: description
manual_override: null
base_governance_profile: standard
overlays:
  multi_agent:
    required: true
    selected: true
    enabled: false
    implementation_status: not_started
    verification_status: unverified
    authorization_snapshot_ref: null
    overlay_activation_verdict_ref: null
  production:
    required: true
    selected: true
    enabled: false
    implementation_status: not_started
    verification_status: unverified
    authorization_snapshot_ref: null
    overlay_activation_verdict_ref: null
control_set_ref: control-set-id
control_set_version: 1
control_set_hash: sha256
unknowns: []
approved_by: human-id
effective_at: timestamp
expires_at: timestamp-or-null
supersedes: null
```

人工覆盖不能只写一句理由。`manual_override` 非空时必须保存原始路由、被覆盖字段和值、覆盖原因、批准者和到期时间；到期后重新计算路由，不能默认沿用旧覆盖。机器字段和不变量只由 `policies/route-decision-contract.yaml` 定义。

`required`、`selected`、`enabled`、`implementation_status` 和 `verification_status` 不得互相推导。`required` 使用 `true/false/unknown`；影响 overlay 判断的路由输入未知时必须记为 `unknown` 并阻断激活和业务声明，不能按 `false` 处理。`required: true` 必须进入选择和影响分析；`enabled: true` 必须同时具备相应实现、有效授权快照和接受的 `overlay_activation_verdict`，否则 fail-closed。

激活使用两个路由版本避免循环：路由 v1 记录 `selected: true, enabled: false`，在隔离环境验证 control set 并形成 overlay activation Evidence/Verdict；路由 v2 再记录 `enabled: true` 和 `overlay_activation_verdict_ref`。业务 Acceptance Verdict 只能使用 v2，不承担 overlay 激活裁决。

路由裁决属于 L3，L1 只定义字段和选择规则。只有 L3 的 Spec、Task、项目 Workflow、Capability Grant、Run、Checkpoint、Evidence、Verdict 和 Claim 强制绑定 `route_decision_ref` 与 `control_set_hash`；L1/L2 通用资产不绑定具体项目路由，`route_decision` 自身绑定 routing policy、control set 和前一版本，不自引用。

## 5. 复判时点

在 S0 初判；S2 完成真实场景/触发后复判；S3 方案选择后复判；S5 执行计划和权限确定后复判；任何数据敏感性、外部副作用、生产等级、协作模型或法规变化都立即复判。

项目类型、基础治理配置、任一 overlay 状态或 control set 变化必须产生新路由版本，记录新旧值、原因、批准者和影响分析。变化会使依赖旧控制集的 Spec、Task、Workflow、Capability Grant、审批票据、Checkpoint、待执行副作用、Evidence、Verdict 和 Completion Claim 进入待复核或失效。历史 Run 不改写；降级不能保留高控制集声明，升级后必须补齐新增门禁。
