# SUPERSEDED：2026-07-10 最小实现草稿

> 历史状态：本文件仅为被替代草稿的原样保存副本，不是当前 Workflow 或实施权威。
>
> 评分已过期：下文出现的历史分数、Phase 名称、完成判断和路径都不得用于当前评分、门禁或完成声明。
>
> 替代计划：[AI Project OS 方案 B 项目推进操作骨架实施计划](2026-07-11-ai-project-os-operational-spine-implementation.md)。

以下从原 `docs/workflows/IMPLEMENTATION_PLAN.md` 原样保留：

---

# 最小实现计划

状态：approved（用户 2026-07-10 口头批准）
依据：`reviews/p0-design-revision-score.yaml` 中登记的 open items
评分公式：只引用 `docs/governance/GATES_PROOF_SCORING.md`；当前有效分数只读取 `project-os.yaml.scoring_evidence` 指向的不可变快照。

本计划记录 L1 自身最小实现顺序，不保存任何具体 L2/L3 的项目事实、路径或运行 Evidence。

## 禁止事项（整个实现阶段）

- 不实现运行工作流引擎；
- 不安装任何第三方运行依赖；
- 不建设 `multi_agent` / `production` overlay；
- 不把设计分、检查器结果或 fixture 描述成业务运行证明；
- 不修改本计划未明确列出的既有权威文件；本计划明确新增或修订的权威产物必须单独审查、验证并登记影响范围。

## Phase 0 — 最小追溯检查器

**目标产物：** `linters/check_controlled_objects.py`

| open item 来源维度 | 具体缺口 | Phase 0 处理方式 |
|---|---|---|
| artifacts_and_traceability | 缺机器可执行关系 allowlist 双向覆盖检查 | C1/C2/C3 检查项 |
| boundaries_and_layers | 缺 L2/L3 锁文件 fixture 和迁移验证 | C4 通用依赖方向扫描 |
| tests_evidence_claims | 缺机器可执行证据枚举唯一性校验 | C5 `proof_level` 唯一权威扫描 |

检查器至少覆盖：

```text
C1  stable_id 在本仓库内唯一，且声明的 canonical_path 文件存在
C2  object_type=source 不得绕过批准事实驱动 Spec/Task/Workflow/Skill
C3  P0/P1 需求必须有对应 spec + traceability 出口
C4  L1 文件和模板不得包含指向具体 L2/L3 仓库的反向路径
C5  proof_level 枚举只在 GATES_PROOF_SCORING.md 一处定义
```

验收命令：

```bash
python3 linters/check_controlled_objects.py . --report
```

门禁：`EXIT=0`、无 P0/P1 finding，并把可重算输出保存为 L1 自身的 Phase 0 Evidence。文件级白名单、业务名特判或整目录跳过不得用于制造通过结果。

## Phase 1 — 标准版骨架目录契约

**目标产物：**

- `templates/standard-project/`：greenfield（新建型）脚手架；
- `templates/brownfield-project/`：R0 存量恢复脚手架。

| open item 来源维度 | 具体缺口 | Phase 1 处理方式 |
|---|---|---|
| evolution_compatibility_assets | 缺迁移 fixture 和可复制消费者骨架 | 提供匿名化、可检查模板 |
| lifecycle_and_progression | 缺 R0 fixture | brownfield 模板提供 R0 清单 |

门禁：两个模板目录均被 Phase 0 检查器实际扫描并返回 `EXIT=0`；模板中的样例必须明确是 fixture，不得签发真实运行或生产声明。

## Phase 2 — 通用 L2 接入与消费者兼容验证

**目标产物：** `docs/workflows/L2_ONBOARDING.md`

| open item 来源维度 | 具体缺口 | Phase 2 处理方式 |
|---|---|---|
| boundaries_and_layers | 缺 L2 消费者兼容步骤 | 提供无业务绑定的锁定、追溯和检查流程 |
| evolution_compatibility_assets | 缺真实消费者验证协议 | 规定 Evidence 留在 L2，L1 只接受满足升格门禁的匿名快照 |

门禁：任一 L2 消费者在自己的仓库创建兼容锁、运行 `--l2-mode` 并保存自己的 Evidence。具体仓库名、路径和 Evidence 不反向进入 L1；单一消费者通过不能证明 L1 已具备跨项目通用性。

## Phase 3 — 图类资产规范

**目标产物：** `docs/governance/DIAGRAM_CONVENTIONS.md`

图的覆盖要求、追溯字段和验收规则属于治理协议，因此保存在 `docs/governance/`。本计划对该文件的明确新增不受“禁止修改计划外既有权威”约束，但仍必须独立审查和验证。

| 来源 | 具体缺口 | Phase 3 处理方式 |
|---|---|---|
| 设计评审盲区审计 | 链路和状态迁移缺少可视核验入口 | 规定受控对象需要的通用图类型与最小声明 |
| lifecycle_and_progression | 状态迁移只有文字视图 | 用匿名 fixture 验证 Mermaid 结构和追溯字段 |

规范只定义通用图类型：`flowchart`、`stateDiagram-v2`、`sequenceDiagram` 和边界/数据流图。任何样例必须来自 L1 匿名 fixture 或满足跨项目升格门禁的通用结论，禁止把单个 L2 的内部目录或命名复制为 L1 标准。

门禁：规范文件被 Phase 0 检查器扫描且 `EXIT=0`。图覆盖检查若尚未实现，只登记为未编号 backlog；不得复用已经分配给其他语义的检查项编号。

## 推进顺序

```text
Phase 0 检查器与回归测试
→ Phase 1 可复制模板
→ Phase 2 通用 L2 接入协议
→ Phase 3 图类资产规范
```

每个 Phase 只在对应产物、测试、检查器结果和声明边界同时成立后结束。具体消费者 Evidence 的升格按仓库层级契约处理，不在 `project-os.yaml` 中登记下层私有路径。
