# 门禁、证据等级与评分

## 1. 证据阶梯

```text
control_package
→ candidate_assets_ready
→ schema_contract_ready
→ contract_tests_ready
→ fixture_runtime_proven
→ local_runtime_proven
→ readonly_real_preflight_passed
→ production_proof
```

高层证据必须包含低层证据。任何声明都由关键路径最低证据等级封顶。

这是全仓唯一可编辑的 `proof_level` 机器枚举。其他文件只能引用它或生成中文视图。

| 枚举 | 中文含义 | 最小证明边界 |
|---|---|---|
| `control_package` | 控制包就绪 | 范围、权威、验收和追溯已定义 |
| `candidate_assets_ready` | 候选资产就绪 | 候选存在且静态清点通过，不代表契约成立 |
| `schema_contract_ready` | Schema/契约就绪 | 结构、版本和失败语义已定义并可解析 |
| `contract_tests_ready` | 契约测试就绪 | 正反例测试已定义并可执行，不代表实现通过 |
| `fixture_runtime_proven` | fixture 运行已证明 | 受控样例产生可复现 Run/Evidence |
| `local_runtime_proven` | 本地真实运行已证明 | 非 fixture 本地输入和真实依赖路径已验证 |
| `readonly_real_preflight_passed` | 只读真实预检通过 | 真实目标环境只读验证通过，无外部写副作用 |
| `production_proof` | 生产证明 | 经批准生产 Run、效果、恢复和责任链成立 |

## 2. 门禁公式

```text
gate_pass =
  exit_code_is_zero
  AND required_artifacts_exist
  AND schemas_are_valid
  AND semantic_invariants_pass
  AND no_open_p0_or_p1_findings
  AND critical_traceability_is_complete
  AND evidence_stale_status_is_fresh
  AND active_rule_set_is_human_approved_scope_matched_and_hash_matched
  AND required_ai_review_verdict_is_allow_with_exact_rule_refs
  AND no_unresolved_rule_gap_or_exhausted_rewrite_loop
  AND proof_level_meets_claim
```

## 3. 完成声明

每项声明必须包含：

- 声明对象和范围；
- 环境和输入类别；
- 证据等级；
- 证据引用；
- 验证命令；
- 内容和环境指纹；
- 时间和有效期；
- 审核身份；
- 人工批准规则集版本/hash与 AI 审核裁决；
- 未覆盖边界。

Run、Evidence、Acceptance Verdict 与 Completion Claim 的字段和固定顺序只由 [Run、Evidence、验收裁决与完成声明](RUN_EVIDENCE_ACCEPTANCE.md) 定义。

普通内容审核不得用人工逐条签字提高 proof level。只有 active 规则集、独立 AI Review Verdict、精确规则引用、完整 attempt 和新鲜 Evidence 才能证明自动审核门禁。人工授权只证明动作获准，不能替代内容审核。

## 4. “100%代码需求完成”

对已批准需求集合 `R`，每项需求的完成值为：

```text
c(r) = min(
  scope_approved,
  implementation_complete,
  acceptance_passed,
  evidence_fresh,
  blockers_closed
)
```

`implementation_complete` 只能由受控对象的 `implementation_status == implemented` 且对应实现验收 Evidence 有效时取 1；`not_applicable/not_started/partial` 均取 0。它不能由生命周期阶段、审批通过或文档存在推导。

```text
completion = Σ(weight(r) × c(r)) / Σ(weight(r))
```

只有分母锁定、P0/P1 全部完成、关键失败态验证、证据未过期、范围删减经批准时，才允许在指定证据等级内声明 100%。这不等于业务效果成功。

完成率必须绑定 `requirement_baseline_id`、需求版本集合和权重 hash；P0/P1 权重不得为 0。任何需求删减或降权必须提供独立批准的 scope-change 和前后分母对账，否则旧分母继续生效。

## 5. 设计评分

采用加权几何平均，防止高分维度掩盖致命短板：

```text
base_score = 100 × exp(Σ(weight_i × ln(dimension_i / 100)))
final_score = min(base_score - penalties, hard_gate_ceiling)
```

标准维度与权重：

| 维度 | 权重 |
|---|---:|
| 系统边界与分层 | 10% |
| 生命周期与推进闭环 | 10% |
| 来源、事实、研究与决策 | 10% |
| 产物职责与追溯 | 10% |
| Workflow、执行和恢复 | 12% |
| AI 原生上下文、模型和工具治理 | 10% |
| 安全、权限与项目隔离 | 12% |
| 测试、证据和完成声明 | 10% |
| 演进、兼容和资产生命周期 | 8% |
| 中文可读性与使用体验 | 8% |

每次评分必须保存：评分对象和范围版本、每维原始值与评分依据、对应文件、验证命令、未通过项、评分者、评分时间、Evidence 引用、处罚项和数值、硬门禁封顶以及公式版本。缺任一可重算输入时输出 `not_evaluated`，不得输出估算分或沿用历史分。

硬封顶：

| 缺口 | 最高分 |
|---|---:|
| 存在致命安全、权限或数据缺陷 | 59 |
| 关键需求没有验收条件 | 79 |
| 没有端到端证据或恢复机制 | 84 |
| 没有跨项目隔离和安全验证 | 89 |
| 没有独立反方审计 | 94 |
| 没有异构真实项目验证 | 不得声称已证明通用 95+ |

## 6. 当前评分入口

本文件只定义算法和硬封顶，不维护当前分数。当前有效评分必须由 `project-os.yaml.scoring_evidence` 指向不可变评分快照；快照必须绑定 Git revision 或全部输入文件 hash，并保存可执行命令及输出。旧评分只代表当时 scope，不得因规范变化自动沿用。

目标方案分描述目标设计本身，不应用“当前尚无运行证据”的封顶伪装为已验证分；当前设计证据分、实现分、本地运行证明分和生产证明分必须分别计算。缺少可重放输入时一律为 `not_evaluated`。
