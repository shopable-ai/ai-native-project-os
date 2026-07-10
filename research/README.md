# 研究区

- `registry.yaml`：当前研究任务的唯一登记表。
- `active/{research_id}_{slug}/`：研究工作流运行时创建的活动研究包。
- `archive/{research_id}_{slug}/`：决策完成后保存原始研究和证据。
- 已批准结论必须升格到对应权威目录；研究区不保留第二份正式结论。

本设计基线不预建空研究包。开始 RSH-OSS-001 后，才从 `templates/research-package/` 实例化首个活动研究目录。
