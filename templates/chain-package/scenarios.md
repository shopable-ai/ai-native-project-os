# 场景

## Behavior Specification

| `behavior_spec_id` | `version` | `requirement_refs` | `problem_statement` | `user_observable_goals` | `behavior_rules` | `non_goals` | `owner_ref` | `approver_ref` | `assumptions` | `unknowns` | `applicability` |
|---|---:|---|---|---|---|---|---|---|---|---|---|
| `{{behavior_spec_id}}` | `{{behavior_spec_version}}` | `{{requirement_refs}}` | `{{problem_statement}}` | `{{user_observable_goals}}` | `{{behavior_rules}}` | `{{non_goals}}` | `{{owner_ref}}` | `{{approver_ref}}` | `{{assumptions}}` | `{{unknowns}}` | `{{applicability}}` |

父级版本只在已批准的用户目标、范围或期望行为改变时升级。代码、测试、原因假设、验证方法或实际执行变化不改变稳定案例 ID。

## Behavior Case Registry

| `case_id` | `requirement_ref` | `case_type` | `representative_scenario_or_trigger` | `expected_user_observable_behavior` | `coverage_target` |
|---|---|---|---|---|---|
| `{{behavior_case_id}}` | `{{requirement_ref}}` | `{{behavior_case_type}}` | `{{representative_scenario_or_trigger}}` | `{{expected_user_observable_behavior}}` | `{{coverage_target}}` |

`case_type` 只能使用 `main_path`、`boundary`、`negative` 或 `failure_recovery`。行为案例只表达执行前目标；新增独立边界时新增稳定案例，不复制旧案例为技术版本。

| 场景 ID | 批准需求 | 参与者 | 前置状态 | 成功终点 | 失败终点 |
|---|---|---|---|---|---|
| `{{scenario_id}}` | `{{requirement_ref}}` | `{{actor_ref}}` | `{{precondition}}` | `{{success_terminal}}` | `{{failure_terminal}}` |

## 非目标

- `{{non_goal}}`

## Optional As-Is/To-Be Gap Analysis

仅 brownfield 或批准需求变更时启用；本表不是新生命周期阶段。

| `gap_id` | `behavior_case_ref` | `as_is_observation_ref` | `to_be_target_ref` | `impact` | `decision_route` |
|---|---|---|---|---|---|
| `{{gap_id}}` | `{{behavior_case_ref}}` | `{{as_is_observation_ref}}` | `{{to_be_target_ref}}` | `{{gap_impact}}` | `{{decision_route}}` |
