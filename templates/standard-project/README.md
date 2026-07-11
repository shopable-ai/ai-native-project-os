# 标准版项目模板（Greenfield）

适用条件：`project_type: greenfield`，`base_governance_profile: standard`。
复制整个目录到你的 L2 业务仓库根目录，填写 `{{ }}` 占位字段后删除本说明。

## 使用步骤

```bash
# 1. 复制模板（以 operate-auto-customer 为例）
cp -r path/to/ai-project-os/templates/standard-project/* your-l2-repo/

# 2. 填写 project-os.lock.yaml（见下方文件）

# 3. 建立 domain/ 业务真相层（见 domain/ 目录骨架）

# 4. 按 governance/rules/ 下的中文模板定义并由人类批准审核规则集

# 5. 运行接入检查器
python3 path/to/ai-project-os/linters/check_controlled_objects.py . --l2-mode --report

# 6. 验收门禁：EXIT=0
```

## 接入后检查清单

```
[ ] project-os.lock.yaml 存在且版本在兼容范围内
[ ] domain/glossary.md 已填写，至少包含本项目核心术语的 stable_id
[ ] domain/ 的事实文件有 approver 字段（不能由 AI 自证）
[ ] governance/rules/ 的规则集由人类批准并发布，成员文件/hash 与 scope 完整
[ ] 普通内容由独立 AI reviewer 审核，不进入 waiting_approval
[ ] specs/ 的 traceability.md 指向 domain/，不再指向 reference/ 中的原始素材
[ ] 运行检查器 EXIT=0
[ ] project-os.yaml.scoring_evidence 追加本次接入 Evidence 引用
```
