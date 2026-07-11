# ADR-0004：分离机器契约与机器政策

- 状态：accepted
- 日期：2026-07-11
- 决策范围：L1 治理机器权威目录

## 背景

原 `policies/` 同时保存项目治理路由政策和八个受控对象/裁决契约。政策回答“在什么结构化条件下选择什么”，契约回答“记录必须具有什么结构与约束”。两类权威混放使目录名不能表达语义，也容易让调用方误把路线选择、记录结构和运行状态折叠为同一轴。

## 决策

1. `policies/` 只保留 `project-governance-routing.yaml` 和问题导航 `README.md`。
2. 八个现有契约通过 Git move 迁移到 `contracts/governance/`，保留原 `contract_id` 和版本语义：
   - `policies/acceptance-verdict-claim-contract.yaml` → `contracts/governance/acceptance-verdict-claim-contract.yaml`
   - `policies/ai-review-verdict-contract.yaml` → `contracts/governance/ai-review-verdict-contract.yaml`
   - `policies/authorization-snapshot-contract.yaml` → `contracts/governance/authorization-snapshot-contract.yaml`
   - `policies/control-set-contract.yaml` → `contracts/governance/control-set-contract.yaml`
   - `policies/governance-rule-set-contract.yaml` → `contracts/governance/governance-rule-set-contract.yaml`
   - `policies/overlay-activation-verdict-contract.yaml` → `contracts/governance/overlay-activation-verdict-contract.yaml`
   - `policies/route-decision-contract.yaml` → `contracts/governance/route-decision-contract.yaml`
   - `policies/rule-gap-case-contract.yaml` → `contracts/governance/rule-gap-case-contract.yaml`
3. 新增阶段退出门禁机器契约 `contracts/governance/stage-exit-gates-contract.yaml`，与人类视图 `docs/workflows/STAGE_EXIT_GATES.md` 分工：前者固定可校验记录，后者解释操作语义。
4. `project-os.yaml.authority` 是契约 ID 到唯一文件路径的机器解析入口。

## 边界

- policy 只负责结构化选择条件和选择结果，不定义受控对象字段。
- contract 只负责对象、裁决和门禁记录结构，不维护项目治理路由阈值。
- stage、work status、approval status、implementation status、proof level、framework edition 和 governance profile 保持独立，不互相推断。
- 失败或 unknown 的阶段门禁结果 fail closed，不得退出当前阶段。

## 拒绝的方案

### 在 `policies/` 保留兼容副本

拒绝。副本会产生双权威，使调用方无法判断应校验哪一版；旧路径失败应尽早暴露并由调用方迁移。

### 用链接或包装文件转发旧路径

拒绝。链接和包装仍让旧目录看起来承载契约权威，延长错误边界并使递归扫描、打包和离线消费产生歧义。

### 静默改写历史快照

拒绝。`docs/superpowers/specs/`、`docs/superpowers/plans/` 与 `reviews/` 中的旧路径是产生当时设计、计划和审查 Evidence 的历史事实。它们保持不可变；本 ADR 提供旧路径到新路径的迁移映射。读取历史快照时，工具可显式应用本 ADR 的映射，但不得把迁移后的路径伪装成当时原文。

## 后果

- 活跃配置、文档与测试必须只引用 `contracts/governance/` 下的契约。
- `policies/` 的契约旧路径立即失效；不存在兼容期或双写期。
- 契约 `contract_id` 保持稳定，因此按 ID 和版本引用的运行记录不需要改写；只有文件路径解析迁移。
- 后续新增资产必须先判断它回答“如何选择”还是“对象结构如何校验”，再分别落到 `policies/` 或 `contracts/`。
