# contracts/ 机器契约问题导航

本目录保存“一个受控对象或裁决记录必须长什么样”的机器权威。它不保存路由阈值等政策选择，也不复制 YAML 中的字段、枚举或不变量。治理契约统一位于 `contracts/governance/`；具体主题的权威路径以 `project-os.yaml.authority` 为准。

| 问题 | 时机 | 输入 | 输出 | 文件 | 示例 | 下一步 |
|---|---|---|---|---|---|---|
| 当前阶段能否退出，失效后重开哪里 | 阶段开始、退出审查或上游变化时 | 阶段、对象引用、证明等级、验证命令与 Evidence | 可审计的阶段门禁记录 | `governance/stage-exit-gates-contract.yaml` | S4 契约审查后记录 `passed`，或因未知副作用保持 `unknown` | 通过则进入下一依赖节点；否则按 `reopen_target` 重开 |
| 路由裁决怎样固定为可复核对象 | 结构化路由输入已经计算后 | 路由政策版本、输入、基础治理配置与 overlay 状态 | 版本化 route decision | `governance/route-decision-contract.yaml` | 将政策计算结果固定为 route v1 | 生成并绑定 control set |
| 路由实际包含哪些控制 | 选定基础治理配置和 overlay 后 | route decision、控制引用、实现 Evidence 与兼容范围 | 可哈希 control set | `governance/control-set-contract.yaml` | standard 基础控制加 selected production overlay | 验证实现、授权和 overlay 激活条件 |
| 人类维护的审核规则如何成为受控版本 | Markdown 规则准备批准或发布时 | 规则正文、scope、批准与版本信息 | 可校验 governance rule set | `governance/governance-rule-set-contract.yaml` | 发布一版内容与证据审核规则集 | 独立 AI 按固定版本审核 |
| 审核策略激活前必须测试什么 | 规则、Prompt、模型、Schema 或 Context 策略准备认证时 | 策略包、测试 case、预期结果、重复次数、指标与阈值 | 版本化预注册测试集 | `governance/review-policy-test-suite-contract.yaml` | 固定正例、反例、边界和对抗测试 | 执行全部评测 Run 并收集 Evidence |
| 审核策略是否具备受限激活资格 | 全部预注册测试和重复 Run 完成后 | 策略包/test suite hash、Run/Evidence、指标、阈值与 verifier | 有范围和期限的认证 Verdict | `governance/review-policy-certification-contract.yaml` | 低风险策略通过阈值并获得受限认证 | 交给激活 Policy 选择自动决策或人工确认 |
| 独立 AI 审核怎样留下可重算裁决 | 生成对象进入自动内容或 Evidence 审核时 | 被审对象、生成/审核 Run、规则集与 Evidence | AI review verdict | `governance/ai-review-verdict-contract.yaml` | 审核结果要求有界改写 | 允许则进入后续门禁；规则不足则开 rule gap |
| 规则缺口怎样异步治理 | 审核发现规则缺失、冲突或过期时 | 被审对象、审核裁决、规则版本与影响范围 | rule gap case | `governance/rule-gap-case-contract.yaml` | 当前对象阻断并登记规则修订责任人 | 新规则批准后用新 Run 重审 |
| 授权引用怎样证明有效而非空壳 | 高风险动作或 overlay 激活前 | 主体绑定、Grant、Ticket、Lease、期限与验证 Evidence | authorization snapshot | `governance/authorization-snapshot-contract.yaml` | 固定一次有效且未撤销的授权快照 | 交给动作门禁或 overlay 激活裁决校验 |
| selected overlay 怎样安全进入 enabled | 控制模块实现完成并在隔离环境验证后 | route v1、control set、授权快照与激活 Evidence | overlay activation verdict | `governance/overlay-activation-verdict-contract.yaml` | production overlay 在指定环境获接受裁决 | 由新 route 版本引用裁决并更新状态 |
| 怎样签发验收裁决和受限完成声明 | 判据、Evidence、审核与授权均准备后 | 精确 subject、criteria、Evidence、route/control 绑定与审核结果 | Acceptance Verdict 或 Completion Claim | `governance/acceptance-verdict-claim-contract.yaml` | 对指定环境和输入类别签发受限 Claim | 持续检查期限、失效条件与禁止外推范围 |
| Run 与 Evidence 怎样留下完整、不可改写且可复算的机器记录 | 执行、重试、恢复或独立采证时 | 路由、控制、指纹、attempt、判据和原始产物 | [Run/Evidence 机器记录](governance/run-evidence-contract.yaml) | `governance/run-evidence-contract.yaml` | 成功、失败、恢复和独立审核 Run 及其 Evidence | 按 [Run/Evidence 语义权威](../docs/governance/RUN_EVIDENCE_ACCEPTANCE.md) 进入审核与验收 |

## 目录边界

- `contracts/` 回答记录结构、约束和校验边界。
- `policies/` 回答在什么结构化条件下选择哪条治理路线。
- 文档解释为什么和怎样操作；机器字段只在对应 YAML 契约维护。
- 契约之间通过稳定 ID、版本、引用和内容 hash 关联，不通过相似文件名推断关系。
