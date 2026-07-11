---
diagram_type: flowchart
governs_object: CHAIN-FIX-001
title: 匿名 fixture 主流程
description: 展示受控输入、执行、契约验证、证据生成与失败重开的主路径。
---

# 匿名 fixture 主流程

```mermaid
flowchart TD
    A[接收已批准输入] --> B[执行有界任务]
    B --> C{契约是否通过}
    C -->|是| D[生成证据]
    C -->|否| E[按恢复目标重开]
```
