# 智能体操作契约

第一语言为中文。文件路径、命令、字段名和行业标准可保留英文。

## 配置文件语言

- YAML、JSON Schema 和代码字段使用稳定英文标识，避免工具兼容和版本迁移问题。
- 所有非直观字段和枚举必须提供中文注释或中文生成视图。
- 面向人的描述、错误信息、命令输出和状态摘要默认使用中文。
- 中文阅读视图必须由机器权威配置生成，不允许维护第二份可编辑配置。
- 在生成器尚未实现前，优先直接给机器配置补中文注释，避免手工双写漂移。

## 阅读顺序

1. `README.zh-CN.md`
2. `project-os.yaml`
3. 本次任务对应的唯一权威文件
4. 必要时再读取其直接引用

禁止默认整仓加载。

## 权威规则

- `docs/architecture/AI_PROJECT_OS_CORE.md` 是薄内核原语、架构平面和主追溯入口的权威源。
- `docs/architecture/FRAMEWORK_EDITION_MODEL.md` 是 L1 框架版本等级与能力范围的权威源。
- `docs/architecture/REPOSITORY_AND_LAYER_CONTRACT.md` 是 L1/L2/L3 所有权、依赖、兼容和资产升格的权威源。
- `docs/architecture/AI_NATIVE_EXECUTION_MODEL.md` 是 AI 执行节点、上下文信任、版本指纹、评测和降级的权威源。
- `docs/architecture/AI_PROJECT_OS_OVERVIEW.md` 是面向人的四条不可折叠主线与阅读入口，不替代各主题权威。
- `docs/workflows/PROJECT_DELIVERY_WORKFLOW.md` 是从需求或存量恢复到 Claim、复盘和升格的推进控制流权威源。
- `docs/workflows/STAGE_EXIT_GATES.md` 是 R0、S0—S7 人类可读退出门禁与重开入口；机器记录结构由对应 governance contract 定义。
- `docs/governance/TERMINOLOGY.md` 是中文术语与稳定 term-id 的唯一权威源。
- `docs/workflows/` 是推进和架构师职责权威源。
- `docs/governance/` 是追溯、门禁、证据和评分权威源。
- `contracts/` 只定义机器结构、版本、引用和失败语义，不承载项目事实或可变治理策略；`policies/` 承载可审计的治理决策规则。
- `docs/research/RESEARCH_WORKFLOW.md` 是研究方法权威源。
- `research/` 只保存候选研究，不是事实源。
- `decisions/` 保存已接受、拒绝或被替代的正式决策。
- 提示词不得成为需求、架构或项目事实的唯一保存位置。

## 设计边界

- 薄内核只定义状态、产物、关系、门禁、声明和证据协议。
- 项目类型、业务术语和自然语言关键词不得硬编码进通用内核。
- 外部工具和开源框架必须通过适配器接入。
- 未完成研究和本地实验前，不得把候选技术写成既定依赖。
- `EXIT=0` 只是门禁必要条件，不是验收充分条件。
- 模拟运行、本地运行、只读真实预检和生产证明不得互相替代。

## 修改规则

- 优先修改唯一权威文件，不复制第二份结论。
- 新增文件前先确认现有文件不能承载该职责。
- 任何架构重大变化必须新增或替代一条架构决策记录。
- 任何上游事实、需求、契约或策略变化，都必须执行影响分析。
- 完成声明必须附验证命令、证据位置和已知缺口。
