# domain/ 目录骨架
#
# 本目录是 L2 业务真相层的根目录。
# 所有文件都是"批准事实"（object_type: fact 或 requirement），
# 必须有 approver（不能由 AI 自证），不能由原始素材（reference/ 或 .prompts/）直接驱动。
#
# 标准子目录：
#   domain/glossary.md        ← 统一语言（业务术语单一定义处）
#   domain/mvp/               ← MVP 意图与最小目标
#   domain/chains/            ← 业务链路（对应 CONTROLLED_OBJECT_MODEL business_chain 类型）
#   domain/capability-map/    ← 能力树（business_capability 类型）
#
# 对应 L1 对象类型映射：
#   glossary 条目      → fact（批准事实）
#   mvp/*.md           → requirement（批准需求）
#   chains/*.md        → business_chain（从 scenario/trigger 推导）
#   capability-map/    → business_capability（从 business_chain 推导）
#
# 来源规则：
#   原始材料（reference/ 等）→ 候选事实/假设（source 对象）
#   经人类 approver 批准后 → 升格为 fact/requirement（进入本目录）
#   specs/ traceability.md 指向本目录（不指向 reference/）

此文件为说明占位，不是可编辑的受控对象，创建真实 domain/ 内容时删除本文件。
