# I/O 契约模板

| 问题 | 时机 | 输入 | 输出 | 下一步 |
|---|---|---|---|---|
| producer 与 consumer 如何在成功、失败和演进时保持可验证兼容？ | 存在组件、服务、Workflow 或 Skill 边界时 | 双方身份、request/event/result schema 和运行约束 | 可测试、可迁移的 I/O 契约 | 生成双方 contract tests 并验证兼容 |

## 复制后的完整树

```text
{{io_contract_root}}/
├── README.md                  # 必需：问题导航与完整树
├── io-contract.yaml           # 必需：协议、故障和兼容机器定义
├── adapters/                  # 条件启用：外部协议适配器实现
├── migrations/               # 条件启用：破坏性变更迁移资产
└── Evidence/Verdict/artifacts # 运行时生成：测试证据、裁决和输出
```

模板不复制业务政策；`error_taxonomy` 等字段引用本 L2 已批准分类。缺少 failure envelope、迁移或 contract tests 时，兼容结论必须 fail-closed。
