---
title: "AI rules"
description: "System rules for AI-assisted editing in this ShopMe workspace."
order: 10
---

# AI rules

Read this file before changing docs content. Keep it in `.shopme/rules.md`; it is a hidden system sidecar, not public docs content.

## Start here

- No `docs.config.yml` is active here. Treat `.` as the editable docs tree.
- Machine-readable rules live in `.shopme/rules.json`.
- Generated link labels live in `.shopme/link-index.json`; use them before inventing internal link text.
- Project-level filing policy lives in `.shopme/project-map.md`; read it before creating new governance or index files.
- Read `.docsignore` before scanning content; ignored paths are not public documentation, while later `!` rules intentionally publish a small matching path.
- Default content filtering hides dot-prefixed and underscore-prefixed files/directories. To publish a small dot-prefixed content directory, add both allow rules, for example `!**/.well-known/` and `!**/.well-known/**`.
- `.git/`, `.shopme/`, `.next/`, `build/`, `dist/`, and `node_modules/` are always system/private paths and cannot be made public with `!` rules.
- Current .docsignore patterns: `.claude/`, `.cursor/`, `.claude-backups/`, `coverage/`, `.turbo/`, `.cache/`, `.idea/`, `.vscode/`, `out/`, `tmp/`, `_drafts/`, `temp/`, `scratch/`, `**/*.draft.md`, `**/*.bak.md`, `**/*.tmp.md`.
- Use `shopme --help` and `shopme init --help` when you need supported CLI behavior instead of guessing from raw Markdown files.
- Prefer ShopMe CLI workflows for preview, build, and mount validation before touching generated output.
- If this workspace skipped `shopme init`, running `shopme` or `shopme build` will still create the missing hidden sidecars under `.shopme/`.

## Local direct-edit HTTP API

- When a ShopMe embedded web runtime is available, AI-assisted local document edits should use the docs HTTP API instead of writing files directly.
- Read before writing: call `POST /api/docs/v1/documents:resolve` to get `document.documentId`, `document.baseVersion`, and `document.raw`.
- Save with `PUT /api/docs/v1/documents/:documentId`, sending the original `baseVersion` and updated `raw`.
- Treat `baseVersion` as required concurrency protection. If the API returns `VERSION_CONFLICT`, reread, merge, and retry; never blind-write over the file.
- `gitCommit` and `gitCommitMessage` are mutation request parameters, not CLI startup flags. Do not invent or use `--git-commit`.
- `"gitCommit": true` commits only the path or paths touched by that HTTP mutation, not unrelated dirty files in the repository.
- MCP clients should use `shopme-mcp` as a thin adapter, configured with `SHOPME_BASE_URL` and, for non-loopback or shared hosts, `SHOPME_API_TOKEN`.
- Discovery endpoints are `GET /api/docs/v1/capabilities` and `GET /api/docs/v1/openapi.json`; the MCP adapter must still call the HTTP API and must not write files directly.

## What you can change

- Update `docs.config.yml` for site metadata, navigation, built-in sections, and content roots when that file exists.
- Add or edit Markdown and MDX under the configured docs root. In this workspace, the docs root is `.` and the active locale root is `.`.
- Keep filenames in kebab-case.

## Ordering rules

- Every public Markdown or MDX page must keep frontmatter with `title`, `description`, and `order`.
- Use `index.md` as the landing page for a folder.
- Prefer gaps in `order` values such as `10`, `20`, `30`, `40`.
- When you insert a page between siblings, adjust `order` values instead of relying on filename sorting.
- Reorder official-site sections with `templates.<slug>.order` and repeated block items with `blockOrder`.

## High-signal title and TOC rule

- Do not treat headings as filing labels. Treat headings as the first layer of the document's actual meaning.
- Before drafting body text, decide what problem the document solves first: direction error or retrieval cost.
- If the doc mainly resolves judgment, policy, mechanism, tradeoff, or review questions, use strong conclusion-first headings.
- If the doc mainly supports execution, keep the main flow scannable but make high-risk nodes expose success conditions, failure points, and required preconditions.
- If the doc mainly supports retrieval, strengthen page-level or overview-level headings, but keep item-level headings accurate and searchable.
- Core rule: write the section's most important conclusion into the heading before deciding how the body expands it.
- The TOC must be independently readable: a reader should be able to infer what the document argues, what it rejects, what is forbidden, what constraint controls the rest, and why the design exists.
- Do not use the body to rescue a weak heading. Fix the heading first.

## High-signal title failure tests

- A heading fails if it only names a category and leaves the conclusion in the body.
- A heading fails if it is only, or almost only, a filing label such as `背景`, `原则`, or `说明` without an explicit section-specific conclusion.
- A heading fails if it can be dropped unchanged into many unrelated documents.
- A heading fails if the TOC alone still cannot tell the reader the key judgment, boundary, mechanism, or rejected mistake.
- A heading fails if it sounds like a document admin, secretary, or generic manual rather than a writer with an actual conclusion.
- A heading fails if its force is wrong for the document type and damages scanability or retrieval.

## Low-information labels to upgrade by default

- Treat labels such as `背景`, `定位`, `原则`, `说明`, `建议`, `使用方式`, `当前问题`, `相关约束`, `注意事项`, `总结`, `目录结构`, and `文档说明` as weak when they are used as the whole heading or as the heading's only real information.
- These words are not banned tokens. They can appear inside a qualified heading when the heading already exposes a concrete conclusion, boundary, conflict, or decision.
- Reject safe filler such as `提升文档质量的方法`, `构建更清晰的大纲`, `优化标题表达的策略` when they are portable across many unrelated docs.

## TOC-first workflow

1. Decide the document type and heading strength before writing prose.
2. Draft the TOC before drafting the body.
3. For each level-1 heading, answer: what is the most important conclusion of this section?
4. Rewrite any heading that still behaves like a category label, a process bucket, or a generic explanation title.
5. Only start body drafting after the TOC already carries first-layer meaning.

## API page heading rules

- For API-style Markdown pages rendered by shopme-cli, optimize heading structure for the right-side TOC.
- Keep the TOC focused on page-level sections, object-level sections, and method-level sections.
- Inside a method section, do not let subsections like Parameters, Return values, Behavior rules, Error conditions, Examples, or Notes dominate the TOC.
- Prefer bold labels, compact tables, tight lists, intro lines, or blockquotes for method-internal detail instead of deep `###` / `####` nesting.
- The page should read like a user-facing SDK reference, not a source-analysis outline.
- Do not force every API item heading into a strong judgment sentence; keep item-level headings exact and searchable.

## AI-first Docs IR authoring rules

- Plain Markdown headings automatically become implicit section blocks; do not rewrite old docs just to satisfy IR.
- Use `:::shared reusable-id ... :::` only for reusable content that is worth transcluding.
- Include shared content with `{{include:reusable-id}}`; include targets must already exist in the page-local shared block registry.
- Avoid include cycles. A cycle must fail closed as `include_cycle_detected`, not be silently swallowed.
- Shared block ids normalize to `shared:<slug>`; keep ids short, stable, and lowercase/kebab-case.
- If retrieval quality needs rollback, switch `DOCS_IR_ENABLED` off instead of changing the public `/docs` rendering contract.

## Relative assets

- Relative attachments are first-class: link neighboring `.md` / `.mdx` files with normal Markdown links.
- Relative `.md` / `.mdx` paths resolve to docs/reference routes.
- Relative non-Markdown files and image `src` values resolve to docs asset URLs.
- Keep public attachments inside the active docs/reference root.
- Do not link to `.docsignore`-ignored files, system/private paths, or `..` traversal targets. Dot-prefixed content is public only when a matching `!` rule allows it.

## Link text rules

- Before you create or rewrite an internal link, look up the target page in `.shopme/link-index.json`.
- When the index entry has a frontmatter `title`, copy that exact visible title into the Markdown link text.
- If the target page title is reader-facing Chinese or any other localized label, keep that label in the link text instead of falling back to the English filename or slug.
- If the target page is missing a `title`, add the frontmatter title first, regenerate or reread `.shopme/link-index.json`, then write the link.

## Boundaries

- Do not add React, TSX, local `component` paths, or local `template` paths to `docs.config.yml`.
- Do not move this file into `.`, `reference/`, `blog/`, or `news/`.
- Do not edit generated output to satisfy a content request: `dist/`, `build/`, `.next/`, and `node_modules/`.
- Do not move internal planning notes or private implementation details into public docs.
- Use `.` for guides and workflows. Use `reference/` for API, config, schema, or lookup-style material.
- Keep homepage / docs / reference / portfolio / blog / news content in their corresponding roots so AI editors place files directly where the site renders them.

## CLI workflow

1. Preview locally with `shopme .`.
2. Read command help with `shopme --help` and `shopme init --help`.
3. Build static output with `shopme build . --out dist`.
4. Validate mounted output with `shopme mount check dist/html --base-path / --canonical https://example.com`.

## Ignore while editing

- Ignore dependency and build folders unless the task is tooling work.
- Ignore `.env` and `.env.local` unless the task is environment setup.
- Ignore embedded runtime internals and generated artifacts when the task is ordinary content work.
