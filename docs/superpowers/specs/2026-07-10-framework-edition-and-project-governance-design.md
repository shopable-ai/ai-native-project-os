# 框架版本等级与项目治理配置分离设计

## 1. 问题

旧模型把 `lite`、`standard`、`multi_agent`、`production` 放进同一个 `profiles` 列表，并用单值 `selected_profile` 和布尔 `enabled` 表示当前状态。它混合了框架产品范围、项目治理强度、执行拓扑、生产运行、实现状态和证据成熟度，无法表达 `standard + multi_agent + production`，也可能把“设计目标”误读为“运行已启用”。

## 2. 决策

建立五组互不替代的分类维度；其中对象状态在状态权威中进一步展开为六个正交坐标：

1. 框架版本等级：`minimal → standard → platform → enterprise`，回答 AI Project OS 本身建设到多大；当前目标是 `standard`。
2. 项目基础治理配置：`lite | standard`，每个 L3 项目必须且只能选择一个；信息不足时默认 `standard`。
3. 可叠加能力：`multi_agent`、`production`，可以独立或同时要求；它们不是第三、第四级框架。
4. 生命周期和状态：R0、S0—S7、工作状态、审批状态和失效状态，回答对象处于哪里。
5. 实现与证明：`design_status`、`implementation_status`、`verification_status` 和 `proof_level`，回答规范、实现和证据分别达到什么程度。

`selected`、`enabled`、`implemented`、`verified` 不得互相推导：选择只表达目标；启用只表达某个有效运行配置实际激活；实现必须有实现级验收；验证必须绑定明确范围、环境、Evidence 和 Verdict。设计阶段禁止用 `enabled: true` 表达已选择或已定义。

## 3. 权威边界

- `project-os.yaml`：机器权威，保存框架等级目录、当前目标、项目治理能力目录和当前成熟度。
- `docs/architecture/FRAMEWORK_EDITION_MODEL.md`：框架四级语义和范围边界。
- `docs/workflows/PROJECT_TYPE_AND_GOVERNANCE_ROUTING.md`：项目类型、基础治理配置、叠加能力和版本化路由裁决。
- `docs/architecture/REPOSITORY_AND_LAYER_CONTRACT.md`：L1/L2/L3 所有权、锁定和迁移。
- 状态、证据、权限、Run/Evidence/Verdict/Claim 继续由各自现有权威文件定义，不在上述文件复制。

## 4. 机器模型

L1 根配置只声明能力目录和当前设计目标，不替任何项目选择治理配置。项目实际选择保存在 L3：

```yaml
governance:
  route_decision_ref: route-id
  base_profile: standard
  overlays:
    multi_agent:
      required: true
      selected: true
      enabled: false
      implementation_status: not_started
      verification_status: unverified
      authorization_snapshot_ref: null
      overlay_activation_verdict_ref: null
  control_set_ref: control-set-id
  control_set_hash: sha256
```

`required`、`selected`、`enabled`、`implementation_status` 和 `verification_status` 分别表达风险要求、项目选择、运行激活、实现和证据；任何一个都不能代替其他字段。

## 5. 迁移

- 删除根配置中的 `selected_profile`、`profiles.*.enabled` 和“四级框架”旧注释。
- 将泛称 `profile: standard` 改为 `framework_edition_compatibility` 或完整治理路由引用。
- 将“生产 Profile”改为“production 叠加能力”或具体生产准入决策。
- 旧 ADR、旧设计记录和旧审查 Evidence 保留历史原文，通过 `superseded_by` 或独立 resolution 标记，不回写当时证据。

## 6. 验收条件

- 所有当前权威文件只把 `minimal/standard/platform/enterprise` 称为框架版本等级。
- `multi_agent/production` 只作为项目可叠加能力出现。
- L1 不包含项目级 `selected_profile` 或运行 `enabled: true`。
- Run、Evidence、Verdict、Claim 和锁定示例绑定 `route_decision_ref` 与 `control_set_hash`。
- 生命周期、状态、proof level、实现状态和框架等级互不推导。
- YAML 可解析、权威路径存在、Markdown 链接有效、漂移扫描和 `git diff --check` 通过。
