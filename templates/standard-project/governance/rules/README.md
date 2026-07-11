---
rule_set_id: review-rules
object_type: governance_rule_set
version: 1
canonical_path: governance/rules/README.md
content_hash: replace-with-sha256-after-approval
governance_scope: l3
scope:
  artifact_classes: [content, evidence]
  project_ids: [replace-with-project-id]
  locales: [all]
status: draft
owner: replace-with-human-role-id
approved_by: null
approved_at: null
effective_from: null
expires_at: null
supersedes: null
---

# 人工治理审核规则模板

本文件是项目规则集的 Markdown 权威模板。人类负责批准、发布和维护规则；AI reviewer 在运行期间逐条引用规则，不得把普通内容转给人工逐条审核。

## rule-content-grounding

```yaml
rule_id: rule-content-grounding
severity: high
applies_to: [content, evidence]
required_evidence: [project_fact_ref, source_ref]
allowed_outcomes: [allow, rewrite_required, blocked, rule_gap]
failure_action: blocked
```

规则正文必须描述可审核的约束、所需 Evidence 和失败动作。不得在 L1 检查器或通用 Workflow 中写入项目术语、具体语言关键词或固定回复触发条件。

批准发布时必须：把 `status` 改为 `active`，填写 verified human `approved_by`、时间、scope 和实际 `content_hash`，并确保每个 `rule_id` 唯一。AI 可以提出修订建议，但不能自行修改这些批准字段。
