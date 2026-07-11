# {{spec_id}} 任务

## 单个 Spec 任务的唯一权威

本文件是单个 Spec 任务的唯一权威；plan 和跨 Spec task-tree 只能引用或生成视图。

## 任务

```yaml
task_declarations:
  - task_ref: "{{task_ref}}"
    source_ref: "{{requirement_ref}}"
    owner_ref: "{{owner_ref}}"
    output_ref: "{{output_ref}}"
    completion_condition: "{{completion_condition}}"
    criterion_ref: "{{criterion_ref}}"
```
