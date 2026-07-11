# 图类资产规范

| 阅读契约 | 内容 |
|---|---|
| 解决的问题 | 把链路、状态、跨节点交接和信任边界投影成可 diff、可检查的图，而不创建第二份业务事实。 |
| 何时阅读 | `{{l2_repo}}` 的 P0/P1 链路、状态对象、外部调用或项目隔离仅靠文字难以核验时。 |
| 输入 | `{{l1_repo}}` 定义的受控对象协议，以及 `{{l2_repo}}` 中 `{{project_id}}` 范围的批准对象。 |
| 输出 | 绑定 owner 对象的 Mermaid 源图、frontmatter 与覆盖记录。 |
| 下一步 | 先确定 `governs_object`，再按本文选择图类型并把覆盖结果交给阶段门禁。 |

本文件是受控对象图类投影视图的类型、必需覆盖和验收规则的唯一权威源，面向设计者、审查者和检查器实现者。

图不是新的业务事实，也不替代 `CONTROLLED_OBJECT_MODEL.md` 的对象定义；它只把既有受控对象投影为可核验结构。

## 1. 为什么图是受控投影

文字链路容易漏掉分支、失败态和跨节点交接。图用于暴露：

- 状态机中的非法迁移和缺失失败态；
- 时序中的交接空隙、无回执副作用和超时；
- 流程中的无终止分支；
- 边界中的读写越界和信任跨越。

每张图必须追溯到一个受控对象，不允许存在没有 owner 对象的孤儿图。图与正文冲突时，以该主题的受控对象权威定义为准，图进入待复核。

## 2. 四类标准图与适用对象

| 图类型 | Mermaid 语法 | 回答的问题 | 必需于 |
|---|---|---|---|
| 流程图 | `flowchart` | 一条链路内部如何分支、失败和终止 | 每个 P0/P1 `business_chain` |
| 状态机 | `stateDiagram-v2` | 一个对象的合法迁移、失败态和终态 | 具有多状态的关键受控对象 |
| 时序图 | `sequenceDiagram` | 跨节点如何交接、谁调用谁、如何回执 | 每个跨节点 `engineering_chain` |
| 边界图 | `flowchart` + 分区 | 读取/写入范围、信任边界和项目隔离 | 涉及授权、数据读写或外部系统边界的对象 |

## 3. 每张图的最小声明

图以独立 `.md` 文件保存，frontmatter 必须包含：

```yaml
---
title: "{{diagram_title}}"
description: "{{diagram_purpose}}"
diagram_type: sequence
governs_object: "{{controlled_object_id}}"
order: 40
---
```

`diagram_type` 只允许 `flowchart/state/sequence/boundary`。正文必须包含可渲染的 Mermaid 代码块；PNG/JPG 可以作为派生预览，但不能成为唯一事实源。

## 4. 覆盖门禁

一个 P0/P1 `business_chain` 的图覆盖判定：

```text
chain_diagram_complete =
  存在 flowchart 且每个分支都有终止态
  AND 若跨节点则存在 sequenceDiagram，且每次外部调用都有回执或超时语义
  AND 若对象多状态则存在 stateDiagram，且非法迁移被显式排除
```

缺流程图时，该链路不得声明图覆盖完成。存在外部副作用但缺时序图时，不得仅凭文字把相应设计声明提升到 `schema_contract_ready` 以上。最终声明仍受关键路径最低有效 Evidence 和 Verdict 封顶。

## 5. 通用样例边界

L1 样例只能使用本文件中的占位符或仓库内匿名 fixture，例如：

```yaml
diagram_type: boundary
governs_object: "{{controlled_object_id}}"
```

具体 L2/L3 的项目名、私有目录、领域术语、渠道名和运行事实不得成为 L1 样板。来自下层的经验只有满足 `REPOSITORY_AND_LAYER_CONTRACT.md §5` 的跨项目升格门禁后，才能用 L1 通用命名重新定义；不得保留对下层仓库的反向引用。

## 6. 检查器待实现项

- frontmatter 的 `governs_object` 指向真实受控对象；
- 每个 P0/P1 `business_chain` 至少有一张 `diagram_type: flowchart`；
- 图正文包含 Mermaid 代码块；二进制图片不是唯一来源；
- 流程图不存在没有出边且未标记为终态的节点；
- 图中的对象版本或内容 hash 变化后，旧图进入待复核。

这些检查在分配独立规则编号并补齐回归测试前只属于 backlog，不得复用现有 C1—C7 的语义编号。
