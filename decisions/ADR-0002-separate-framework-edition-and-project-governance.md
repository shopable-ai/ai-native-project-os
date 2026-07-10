# ADR-0002：分离框架版本等级与项目治理配置

- 状态：已接受
- 日期：2026-07-10
- 替代：ADR-0001 中把“标准版/Profile/多智能体/生产”视作同一升级轴的部分

## 背景

旧配置把 `lite`、`standard`、`multi_agent`、`production` 放进同一单选列表。前两者表达治理强度，后两者分别表达协作拓扑和生产运行，无法形成一致的等级顺序，也遗漏了最初讨论的最大企业版本。

## 决策

1. 框架版本等级固定为 `minimal`、`standard`、`platform`、`enterprise`；当前目标为 `standard`。
2. 项目基础治理配置固定为 `lite | standard`。
3. `multi_agent`、`production` 是可独立组合的项目叠加能力。
4. L1 根配置只声明目录、目标和成熟度；具体选择保存在 L3 路由裁决。
5. `selected`、`enabled`、`implemented`、`verified` 分开记录，禁止把设计选择写成运行启用。

## 后果

- 可以表达 `standard + multi_agent + production`，而不把 production 误认为企业版。
- 框架范围、项目风险路由和证据成熟度可以独立演进。
- 现有单值 `profile`、`selected_profile` 和 `enabled` 需要迁移。

## 重审条件

- 两个异构消费者证明四级框架边界无法保持稳定；
- 基础治理配置需要第三种互斥等级；
- 新叠加能力与现有配置无法通过 control set 组合；
- 企业治理需求证明 `platform` 与 `enterprise` 无法合理分离。
