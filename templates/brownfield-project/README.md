# 存量架构恢复模板（Brownfield / R0）

适用条件：`project_type: brownfield`，先执行 R0 存量恢复，再回到相应成熟度阶段。
架构师工作流参考：`docs/workflows/ARCHITECT_WORKFLOWS.md § A02`

## R0 存量清点表（inventory）

填写下表后保存为 `r0-inventory.md`，这是 R0 退出门禁的必需产物。

### 1. 需求与文档

| 编号 | 文件路径 | 性质 | 状态 |
|---|---|---|---|
| REQ-001 | {{ 路径 }} | requirement / assumption / source | active / orphan / stale |

### 2. 代码与实现

| 组件 | 路径 | 对应需求 | 状态 |
|---|---|---|---|
| {{ 组件名 }} | {{ 路径 }} | {{ REQ-xxx 或 orphan }} | active / deprecated |

### 3. 契约与测试

| 契约/测试 | 路径 | 覆盖的需求 | 状态 |
|---|---|---|---|
| {{ 名称 }} | {{ 路径 }} | {{ REQ-xxx 或 orphan }} | passing / failing / missing |

### 4. 孤儿实现（无来源需求）

| 实现 | 路径 | 处置建议 |
|---|---|---|
| {{ 名称 }} | {{ 路径 }} | keep / migrate / delete / defer |

---

## 差距矩阵（gap-matrix）

填写下表后保存为 `gap-matrix.md`。

| 需求 | 当前架构状态 | 目标架构状态 | 差距 | 优先级 |
|---|---|---|---|---|
| {{ REQ-xxx }} | {{ 描述 }} | {{ 描述 }} | {{ 缺什么 }} | p0 / p1 / p2 |

---

## R0 退出门禁

```
[ ] 所有活跃入口和运行状态已冻结记录
[ ] 需求、文档、代码、契约、测试、运行产物已清点
[ ] 孤儿实现已标记并有处置计划
[ ] 差距矩阵已填写，P0/P1 差距有优先级
[ ] 本目录通过检查器扫描（EXIT=0）
[ ] 保存 Evidence：reviews/phase-r0-inventory-evidence.yaml
[ ] 现有人工逐条审核点已分类为规则治理、AI 自动审核或高风险动作授权
[ ] 普通内容审核规则已迁移到 governance/rules/，未保留 waiting_approval 默认路径
```

人工逐条审核记录只能作为规则提炼输入，不能直接升格为 active 规则。规则由人批准后，普通内容交给独立 AI reviewer；不可逆外部动作继续使用单独人工授权票据。

---

## 接入检查器

```bash
python3 path/to/ai-project-os/linters/check_controlled_objects.py . --l2-mode --report
```
