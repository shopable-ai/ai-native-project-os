# L2 业务系统接入指南

| 阅读契约 | 内容 |
|---|---|
| 解决的问题 | 一个 L2 业务系统仓库第一次消费 L1 时，怎样建立可迁移、可验证且不反向污染 L1 的兼容边界。 |
| 何时阅读 | 初始化 `{{l2_repo}}`、升级 `{{l1_repo}}` 锁定版本或接入检查失败时。 |
| 输入 | `{{l1_repo}}`、`{{l2_repo}}`、可选 `{{project_id}}`、通过决策门的事实与需求。 |
| 输出 | L1 版本锁、L2 事实/Spec 边界和保存在 L2 的接入 Evidence。 |
| 下一步 | 完成占位符替换后执行本文检查命令，再按[项目交付工作流](PROJECT_DELIVERY_WORKFLOW.md)定位 R0/S0—S7。 |

层级所有权、锁定字段和兼容规则只由[仓库与 L1/L2/L3 层级契约](../architecture/REPOSITORY_AND_LAYER_CONTRACT.md)定义；本文只给出通用步骤，不保存任何具体业务仓库事实。

## 1. 占位符约定

| 占位符 | 含义 |
|---|---|
| `{{l1_repo}}` | AI Project OS 仓库根目录 |
| `{{l2_repo}}` | 待接入的 L2 业务系统仓库根目录 |
| `{{project_id}}` | 仅在需要 L3 实例隔离时使用的项目标识 |
| `{{business_term}}` | 由 L2 自己治理和维护的业务术语 |
| `{{spec_id}}` | L2 规格控制包的稳定编号 |
| `{{evidence_file}}` | L2 自己保存的接入检查 Evidence 文件名 |

占位符必须由 L2 在复制后替换。L1 文档不得把任何具体项目名、行业、地区、渠道、自然语言关键词或下层私有路径写成默认值。

## 2. 接入前判断

| 情况 | 项目类型 | 起点 |
|---|---|---|
| 全新系统，无历史实现 | `greenfield`（新建型） | 使用 `templates/standard-project/`，从 S0 开始 |
| 已有实现，需要恢复来源与架构 | `brownfield`（存量恢复型） | 使用 `templates/brownfield-project/`，先执行 R0 |

项目类型、基础治理配置和叠加能力的选择只引用[项目类型与治理配置路由](PROJECT_TYPE_AND_GOVERNANCE_ROUTING.md)，本文不维护第二套路由条件。

## 3. 锁定 L1 版本

```bash
cp {{l1_repo}}/templates/standard-project/project-os.lock.yaml \
   {{l2_repo}}/project-os.lock.yaml
```

至少填写：

- `version`：当前消费的 L1 版本；
- `compatibility_range`：L2 接受的兼容范围；
- `locked_at`：实际锁定时间；
- `locked_by`：对本次锁定负责的人类角色或身份；
- `protocol_locks`：L2 实际消费的协议、policy、Workflow、Skill 和 Tool 版本或 hash。

锁定记录表示消费约束，不表示 L1 能力已经在 L2 实现、启用或验证。

## 4. 建立 L2 受控事实与需求

L2 必须把原始来源与批准事实分开。推荐的通用落点如下；L2 可以采用等价结构，但必须保持来源、事实、控制和 Evidence 的职责分离。

```text
{{l2_repo}}/
├── domain/
│   ├── glossary.md
│   ├── mvp/
│   ├── chains/
│   └── capability-map/
├── specs/
└── reviews/
```

通用术语条目示例：

```markdown
## {{business_term}}
stable_id: term-{{business_term_id}}
object_type: fact
canonical_path: domain/glossary.md#{{business_term_anchor}}
approval_route: {{policy_certified_or_human_signoff}}
decision_authority_ref: {{policy_or_human_principal}}
approver: {{human_approver_or_null}}
定义：{{approved_definition}}
```

示例只规定 L1 公共字段，不替 L2 定义术语内容。原始来源必须先经合法 Decision Gate，才能升格为 `fact` 或 `requirement`；自动路径还须引用当前认证 Verdict。

## 5. 让 Spec 追溯到批准对象

每个 `specs/{{spec_id}}/traceability.md` 必须指向 L2 自己的批准事实或需求，不能让原始来源直接驱动 Spec、Task、Workflow 或实现。

```markdown
| 下游对象 | 上游批准对象 | 关系 | 当前证据等级 |
|---|---|---|---|
| `{{spec_id}}` | `domain/{{approved_requirement_path}}` | `derives_from` | `control_package` |
```

`proof_level` 的唯一枚举仍由 L1 的 `GATES_PROOF_SCORING.md` 定义；表中的值不构成自证。

## 6. 运行 L2 接入检查

```bash
python3 {{l1_repo}}/linters/check_controlled_objects.py \
    {{l2_repo}} --l2-mode --report
```

接入门禁至少要求：命令 `EXIT=0`、无 P0/P1 finding、锁文件存在、关键 traceability 指向批准对象。`EXIT=0` 只是必要条件，不替代 L2 自己的语义验收。

## 7. Evidence 所有权

检查器输出的 JSON Evidence 保存在：

```text
{{l2_repo}}/reviews/{{evidence_file}}
```

具体 L2 的仓库名、路径、Run、Evidence 和 Verdict 不得反向写入 L1。若要把兼容经验升格为 L1 资产，必须先满足 `REPOSITORY_AND_LAYER_CONTRACT.md §5` 的跨项目升格门禁；L1 只能保存匿名化 fixture 或不反向依赖下层仓库的可重算兼容快照。

## 8. 快速检查清单

```text
[ ] project-os.lock.yaml 存在，版本和兼容范围已填写
[ ] 原始来源与批准 fact/requirement 已分离
[ ] approved 对象具有 stable_id、canonical_path、approval_route 和 decision authority
[ ] specs/{{spec_id}}/traceability.md 指向批准对象
[ ] 具体业务事实和接入 Evidence 只保存在 {{l2_repo}}
[ ] --l2-mode 返回 EXIT=0，且 L2 自己的语义门禁通过
[ ] 未把具体 L2/L3 路径、业务术语或运行事实反写到 L1
```

接入门通过后，按 [L2 业务系统端到端推进 SOP](L2_PROGRESSION.md) 定位 R0 或 S0—S7 的当前阶段；接入检查本身不等于任何生命周期阶段已经完成。
