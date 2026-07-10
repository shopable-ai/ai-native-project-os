# 研究包模板说明

创建研究包时使用：

```text
research/active/{research_id}_{slug}/
├── brief.md
├── sources.yaml
├── options.md
├── experiment-plan.md
├── evidence/
├── adversarial-review.md
└── verdict.md
```

## 最小要求

- `brief.md` 必须明确研究要支持哪个决策，而不是泛泛学习。
- `sources.yaml` 必须优先官方资料、原始论文和项目仓库。
- `options.md` 至少包含两个候选或解释为什么只有一个可行候选。
- `experiment-plan.md` 必须声明命令、输入、环境、成功判据和停止条件。
- `evidence/` 保存可复现原始证据，不只保存总结。
- `adversarial-review.md` 必须列出失败条件和反对采用的理由。
- `verdict.md` 只能给出采用、适配、延后或拒绝，并声明重审条件。

研究结论未通过架构决策门禁前，不得写入正式依赖或完成声明。
