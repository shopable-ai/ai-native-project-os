# {{spec_id}} 实施计划

## task_refs

本文件只排序 `tasks.md` 中已经存在的 task refs，不定义新任务。

```yaml
task_refs:
  - "{{task_ref}}"
```

## 排序规则

- 只排序依赖已满足的 task refs；任务内容、完成条件和 owner 回到 `tasks.md` 修改。
- 上游批准对象变化时，重开本 Spec 并重新计算顺序。
