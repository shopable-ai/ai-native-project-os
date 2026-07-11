# 存量架构恢复模板（Brownfield / R0）

| 问题 | 时机 | 输入 | 输出 | 下一步 |
|---|---|---|---|---|
| 存量 L2 系统如何在不丢失现状的前提下接入？ | `project_type: brownfield` 时 | 现有代码、文档、配置、契约、测试和运行入口 | L2 根目录中的 R0 inventory 与 gap matrix | 完成 R0 退出门禁后回到相应成熟度阶段 |

适用条件：`project_type: brownfield`，先在 L2 根目录执行 R0 存量恢复，再回到相应成熟度阶段。
架构师工作流参考：`docs/workflows/ARCHITECT_WORKFLOWS.md § A02`

## 复制后的完整树

```text
{{l2_repo}}/
├── README.md                              # 必需：本恢复入口
├── r0-inventory.md                        # 必需：存量清点结果
├── gap-matrix.md                          # 必需：差距与优先级
├── project-os.lock.yaml                   # 必需：L1 协议锁定
├── governance/rules/                      # 条件启用：迁移后的稳定规则
├── projects/{project_id}/                 # 条件启用：有多实例隔离证据时创建
└── Run/Evidence/Verdict/Claim/artifacts   # 运行时生成：不随模板预建
```

## R0 存量清点表（inventory）

填写下表后保存为 `r0-inventory.md`，这是 R0 退出门禁的必需产物。

### 1. 需求与文档

| 编号 | 文件路径 | 性质 | 状态 |
|---|---|---|---|
| REQ-001 | `{{requirement_path}}` | requirement / assumption / source | active / orphan / stale |

### 2. 代码与实现

| 组件 | 路径 | 对应需求 | 状态 |
|---|---|---|---|
| `{{component_name}}` | `{{component_path}}` | `{{requirement_id_or_orphan}}` | active / deprecated |

### 3. 契约与测试

| 契约/测试 | 路径 | 覆盖的需求 | 状态 |
|---|---|---|---|
| `{{contract_or_test_name}}` | `{{contract_or_test_path}}` | `{{requirement_id_or_orphan}}` | passing / failing / missing |

### 4. 孤儿实现（无来源需求）

| 实现 | 路径 | 处置建议 |
|---|---|---|
| `{{implementation_name}}` | `{{implementation_path}}` | keep / migrate / delete / defer |

---

## 差距矩阵（gap-matrix）

填写下表后保存为 `gap-matrix.md`。

| 需求 | 当前架构状态 | 目标架构状态 | 差距 | 优先级 |
|---|---|---|---|---|
| `{{requirement_id}}` | `{{current_state}}` | `{{target_state}}` | `{{gap}}` | p0 / p1 / p2 |

---

## R0 退出门禁

```
[ ] 所有活跃入口和运行状态已冻结记录
[ ] 需求、文档、代码、契约、测试、运行产物已清点
[ ] 孤儿实现已标记并有处置计划
[ ] 差距矩阵已填写，P0/P1 差距有优先级
[ ] 已清点现有内容审核规则、Prompt 约束、人工审核队列和外部动作授权边界
[ ] 已规划把稳定约束迁入 governance/rules/ 中文 Markdown 规则包
[ ] 本目录通过检查器扫描（EXIT=0）
[ ] 保存 Evidence：reviews/phase-r0-inventory-evidence.yaml
```

---

## 接入检查器

```bash
python3 {{l1_repo}}/linters/check_controlled_objects.py . --l2-mode --report
```

规则包格式使用 `templates/standard-project/governance/rules/`。存量项目先迁移规则并保留来源，再把普通内容审核切换为独立 AI reviewer；不可逆动作的人工授权不得删除。
