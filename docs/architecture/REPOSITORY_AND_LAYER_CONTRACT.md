# 仓库与 L1/L2/L3 层级契约

本文件是层级所有权、仓库落点、依赖方向、版本兼容和迁移规则的唯一权威源。L1/L2/L3 只表示所有权和依赖，不表示框架版本等级、项目治理配置、生命周期、实现状态或 proof level。

大写 `L1/L2/L3` 与小写 `governance_scope: l1/l2/l3` 的中文显示和大小写消歧只引用[术语权威](../governance/TERMINOLOGY.md#仓库所有权层级)；本文只维护仓库所有权、依赖和兼容规则。

## 1. 层级所有权

| 层级 | 保存内容 | 允许依赖 | 禁止事项 |
|---|---|---|---|
| L1 AI Project OS | 通用方法、对象协议、状态、门禁、证据、模板、框架版本目录、项目治理协议和适配器接口 | 外部标准与经决策接受的依赖 | 引用 L2/L3 业务事实、项目 ID、行业关键词或运行数据；替项目选择或激活治理配置 |
| L2 业务系统 | 业务事实、政策、场景、链路、业务能力、功能、契约、工作流和业务 Skill | 锁定兼容的 L1 | 重定义 L1 状态/证据/裁决；把 L3 个例直接升格为业务规则 |
| L3 项目实例 | 项目配置、批准事实、数据、Run、Evidence、验收裁决、声明和交付物 | 锁定 L2，并传递 L1 兼容信息 | 反向修改 L2/L1；让原始来源绕过批准流程驱动执行 |

依赖只能是 `L3 → L2 → L1`。上层发布协议和版本，不读取下层仓库；下层通过锁定记录、版本化契约或适配器消费上层。

## 2. 标准落点

L1 当前正式落点：

- `project-os.yaml`：系统状态和主题级权威路由；
- `docs/`：人类可读的通用协议；
- `decisions/`：不可改写历史的正式决策；
- `research/`：候选研究与原始证据，不保存正式结论副本；
- `reviews/`：审查证据，不承载规范定义；
- `templates/`：有正式内容的模板。

用户为单次设计审查临时提供的手工笔记、聊天摘录和外部项目路径不是 L1 资产：只能在当次审查中用于发现问题，不得复制、登记、引用或成为追溯上游。被独立验证并接受的通用结论必须用本仓自身的规范语言重新定义，且不得依赖临时材料继续存在。

L2 应拥有业务事实和业务设计；L3 应位于 L2 约定的 `projects/{project_id}/` namespace。具体目录可以由 L2 定义，但必须保持事实、控制、运行、证据和交付物的职责分离。

本设计阶段不创建只有名称的 `kernel/`、`contracts/`、`framework-editions/`、`project-governance/`、`adapters/`、`skills/` 或运行目录。目录只能随首个正式协议、实现或资产一起创建。

## 3. 锁定和兼容

L2 必须提供 `project-os.lock` 或等价机器记录，至少包含：

```yaml
system_id: ai-project-os
schema_version: 3
version: 0.1.0-design
supported_framework_editions: [standard]
compatibility_range: ">=0.1.0-design,<0.2.0"
adapters: []
protocol_locks:
  controlled_object_schema: version-or-hash
  proof_level_enum: version-or-hash
  io_contracts: []
  workflows: []
  skills: []
  tools: []
  policies: []
locked_at: timestamp
```

L3 必须锁定 L2 版本、项目 namespace、所需 L1 框架等级兼容范围和版本化治理路由裁决。锁定记录是消费约束，不是把 L1/L2 复制到 L3。项目实例至少记录：

```yaml
governance:
  route_decision_ref: route-id
  control_set_ref: control-set-id
  control_set_hash: sha256
```

兼容规则：

1. 新增可选字段且旧消费者可忽略，属于向后兼容。
2. 删除必需字段、改变字段语义、收紧枚举或改变状态迁移，属于破坏性变化，必须提升协议主版本或提供迁移器。
3. 未识别可选字段可以原样保留；未知必需字段、枚举或关系必须 fail-closed。
4. L2 可扩展业务对象，但不得重定义 L1 的稳定 ID、工作状态、证据等级、验收裁决和声明封顶。
5. 系统协议、对象 Schema、proof enum、I/O Contract、Workflow、Skill、Tool、policy 和 adapter 使用各自版本命名域和内容 hash；顶层版本相同不代表它们自动兼容。

## 4. 迁移规则

迁移必须记录来源版本、目标版本、影响对象、迁移器版本、迁移命令或人工步骤、验证命令、fixture、回滚路径和剩余不兼容项。迁移失败时保留旧锁定和旧证据，不得部分升级后继续签发完成声明。恢复旧 Checkpoint 前必须验证所有协议和资产版本。

L1 协议变化应使受影响的 L2 锁定进入待复核；L2 变化应使受影响 L3 的 Spec、Run 前置条件、Evidence 和 Completion Claim 按失效传播协议处理。

## 5. 资产反向升格门禁

L3 资产升格到 L2，至少需要：明确消费者、稳定契约、项目内反例测试、适用边界、维护责任和批准记录。

L2 资产升格到 L1，除上述条件外，还必须具有至少两个异构业务系统或项目类别的验证、跨项目隔离证据、通用命名、退出/替换成本和独立反方审查。单项目成功不能成为 L1 规则。

模板、Workflow、Skill 和 Tool 必须有版本、消费者、兼容范围、维护者以及 `candidate → active → deprecated → retired` 生命周期。失败资产可降级或失效；替代资产必须用 `supersedes` 保留历史关系。
