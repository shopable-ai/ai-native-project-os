# domain/ 批准事实与需求目录

本目录保存 L2 自己批准的业务事实、需求、链路和能力，不保存原始来源或运行产物。

```text
domain/
├── glossary.md          # 统一术语与批准 fact
├── mvp/                 # 批准 requirement
├── chains/              # 条件启用：批准 business_chain
└── capability-map/      # 条件启用：批准 business_capability
```

原始材料只能先形成 `source`、候选事实、假设或未知；经合法 Decision Gate 后，才可进入本目录。低风险对象可引用当前认证策略，高风险目标、责任、scope 或风险变化必须引用可追责人类；`specs/` 不能指向原始材料直接驱动实现。
