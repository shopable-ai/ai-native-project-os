# 标准版 L2 项目模板（Greenfield）

| 问题 | 时机 | 输入 | 输出 | 下一步 |
|---|---|---|---|---|
| 新建型业务系统如何接入 AI Project OS？ | L2 Greenfield 建立首个批准需求时 | L1 版本、L2 批准事实和 owner | 位于 L2 根目录的标准控制骨架 | 复制 fixture、替换批准事实并运行接入检查 |

本模板适用于 `project_type: greenfield`（新建型）、`base_governance_profile: standard`（标准基础治理配置）的 L2 业务系统。目录中的 `REQ-001` 和 `REQ-FUNC-001` 是已填好的通用 fixture，用来演示批准事实、业务需求、功能需求、baseline、Spec 和 review evidence 如何追溯；复制后必须替换为真实批准内容。

默认直接复制到 L2 根目录，不套 `projects/{project_id}/`；后者只有多实例隔离证据成立时才条件启用。

## 复制后的完整目录

```text
{{l2_repo}}/
├── project-os.lock.yaml                         # 必需：锁定 L1 版本和协议
├── domain/                                      # 必需：L2 批准事实与需求
│   ├── README.md                                # 必需：目录职责说明
│   ├── glossary.md                              # 必需：示例 fact FACT-001
│   └── mvp/
│       └── REQ-001.md                           # 必需：示例 requirement
├── requirements/                                # 必需：人机需求设计层
│   ├── README.md                                # 必需：需求权威与操作边界
│   ├── 项目地图.md                              # 必需：人类每日引用入口
│   ├── functions/
│   │   └── FUNC-001_功能需求卡.md               # 必需：示例功能需求权威
│   ├── baselines/
│   │   └── REQ-BASELINE-001.yaml                # 必需：批准需求版本/hash 集合
│   ├── context/
│   │   └── CTX-001.yaml                         # 条件启用：AI 上下文快照
│   └── generated/
│       └── README.md                            # 运行时生成：只定义派生视图边界
├── governance/
│   └── rules/                                   # standard 基础治理配置必需
├── specs/
│   └── REQ-FUNC-001/                            # 必需：功能需求对应 Spec 五件套
│       ├── spec.md
│       ├── plan.md
│       ├── tasks.md
│       ├── acceptance.md
│       └── traceability.md
├── reviews/
│   └── REQ-FUNC-001-review-evidence.yaml        # 必需：fixture review evidence
├── projects/{project_id}/                       # 条件启用：需要 L3 实例隔离时创建
├── runs/                                        # 运行时生成：Run 和临时执行产物
└── artifacts/                                   # 运行时生成：经验收的交付物
```

模板不预建空的 `projects/`、`runs/` 或 `artifacts/`。只有在条件成立或首个正式产物出现时创建，避免空目录被误读为能力已经实现。

## 使用步骤

```bash
# 1. 复制模板到待接入的 L2 仓库
cp -R {{l1_repo}}/templates/standard-project/. {{l2_repo}}/

# 2. 填写 L1 版本锁定
${EDITOR} {{l2_repo}}/project-os.lock.yaml

# 3. 用已批准事实、意图和需求替换 FACT-001 / REQ-001 / REQ-FUNC-001 fixture

# 4. 人类批准功能需求，创建新 baseline，再更新 Spec 五件套和 Evidence

# 5. 运行接入检查器
python3 {{l1_repo}}/linters/check_controlled_objects.py \
  {{l2_repo}} --l2-mode --report
```

## 完整样例的声明边界

- `domain/glossary.md` 演示一条由人类批准的 `fact`。
- `domain/mvp/REQ-001.md` 演示一条由该 fact 推导的 P1 `requirement`。
- `requirements/functions/FUNC-001_功能需求卡.md` 是人类主要审查单元；它区分批准约束和候选方案。
- `requirements/baselines/REQ-BASELINE-001.yaml` 与 `context/CTX-001.yaml` 只演示结构，不是真实批准或运行证明。
- `specs/REQ-FUNC-001/` 演示功能需求进入范围、计划、任务、验收和追溯五件套。
- `reviews/REQ-FUNC-001-review-evidence.yaml` 只记录 fixture 结构检查，`proof_level` 为 `control_package`。
- 样例没有签发 Acceptance Verdict 或 Completion Claim，不证明实现、本地运行、真实环境或生产能力。

## 接入后检查清单

```text
[ ] project-os.lock.yaml 的版本、兼容范围、时间和负责人已填写
[ ] FACT-001 / REQ-001 / REQ-FUNC-001 已替换为 L2 自己的事实、意图和需求
[ ] fact/requirement 具有 stable_id、canonical_path 和人类 approver
[ ] 功能需求已完成 AI 自检与人类批准，baseline 锁定精确 version/content_hash
[ ] Spec 只引用当前 baseline 成员，没有从功能树或聊天直接生成
[ ] governance/rules/ 的 active 规则集具有成员 hash、scope 和批准记录
[ ] specs/{spec_id}/traceability.md 只指向批准对象，不指向原始来源
[ ] review Evidence 明确环境、范围、验证状态和禁止外推项
[ ] --l2-mode 返回 EXIT=0，且 L2 自己的语义验收通过
```
