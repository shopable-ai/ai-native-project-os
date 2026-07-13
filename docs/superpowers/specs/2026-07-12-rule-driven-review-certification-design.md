# 规则驱动审核与审核策略认证设计

**状态：** 已获用户批准，等待按实施计划落地。

**实施分支：** `agent/capability-function-pilot`。

**语言约定：** 面向人的说明以中文为主；稳定路径、字段、枚举、Schema 和命令保留英文。

## 1. 核心结论

AI Project OS 不把“批准”永久绑定为人工逐条操作，也不允许 AI 自己修改规则后给自己放行。正确边界是：

```text
人类确定目标、责任与高阶治理边界
→ 规则、Prompt、Schema、Context 和模型约束形成审核策略包
→ 预注册测试集与阈值
→ 多轮测试、Evidence 与独立认证 Verdict
→ 风险路由
   ├─ policy_certified：策略自动激活
   ├─ human_signoff：人工确认后激活
   └─ blocked：阻断或进入 rule_gap
→ 运行时由独立 AI reviewer 自动审核
→ 变化、漂移或反例触发失效与重新认证
```

普通内容、低风险功能需求和满足预先授权条件的小版本规则可以由已认证策略自动裁决。目标变化、范围扩大、阈值降低、风险接受、权限扩大和不可逆外部动作仍要求人工决定或独立授权。

## 2. 需要修正的问题

当前仓库已经实现人工规则治理、AI 自动审核、有界改写、规则缺口、职责分离和声明封顶，但仍有三个缺口：

1. `Human Approval` 被写成所有需求、Baseline、Context 和规则激活的固定前置条件；
2. 规则发布只有结构检查和静态反方审查，没有“测试集 → 多轮 Run → Evidence → Certification Verdict → 激活”的强制门禁；
3. Prompt、模型、规则、Schema 或 Context 策略变化后，缺少统一的认证失效绑定。

本设计只补这三个缺口，不重新建设审核平台或项目状态轴。

## 3. 批准与激活边界

保留现有 `approval_status`、`approved_intent` 和对象状态，避免破坏已有兼容关系；新增决策来源，不把 `approved` 解释成必然由人类逐条点击。

最小决策记录包含：

```yaml
approval_route: policy_certified | human_signoff
decision_authority_ref: policy-or-human-principal
certification_verdict_ref: verdict-or-null
approved_by: human-principal-or-null
```

约束：

- `policy_certified` 必须引用当前、未失效、scope 匹配的认证 Verdict；
- `human_signoff` 必须引用可验证的人类 principal；
- AI 可以执行认证策略，但不能修改激活策略、降低阈值、扩大 scope 或给自己的策略签发独立认证；
- 两条路径都不能替代外部副作用授权；
- 任何路径证据不足时均 fail closed。

## 4. 审核策略包

认证对象不是单独一段 Prompt，而是可重放的审核策略包：

```text
规则集版本/hash
+ Prompt 模板版本/hash
+ 输出 Schema 版本/hash
+ Context 选择、排序、截断和排除策略/hash
+ 模型 fingerprint、参数和允许的 fallback
+ Tool 与权限边界
+ 审核结果枚举、改写上限和失败出口
```

Prompt 只装配权威规则，不成为规则或业务事实源。任何组成部分变化都产生新的策略包 hash，并使旧认证进入待复核或失效。

## 5. 预注册测试集

每个审核策略在激活前必须绑定版本化测试集。至少覆盖：

| 类别 | 目的 |
|---|---|
| `positive` | 正确输出不被错误拒绝 |
| `negative` | 明确违规输出被拦截 |
| `boundary` | 临界、模糊和部分信息不会随意放行 |
| `adversarial` | 注入、欺骗、绕过和规则操纵被识别 |
| `unknown` | 规则不足时进入 `rule_gap` |
| `rule_conflict` | 冲突无法消解时阻断 |
| `stale_rule` | 过期、撤销或 hash 不匹配规则不能运行 |
| `cross_project` | 不读取或引用其他项目私有事实 |
| `multilingual` | 翻译不改变风险、规则和声明上限 |
| `rewrite_limit` | 达到改写上限后只能 blocked |
| `recovery` | 新规则生效后以新 Run 重审旧对象 |

每个 case 预先声明输入、预期 decision、预期 rule refs、禁止结果、必需 finding/Evidence、风险级别和重复次数。不得在看到模型输出后修改预期结果来制造通过。

## 6. 多轮测试与指标

确定性 Schema、引用和 hash gate 可按版本运行一次；非确定性 AI reviewer 必须按测试集声明重复执行，保存全部尝试而不是只保留最佳结果。

最小观测指标：

- `false_allow_rate`；
- `false_block_rate`；
- `decision_stability`；
- `rule_citation_accuracy`；
- `schema_valid_rate`；
- `rule_gap_detection_rate`；
- `rewrite_success_rate`；
- `cross_project_leakage_rate`。

阈值由项目风险策略预注册。高风险规则优先约束 false allow，而不是只看平均准确率。测试数量和重复次数不足时只能降低 claim ceiling，不能自动补成通过。

## 7. 认证与激活路由

认证 Verdict 使用以下结论：

```text
certified
certified_with_ceiling
rejected
rule_gap
expired
revoked
```

激活策略至少区分：

| 变化 | 默认路由 |
|---|---|
| 文字澄清且语义/hash 边界可证明未扩大 | 完整回归后可自动激活 |
| 增加测试、修复已知 rule gap | 完整回归后按风险路由 |
| 新规则族、scope 扩大、阻断阈值降低 | 人工确认 |
| 删除 blocking 规则、扩大权限或外部副作用 | 人工确认并单独授权 |
| 低风险功能需求且完整通过认证 | 可由策略门进入 Baseline |
| 原始意图冲突、关键 Unknown 或责任变化 | blocked 或人工确认 |
| 不可逆外部动作 | 独立人工授权 |

人工确认不是普通输出的默认兜底。规则不足时当前对象保持 blocked，人类异步完善规则，随后以新 Run 重新审核。

## 8. 结构与决策边界

新增资产遵守现有目录职责：

- `contracts/`：测试集、认证记录的结构、I/O、版本和失败语义；
- `policies/`：风险路由、自动激活、人工确认和阻断决策；
- `docs/governance/`：人类可读的审核策略认证权威；
- `templates/`：L2 可复制的真实规则包、测试集和激活策略示例；
- `fixtures/`：正反例与失效场景；
- `reviews/`：新鲜验证证据，不承载可编辑规范。

不得把测试 case、Prompt 或生成报告变成第二份规则权威。

## 9. 生命周期接入

- S0：确定目标、风险级别和允许的 approval route；
- S2：功能需求通过独立审核和决策门后进入 Baseline；
- S3/S4：策略包中的模型、Prompt、Context、Schema 和权限边界进入 ADR/工程设计；
- S5：Spec/Workflow 绑定当前认证策略和精确 hash；
- S6：运行评测、签发认证 Verdict、执行 AI 审核和验收；
- S7：真实反例、事故和 rule gap 回流测试集与规则新版本。

阶段、审批状态、实现状态、proof level 和激活路由保持正交。

## 10. 失效与重开

以下变化必须使旧认证进入 `review_required`、`expired` 或 `invalidated`：

- 规则、Prompt、模型/参数、Schema、Context 策略或 Tool 权限变化；
- 测试集、指标定义或阈值变化；
- 适用 scope 或项目 namespace 扩大；
- 新反例、生产事故或真实业务结果推翻原判断；
- reviewer 独立性、Evidence 新鲜度或认证权限失效。

失效传播到使用该认证的 Baseline、Spec、Workflow、AI Review Verdict 和 Claim；重开最早受影响阶段，不改写历史 Run 或旧 Verdict。

## 11. 非目标

- 不建设完整 AI reviewer 运行平台；
- 不选择或安装新的模型/工作流依赖；
- 不建立人工逐条审批界面；
- 不新增 `critical` 基础 Profile；
- 不用自然语言关键词硬编码风险路由；
- 不把 fixture、退出码或文档存在描述为生产就绪；
- 不声称当前总体评分达到 95+。

## 12. 完成边界

本阶段可以证明：权威、契约、模板、检查器和正反例 fixture 对规则认证与条件式决策门形成静态闭环。

本阶段不能证明：真实模型多轮稳定性、真实人工效率、真实 L2 消费、跨项目隔离、生产副作用安全或通用 95+。当前总体评分继续读取 `reviews/current-score-status.yaml`，没有完整可重算输入时保持 `not_evaluated`。
