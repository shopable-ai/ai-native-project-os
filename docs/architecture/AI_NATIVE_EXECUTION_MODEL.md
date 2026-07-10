# AI 原生执行模型

本文件是 AI 原生执行节点、版本指纹、上下文信任、评测和降级声明的唯一权威源。

本文件定义规范目标，不表示能力已经实现或验证。当前 design、implementation 和 verification 状态只读取 `project-os.yaml.maturity`；任何运行能力必须由对应 Evidence/Verdict 证明。

## 1. 执行节点类型

每个工程链路节点必须声明一个主要类型，可声明辅助类型：

| 类型 | 职责 | 强制边界 |
|---|---|---|
| `deterministic_code` | 可重复计算、校验、转换和协议执行 | 固定 I/O Schema、错误码和测试 |
| `model_reasoning` | 非确定性理解、生成、比较和判断 | 结构化输出、评测、失败返回和声明封顶 |
| `retrieval` | 检索或上下文装配 | 来源、信任级别、hash、截断和新鲜度 |
| `agent_action` | 依据目标选择步骤并调用能力 | 能力白名单、预算、checkpoint、审批和停止条件 |
| `human_decision` | 事实批准、风险接受、验收或不可逆动作授权 | 人类身份、输入摘要、决定、时间和有效期 |
| `external_system` | 受控边界之外的服务或设备 | 契约、超时、幂等、回执、失败和恢复语义 |

能够由确定性代码可靠完成的步骤，不默认交给模型。模型、Agent 和 Tool 是不同对象；Workflow 负责编排，不隐含无限权限。

## 2. 节点最小声明

```yaml
node_id: stable-id
execution_type: model_reasoning
input_schema_ref: schema-id
output_schema_ref: schema-id
model_ref: provider-model-version-or-null
prompt_ref: prompt-version-or-null
context_policy_ref: policy-version-or-null
tool_refs: []
policy_refs: []
evaluation_refs: []
budgets:
  token_limit: 0
  cost_limit: 0
  latency_ms: 0
  retry_limit: 0
failure_return_ref: contract-id
fallback_ref: null
fallback_claim_ceiling: control_package
capability_grant_refs: []
```

## 3. Run 指纹

Run 必须记录代码提交、依赖锁、配置、模型提供方/修订/参数、提示模板与实际渲染结果、上下文、Tool 集、策略和 Schema 的版本或内容指纹。只记录“最新”或供应商别名不具备重放资格。托管模型即使指纹一致也可能漂移，因此重放证明以版本化评测而非逐字一致为准。

`retrieval` 还必须记录查询指纹、索引/快照 ID、项目 namespace、过滤器、排序策略、top_k、返回片段和空/部分结果。上下文 manifest 逐项记录来源 ID、内容 hash、信任等级、权威状态、token 数、纳入范围、顺序、截断和省略理由；关键批准事实被截断时 fail-closed。

## 4. 不可信输入与提示注入

原始来源、网页、附件、检索片段和外部 Tool 输出默认不可信。每项上下文声明 `trust_level`、`instruction_or_data`、`source_authority` 和 `permission_effect`。不可信内容只能作为引用数据进入隔离区，不得获得系统指令优先级、权限声明或批准身份。检测到权限提升、秘密索取或越权 Tool 指令时 fail-closed 并产生审计 Evidence。

## 5. 评测与失败返回

非确定性节点必须绑定版本化评测集、反例集和注入攻击集，并记录 dataset fingerprint、指标定义、阈值、基线、失败样例和 evaluator 身份。评测至少覆盖结构契约、事实依据、拒绝/安全边界、跨语言或跨项目适用范围以及降级行为。解析失败、置信不足、预算超限、Tool 失败和无有效上下文必须返回结构化失败，不得伪造正常结果。

## 6. 预算、重试与降级

成本、token、延迟和尝试预算在运行前定义；只有显式 `retryable` 错误可以重试，并累计全部消耗和尝试。非确定性重试必须保存每次尝试，不能只保留最佳输出。降级路径必须事前声明触发条件、替代节点、丢失能力、证据损失和 `fallback_claim_ceiling`；未登记的临时降级不得签发 Completion Claim，降级 Evidence 必须标记 `degraded_execution`。

本文件不预设 LangGraph、Temporal 或任何模型/观测框架为依赖。候选只能经研究、实验和 ADR 后通过适配器接入。
