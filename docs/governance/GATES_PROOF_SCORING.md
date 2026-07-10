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

## 2. 门禁公式

```text
gate_pass =
  exit_code_is_zero
  AND required_artifacts_exist
  AND schemas_are_valid
  AND semantic_invariants_pass
  AND no_open_p0_or_p1_findings
  AND critical_traceability_is_complete
  AND evidence_is_fresh
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
- 未覆盖边界。

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

```text
completion = Σ(weight(r) × c(r)) / Σ(weight(r))
```

只有分母锁定、P0/P1 全部完成、关键失败态验证、证据未过期、范围删减经批准时，才允许在指定证据等级内声明 100%。这不等于业务效果成功。

## 5. 设计评分

采用加权几何平均，防止高分维度掩盖致命短板：

```text
base_score = 100 × exp(Σ(weight_i × ln(dimension_i / 100)))
final_score = min(base_score - penalties, hard_gate_ceiling)
```

硬封顶：

| 缺口 | 最高分 |
|---|---:|
| 存在致命安全、权限或数据缺陷 | 59 |
| 关键需求没有验收条件 | 79 |
| 没有端到端证据或恢复机制 | 84 |
| 没有跨项目隔离和安全验证 | 89 |
| 没有独立反方审计 | 94 |
| 没有异构真实项目验证 | 不得声称已证明通用 95+ |

## 6. 当前评分

| 对象 | 分数 |
|---|---:|
| 目标架构设计 | 97/100 |
| 标准版工作流设计 | 94/100 |
| 开源复用策略 | 92/100 |
| 当前本仓实现 | 0/100 |
| 当前生产证明 | 0/100 |
