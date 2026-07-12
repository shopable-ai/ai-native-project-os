---
stable_id: REQ-FUNC-001
object_type: requirement
requirement_kind: functional
function_id: FUNC-001
canonical_path: requirements/functions/FUNC-001_功能需求卡.md
version: 1
governance_scope: l2
lifecycle_stage: S2
priority: p1
work_status: completed
approval_status: approved
implementation_status: not_started
owner: human-template-owner
executor: ai-template-author
approver: human-template-owner
verifier: independent-template-reviewer
capability_refs: [CAP-001]
business_requirement_refs: [REQ-001]
business_chain_refs: [CHAIN-001]
scenario_refs: [SCENARIO-001]
intent:
  original_intent: "使交付对象能够回溯到批准事实，而不是增加文件数量"
  interpreted_intent: "为一个功能建立人类可审查需求并保持端到端追溯"
  approved_intent: "在不把模板存在当作实现证明的前提下保持交付追溯"
  implementation_intent: "让 Spec 精确绑定批准功能需求版本、hash 和 baseline"
context_snapshot_ref: CTX-001
baseline_ref: REQ-BASELINE-001
content_hash: "{{functional_requirement_content_hash}}"
supersedes: null
candidate_solution_status: candidate
spec_refs: [SPEC-REQ-FUNC-001]
stale_status: fresh
---

# FUNC-001：交付对象追溯

## 一句话结论

让人类先确认交付对象为什么需要追溯、怎样才算正确，再由 Spec 生成工程工作包。

## 为什么需要

业务 Requirement `REQ-001` 要求交付对象能够回溯到批准 Fact；只创建 Spec 文件不能证明 AI 理解了这个目标。

## 使用者与触发条件

L2 owner 在 `FUNC-001` 准备进入 ADR 或 Spec 前审查；上游意图、Chain、Capability 或 Function 变化时重开。

## 正常流程

读取批准上游 → AI 形成 draft 与自检 → 人类审查四段意图和边界 → 批准版本 → 写入新 baseline → ADR/Spec 消费。

## 异常、拒绝和恢复

意图不一致、Unknown 阻断、上下文不可重放或人类拒绝时保持 blocked；修订创建新版本，不能覆盖旧批准内容。

## 输入

- `FACT-001`、`REQ-001`；
- `SCENARIO-001`、`CHAIN-001`、`CAP-001`、`FUNC-001`；
- `CTX-001` 中明确纳入的权威文件。

## 输出

- 一份经批准的功能需求版本；
- baseline 成员引用；
- ADR/Spec 的边界与验收方向。

## 业务规则

- `implementation_intent` 不得扩大 `approved_intent`；
- 未批准需求不得进入 active Spec；
- 生成视图不能替代本卡。

## 非目标与边界

- 不实现 Workflow engine；
- 不把文件存在当作实现、运行或生产证明；
- 不在本卡决定候选技术方案。

## 数据、权限与风险

只使用已批准 L2 示例对象。AI 可以起草，只有可验证人类 principal 可以批准需求和 baseline。

## 验收方向

人类能够从本卡回溯批准意图、Chain/Capability/Function，并确认 Spec 未扩大范围且绑定精确版本/hash。

## 已批准实现约束

- fail closed；
- 保留旧版本与 `supersedes`；
- `.prompts/`、聊天和临时笔记不得成为权威。

## 候选实现要点

- 候选：未来生成项目地图、覆盖矩阵和影响预览；
- `candidate_solution_status: candidate`，未经研究/ADR 不进入 Spec。

## 已有资产

- L1 需求设计工作流；
- requirement design package contract；
- Spec 五件套模板。

## 未知与待确认

- `UNKNOWN-001`：真实 L2 是否需要自动项目地图生成器；当前阻断相关自动化决定，不阻断静态模板。

## 上下游影响

上游：`REQ-001`、`CHAIN-001`、`CAP-001`、`FUNC-001`。下游：ADR、`SPEC-REQ-FUNC-001`、Task、Test、Evidence、Verdict 和 Claim。

## AI 生成自检

- 缺少：真实 L2 的业务链和使用者验证；
- 假设：示例只证明结构；
- 可能错误：把通用追溯误解为多建文件；
- 待人工确认：四段意图、边界、风险和验收方向；
- 冲突检查：不得与 `REQ-001` 非目标或声明边界冲突。

## Spec 映射

批准后由 `SPEC-REQ-FUNC-001` 实现；Spec 必须引用 `REQ-FUNC-001/version/content_hash` 和 `REQ-BASELINE-001`。
