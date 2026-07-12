# 权限、外部副作用与项目隔离

本文件是 `standard` 基础治理配置下责任分离、Skill/Tool 权限、外部副作用和跨项目隔离的唯一权威源。这些控制由风险和动作本身触发，不推迟到 `production` 叠加能力；真实外部写不自动等同于生产运行。

## 1. 责任分离

| 责任 | 含义 | 高风险约束 |
|---|---|---|
| `owner` | 对对象生命周期和业务后果负责 | 必须是可追责的人类角色 |
| `executor` | 产生内容或执行动作 | 不能自批、自证自己的高风险声明 |
| `approver` | 记录规则、事实、需求、范围等治理对象的决策权威 | 自动路径绑定激活 Policy；高风险变化绑定可验证人类 principal；不承担日常逐条内容审核 |
| `ai_reviewer` | 按 active Markdown 规则独立审核内容、Evidence、风险和质量 | 不能与生成节点复用同一 Run step、prompt/context role 或 attempt |
| `verifier` | 独立检查 Evidence 与判据 | 不得修改原始 Evidence 迎合结论 |
| `action_authorizer` | 为明确的高风险或不可逆动作签发受限授权 | 必须绑定精确目标、内容/hash、期限和单次消费语义 |

低风险场景允许同一基础模型承担生成与审核的不同执行节点，但节点、上下文、attempt 和 Evidence 必须独立。涉及真实外部写、敏感数据、例外、高风险 Verdict 或生产声明时，executor、ai_reviewer、verifier 和 action_authorizer 按路由策略满足职责分离，owner 必须是可追责人类。

身份校验基于不可伪造的 `actor_id`、`actor_kind`、真实 principal/session、`delegated_by` 和 role binding，而不是显示名称。高风险 Fact、授权、Verdict 和 Claim 必须绑定人工票据或独立 gate 签名；同一 principal、会话或控制主体使用多个角色别名仍视为冲突。

## 2. 审核与授权不得互相替代

内容审核通过不授予动作权限。`ai_review_verdict.decision: allow` 只证明被审核对象满足已绑定规则集，不能生成 Capability Grant、Approval Ticket、Secret Lease 或 Authorization Snapshot。

动作授权也不批准内容。即使目标、账号和副作用票据有效，只要适用的 AI 审核为 `blocked/rule_gap`、规则集失效或审核 Evidence 不完整，动作仍必须 fail-closed。低风险治理对象可由当前认证策略决策；人工集中在目标/责任/scope 变化、阈值降低、权限扩大、例外、剩余风险接受和高风险动作授权，不成为日常逐条 reviewer。

## 3. 能力授权

Skill 和 Tool 不获得项目级通配权限，必须逐项声明：

```yaml
extends: controlled_object_base/v1
capability_id: capability-id
project_id: project-id
namespace: project-id/environment/resource-type
route_decision_ref: route-id
control_set_ref: control-set-id
control_set_hash: sha256
actor_id: actor-or-tool
environment: environment-id
resource_selectors: []
allowed_operations: []
explicit_denies: []
file_roots: []
network_destinations: []
secret_refs: []
data_classes: []
external_actions: []
purpose: description
issued_for_run: run-id
policy_version: version
max_uses: 1
approved_by: action-authorizer-or-policy
issued_at: timestamp
expires_at: timestamp
revocation_ref: null
```

默认拒绝且 deny 优先，未知操作或字段 fail-closed。文件权限以规范化绝对 realpath 和 `read/create/modify/delete/execute` 分开授权，拒绝符号链接、挂载点、相对路径或路径变化造成的根目录逃逸；临时目录继承项目 namespace，删除和跨根移动单独审批。

每份 Capability Grant、秘密 lease、审批票据和副作用 Operation 必须绑定当前 `route_decision_ref`、`control_set_ref` 与 `control_set_hash`。治理路由或控制集变化时，旧授权先进入待复核或撤销，不能因基础配置名称相同而继续复用。

激活门禁使用的 `authorization_snapshot_ref` 不能是任意字符串或单份 Grant 的别名。授权快照必须按 `contracts/governance/authorization-snapshot-contract.yaml` 聚合并锁定主体绑定、Grant、审批票据、秘密 lease、职责分离结果、路由/control set、有效期、撤销状态、验证 Evidence 和签名；只有 `verified + fresh + active + unexpired` 的快照有效。

网络权限固定 scheme、host、port、动作、TLS 身份、重定向和解析后地址范围；默认拒绝未授权私网与 metadata endpoint。声明为读取的外部动作必须由契约证明无副作用，未知语义按写操作治理。

秘密只通过项目绑定的短时 lease 引用，记录 owner、用途、主体、环境、有效期、轮换和撤销传播。prompt、Tool I/O、异常、日志、trace、Evidence 和缓存写入前必须脱敏与秘密扫描；疑似泄漏时隔离产物、撤销凭据并阻断 Claim。

## 4. 项目隔离

每个 L3 必须拥有稳定 `project_id` 和不可碰撞 namespace。namespace 由 `project_id + environment + resource_type` 生成并注册，创建时检测碰撞；空值、`default`、`global` 或未登记 namespace 一律 fail-closed。至少隔离：

- 文件允许根目录和临时目录；
- 缓存 key 与持久化目录；
- RAG collection/index namespace；
- Run、Evidence、日志和 trace；
- secret owner 与授权作用域；
- 外部账号、目标资源和幂等键前缀。

缓存、RAG、日志、trace、secret 和幂等键必须携带完整 namespace。跨项目读取或复用必须有版本化共享资产 ID、去敏规则、消费者列表、复制/引用方式、撤销/删除传播和审批；默认拒绝，不得直接挂接源项目私有存储。

## 5. 副作用等级

| 等级 | 语义 | 最低控制 |
|---|---|---|
| `none` | 纯计算或已批准本地读取 | 输入白名单和审计记录 |
| `read_external` | 读取外部真实系统 | 范围限制、凭据隔离、数据最小化、禁止写入 |
| `write_reversible` | 可明确撤销的外部写入 | 审批票据、幂等键、前后快照、超时、回执和撤销步骤 |
| `write_irreversible` | 发送、付款、删除、发布等不可逆动作 | 每次人工门禁、精确目标预览、短时授权、双重检查、失败关闭 |

安全、隐私、真实发送、付款、删除和生产发布必须有人工门禁，不允许静默豁免。

## 6. 外部副作用记录

执行前必须绑定：`approval_ticket`、Run、namespace、真实 actor、外部账号、动作、精确目标集合、规范化内容/金额及 hash、Tool/策略版本、环境、幂等键、超时、最大重试、撤销或补偿方案和 `max_uses`。不可逆动作默认单次消费，票据以原子 `pending → consumed` 转换；任何绑定内容变化、重复消费或并发冲突都使审批失效。

执行后必须保存外部回执、观测状态和撤销能力。未知结果不得自动重放；先查询外部状态。超时、审批过期、目标不一致、权限不足、回执缺失或撤销失败都必须 fail-closed，Run 不能标记语义成功。

副作用使用稳定 `operation_id` 和独立 `attempt_id`，并在 append-only 账本中迁移 `prepared → approved → dispatched → acknowledged → reconciled/unknown/compensated`。调用前持久化 operation、幂等键和票据消费；调用后保存外部 request ID、回执和响应 hash。恢复只对账同一 operation，不能创建新动作假装重试。

重试只在动作已证明幂等或外部状态证明未发生时允许。无外部幂等和可靠查询能力的不可逆动作禁止自动恢复。`unknown` 必须建立对账 case（owner、外部标识、查询 Evidence、范围、期限），阻断后续动作和接受裁决，不能自动重发。

高风险外部 Evidence 必须由独立 verifier 通过外部状态读取或第二可信通道确认；补偿 Verdict 分别记录原动作、补偿动作、最终状态和不可恢复残余影响。

## 7. 声明边界

本文件当前只有设计语义。尚无权限代理、秘密管理、隔离检查器或副作用运行证明；因此不能声明跨项目隔离已验证或生产安全已就绪。
