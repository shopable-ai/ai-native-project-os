---
diagram_type: flowchart
governs_object: CHAIN-REQ-001
---

# CHAIN-REQ-001 流程图

```mermaid
flowchart LR
    A["批准业务需求"] --> B["机会价值判断"]
    B --> C{"满足批准规则？"}
    C -->|是| D["进入销售处理"]
    C -->|否| E["安全拒绝"]
```
