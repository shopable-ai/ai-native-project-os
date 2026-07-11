# Skill 模板

| 问题 | 时机 | 输入 | 输出 | 下一步 |
|---|---|---|---|---|
| 哪个局部能力可被明确消费者在单一阶段复用？ | 职责、I/O 和模型/代码边界稳定时 | 消费者、局部职责、I/O 契约、权限 | 可评测的 Skill 包 | 填写 SKILL.md 与机器 manifest 后运行 eval |

## 复制后的完整树

```text
{{skill_root}}/
├── README.md                    # 必需：问题导航与完整树
├── SKILL.md                     # 必需：面向执行者的局部操作说明
├── skill.yaml                   # 必需：消费者、边界、权限、评测和兼容
├── scripts/                     # 条件启用：确定性代码实现
├── prompts/                     # 条件启用：模型局部提示资产
└── Run/Evidence/Verdict/artifacts # 运行时生成：评测与执行产物
```

Skill 只承担一个阶段内的局部职责，禁止跨阶段 Workflow。需要多节点状态迁移时改用 `templates/workflow/`。
