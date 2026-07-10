---
title: "Project map"
description: "Project-specific filing map for this ShopMe workspace."
order: 20
---

# Project map

This file explains where experts/agents should add new files in this workspace and which existing directories are active / archive / reference.

No `docs.config.yml` is active here. Treat `.` as the editable docs tree.

`.` is the active docs root for public guides and workflows.

## Overall policy

Use the smallest number of files that materially improve execution.

Do not create directory-level `README.md` or `INDEX.md` files whose only purpose is:
- repeating sibling filenames
- summarizing obvious folder contents
- restating what another index already says

A new summary file is justified only if it does at least one of these things:
- changes reading order
- defines decision gates
- defines archive vs active status
- reduces repeated expert setup prompts
- becomes the stable entrypoint for future sessions

## Directory roles

### Project root
The project root is `.`. Public docs and workflows should live under that active docs tree unless a more specific section below applies.

### `.shopme/`
Use for workspace governance, editor constraints, routing rules, archive policy, and file-placement policy.

### `.`
Use for public docs: methods, taxonomy, system design, workflows, and durable reading paths.

### `prompts/`
Use for reusable execution prompts and operator-safe task briefs.

### `operator/`
Use for operating procedures, ingestion guides, review pipelines, and curator workflows.

### `deliverables/`
Use for directly usable assets.

## Filing defaults

When unsure, use this order:

1. If it is a rule about how experts should work here -> `.shopme/`
2. If it is a reusable public docs page -> docs root
3. If it is a schema / registry / lookup contract -> `reference/`
4. If it is a showcase / curated example / 作品集 / 展示库 -> `portfolio/`
5. If it is a longer update or retrospective -> `blog/`
6. If it is a short update or release snapshot -> `news/`
7. If it is a reusable execution prompt -> `prompts/`
8. If it is an operating procedure or ingestion flow -> `operator/`

## Current active root policy

- docs root is for active working docs only.
- `deliverables/` is for directly usable assets.
- `.shopme/` is the stable home for governance and routing rules.

## Homepage and section placement

- 首页文档入口：根 `index.md` 或 docs 根入口页
- 文档方法体系：docs 根
- 参考 / schema / 字段规范：`reference/`
- 场景方案 / 展示库 / 作品集：`portfolio/`
- 长更新 / 策展日志 / 实验复盘：`blog/`
- 短动态 / 更新快照 / release note：`news/`
- 执行提示词：`prompts/`
- 运营与录入流程：`operator/`

## Archive / reference zones

No extra archive/reference roots are currently declared.
