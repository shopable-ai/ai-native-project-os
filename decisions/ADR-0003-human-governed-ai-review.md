# ADR-0003：人工治理规则与 AI 自动审核分离

- 状态：accepted
- 日期：2026-07-11
- 适用层级：L1 通用系统
- 替代关系：补充 ADR-0001 与 ADR-0002，不替代其框架分层决议

## 背景

现有模型同时使用 `human_decision`、`approver`、`verifier`、`waiting_approval` 和 Verdict 表达规则批准、内容审核、验收与动作授权。该语义容易把“人负责治理规则”退化为“每条普通内容等待人工审核”，既不符合 AI-native 运行目标，也让安全授权与内容质量混为一谈。

## 决议

采用三类正交责任：

1. 人类批准和维护版本化 Markdown 治理规则、事实、需求、例外和剩余风险。
2. 独立 AI reviewer 在运行期间依据 active 规则集审核普通内容、Evidence、风险和质量，逐项引用 `rule_ref`，并输出 `allow/rewrite_required/blocked/rule_gap`。
3. 人类通过独立授权快照控制不可逆外部动作；该授权不能覆盖 blocked AI Review Verdict。

普通内容审核不得进入 `waiting_approval`。可修复问题进入有界自动改写；规则不足创建 `rule_gap_case` 并安全阻断当前对象，人类异步修订规则。

## 后果

- `human_decision` 收窄，不再承担普通内容逐条审核。
- 新增 `governance_rule_set`、`ai_review_verdict` 和 `rule_gap_case` 受控对象及机器契约。
- Workflow、Evidence、Acceptance 和 Claim 必须精确绑定规则集与审核裁决。
- 规则批准、内容审核和动作授权分别失效、分别留证，不能互相替代。
- L1 不包含业务术语、自然语言关键词或固定回复；L2/L3 提供具体规则正文。

## 拒绝的方案

- 仅修改“审核”措辞：没有机器契约，无法阻止逐条人工等待重新出现。
- 由生成 AI 自审：缺少独立节点、attempt 和责任分离，不能形成可靠 Evidence。
- AI 审核通过即自动授权动作：混淆内容合规与权限，扩大副作用风险。
- L1 直接实现完整模型运行时：超出当前成熟度并提前锁定未研究依赖。

## 迁移与验证

现有权威文档、策略、模板和检查器必须统一采用三类职责语义。静态检查至少验证规则集批准、精确规则引用、reviewer 独立、有界改写、规则缺口阻断、普通审核不等待人工，以及动作授权不能覆盖 blocked Verdict。

本 ADR 只批准设计与静态契约变更，不证明 AI reviewer 已运行，不证明本地真实、异构项目或生产能力。
