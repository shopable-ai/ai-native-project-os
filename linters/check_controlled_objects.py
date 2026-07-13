#!/usr/bin/env python3
"""
最小追溯检查器 — ai-project-os Phase 0 核心产物

检查项直接来自 reviews/p0-design-revision-score.yaml open_items：
  C1  stable_id 在本仓库内唯一，且 canonical_path 文件存在
  C2  object_type=source 不得驱动 Spec/Task/Workflow/Skill（绕过批准事实）
  C3  p0/p1 优先级需求必须有对应 spec + traceability 文件出口
  C4  L1 文件不得反向引用 L2/L3 具体仓库路径（单向依赖强制）
  C5  proof_level 枚举只在 GATES_PROOF_SCORING.md 一处定义
  C6  AI 自动审核不得降级为逐条等待人工批准
  C7  AI 审核裁决必须绑定规则、独立 Run、Evidence 和有界改写
  C8  阶段门禁契约完整覆盖 R0、S0—S7 及记录/证据/失效语义
  C9  模板包满足机器契约声明的文件、字段、章节和值约束
  C10 术语 term-id 只由唯一权威定义并与机器清单精确一致
  C11 权威路径与契约引用存在、唯一且版本匹配
  C12 结构化业务链/工程链具备按风险字段要求的 Mermaid 图
  C14 审核策略包、预注册测试、认证与激活路由形成静态闭环

退出码 0 = 无 P0/P1 发现；1 = 有发现（CI 可拦）。只读，不改任何文件。

用法：
  python3 linters/check_controlled_objects.py <repo_root> [--report] [--l2-mode]

  --report    打印详细报告（默认只打印摘要）
  --l2-mode   L2 项目接入模式（额外检查 project-os.lock 是否存在）
"""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path
from typing import Optional

import yaml

# ── 常量 ──────────────────────────────────────────────────────────────────────

PROOF_LEVEL_AUTHORITY = "docs/governance/GATES_PROOF_SCORING.md"
PROOF_LEVEL_ENUM = [
    "control_package",
    "candidate_assets_ready",
    "schema_contract_ready",
    "contract_tests_ready",
    "fixture_runtime_proven",
    "local_runtime_proven",
    "readonly_real_preflight_passed",
    "production_proof",
]

# 具体 L3 namespace 路径特征。`projects/{project_id}/` 这类通用占位符不匹配。
L2_PATH_PATTERNS = [
    r"projects/[a-zA-Z0-9_\-]+/",
]

# 被认为是"实现驱动"的关系关键词（source 不得出现在这些上下文）
IMPL_RELATION_KEYWORDS = [
    "implements",
    "governed_by",
    "consumes",
]

# 文件扩展名白名单（只扫这些）
SCAN_EXTENSIONS = {".md", ".yaml", ".yml", ".json", ".py"}

# ── 数据结构 ───────────────────────────────────────────────────────────────────

class Finding:
    def __init__(self, rule: str, severity: str, file: str, line: int, message: str):
        self.rule = rule
        self.severity = severity  # P0 / P1 / INFO
        self.file = file
        self.line = line
        self.message = message

    def as_dict(self) -> dict:
        return {
            "rule": self.rule,
            "severity": self.severity,
            "file": self.file,
            "line": self.line,
            "message": self.message,
        }


# ── 工具函数 ──────────────────────────────────────────────────────────────────

def rel(repo: Path, p: Path) -> str:
    try:
        return str(p.relative_to(repo))
    except ValueError:
        return str(p)


def read_text(p: Path) -> str:
    try:
        return p.read_text(encoding="utf-8", errors="ignore")
    except OSError:
        return ""


def resolve_repo_path(
    repo: Path,
    raw: object,
    rule: str,
    context: str,
) -> tuple[Path | None, list[Finding]]:
    """解析受控相对路径；绝对路径、父级跳转和仓库逃逸一律 fail-closed。"""
    if not isinstance(raw, str) or not raw:
        return None, [Finding(rule, "P0", ".", 0, f"{context} 必须是非空相对路径")]
    raw_path = Path(raw)
    if raw_path.is_absolute() or ".." in raw_path.parts:
        return None, [Finding(rule, "P0", ".", 0, f"{context} 必须是仓库内且不含 '..' 的相对路径: {raw}")]
    resolved = (repo / raw_path).resolve()
    try:
        resolved.relative_to(repo.resolve())
    except ValueError:
        return None, [Finding(rule, "P0", ".", 0, f"{context} 解析后越过仓库边界: {raw}")]
    return resolved, []


def iter_repo_files(repo: Path, skip_run_artifacts: bool = False) -> list[Path]:
    """遍历受扫描文件，跳过元数据、隔离 worktree 和 checker fixture。"""
    result = []
    for p in repo.rglob("*"):
        if not p.is_file():
            continue
        parts = p.relative_to(repo).parts
        if ".git" in parts or ".worktrees" in parts or "worktrees" in parts or ".shopme" in parts:
            continue
        if len(parts) >= 2 and parts[:2] in {
            ("fixtures", "checker-positive"),
            ("fixtures", "checker-negative"),
        }:
            continue
        if p.suffix not in SCAN_EXTENSIONS:
            continue
        # 跳过运行产物目录（runs/ 是可删除重建的，不是正式受控对象）
        if skip_run_artifacts and "runs" in parts:
            continue
        result.append(p)
    return result


# ── 检查项实现 ─────────────────────────────────────────────────────────────────

def check_c1_stable_id_unique(repo: Path, files: list[Path]) -> list[Finding]:
    """C1: stable_id 在本仓库内唯一，且声明的 canonical_path 存在。"""
    findings: list[Finding] = []
    seen: dict[str, str] = {}  # stable_id -> 首次出现文件

    for p in files:
        text = read_text(p)
        # Markdown 代码块内的内容是示例，不扫
        in_code_block = False
        lines = text.splitlines()
        for i, line in enumerate(lines, 1):
            if line.strip().startswith("```"):
                in_code_block = not in_code_block
            if in_code_block:
                continue
            # 只有顶层 stable_id 定义对象；baseline/manifest 内缩进的 stable_id 是引用。
            m = re.match(r"^stable_id\s*:\s*['\"]?([a-zA-Z0-9_\-\.]+)['\"]?", line)
            if not m:
                continue
            sid = m.group(1)
            rp = rel(repo, p)
            if sid in seen:
                findings.append(Finding(
                    "C1", "P0", rp, i,
                    f"stable_id '{sid}' 重复定义，首次出现在 {seen[sid]}",
                ))
            else:
                seen[sid] = rp

            # 检查 canonical_path 是否存在（跳过模板占位符和示例值）
            cp_m = re.search(r"canonical_path\s*:\s*['\"]?([^\s'\"#\{\}]+)['\"]?", text)
            if cp_m:
                cp_val = cp_m.group(1)
                # 跳过模板占位符（如 path/to/authority、{{placeholder_name}}）
                if cp_val.startswith("path/to") or "{{" in cp_val or cp_val == "null":
                    pass
                else:
                    candidates = [repo / cp_val]
                    parts = p.relative_to(repo).parts
                    if len(parts) >= 2 and parts[0] == "templates":
                        candidates.append(repo / parts[0] / parts[1] / cp_val)
                    if not any(candidate.exists() for candidate in candidates):
                        findings.append(Finding(
                            "C1", "P1", rp, i,
                            f"canonical_path '{cp_val}' 文件不存在",
                        ))
    return findings


def check_c2_source_no_bypass(repo: Path, files: list[Path]) -> list[Finding]:
    """C2: object_type=source 的文件不得出现在实现关系链中。"""
    findings: list[Finding] = []
    # 找出所有声明 object_type: source 的文件
    source_files: set[str] = set()
    for p in files:
        text = read_text(p)
        if re.search(r"object_type\s*:\s*['\"]?source['\"]?", text):
            source_files.add(rel(repo, p))

    if not source_files:
        return findings

    # 扫描其他文件是否通过实现关系关键词引用了 source 文件
    for p in files:
        rp = rel(repo, p)
        if rp in source_files:
            continue
        text = read_text(p)
        for i, line in enumerate(text.splitlines(), 1):
            for kw in IMPL_RELATION_KEYWORDS:
                if kw in line:
                    for sf in source_files:
                        sf_name = Path(sf).stem
                        if sf_name in line:
                            findings.append(Finding(
                                "C2", "P0", rp, i,
                                f"object_type=source 的 '{sf}' 被 '{kw}' 关系直接引用，绕过批准事实流程",
                            ))
    return findings


def check_c3_p0p1_has_spec_traceability(repo: Path, files: list[Path]) -> list[Finding]:
    """C3: 标记 p0/p1 的需求必须有对应 spec + traceability 文件。"""
    findings: list[Finding] = []
    specs_dir = repo / "specs"
    if not specs_dir.exists():
        # L1 自身不要求 specs/，L2 模式才检查
        return findings

    for p in files:
        text = read_text(p)
        if not re.search(r"(priority|weight)\s*:\s*['\"]?(p0|p1)['\"]?", text, re.IGNORECASE):
            continue
        object_type_match = re.search(
            r"^object_type\s*:\s*['\"]?([a-zA-Z0-9_\-]+)['\"]?",
            text,
            re.MULTILINE,
        )
        if object_type_match and object_type_match.group(1) != "requirement":
            continue
        requirement_kind_match = re.search(
            r"^requirement_kind\s*:\s*['\"]?([a-zA-Z0-9_\-]+)['\"]?",
            text,
            re.MULTILINE,
        )
        # 业务/目标/质量/约束需求先由功能需求承接，不直接要求同名 Spec。
        if requirement_kind_match and requirement_kind_match.group(1) != "functional":
            continue
        rp = rel(repo, p)
        # 检查是否有对应的 spec 目录（简单启发：spec_id 字段）
        sid_m = re.search(r"stable_id\s*:\s*['\"]?([a-zA-Z0-9_\-]+)['\"]?", text)
        if not sid_m:
            continue
        sid = sid_m.group(1)
        spec_dir = specs_dir / sid
        if not spec_dir.exists():
            findings.append(Finding(
                "C3", "P1", rp, 0,
                f"P0/P1 需求 '{sid}' 在 specs/{sid}/ 没有对应控制包目录",
            ))
            continue
        traceability = spec_dir / "traceability.md"
        if not traceability.exists():
            findings.append(Finding(
                "C3", "P1", rp, 0,
                f"P0/P1 需求 '{sid}' 的 specs/{sid}/traceability.md 不存在",
            ))
    return findings


def check_c4_l1_no_l2_refs(repo: Path, files: list[Path]) -> list[Finding]:
    """C4: L1 文件不得反向引用 L2/L3 具体路径（单向依赖）。"""
    findings: list[Finding] = []
    patterns = [re.compile(pat) for pat in L2_PATH_PATTERNS]

    for p in files:
        rp = rel(repo, p)
        text = read_text(p)
        for i, line in enumerate(text.splitlines(), 1):
            for pat in patterns:
                if pat.search(line):
                    # 排除注释行、Python 字符串定义行（linter 模式字符串）
                    stripped = line.strip()
                    if stripped.startswith("#") or stripped.startswith("//") or stripped.startswith("r\""):
                        continue
                    findings.append(Finding(
                        "C4", "P1", rp, i,
                        f"L1 文件引用了 L2/L3 路径: {line.strip()[:80]}",
                    ))
    return findings


def check_c5_proof_level_single_authority(repo: Path, files: list[Path]) -> list[Finding]:
    """C5: proof_level 枚举只在 GATES_PROOF_SCORING.md 一处定义。"""
    findings: list[Finding] = []
    authority_path = repo / PROOF_LEVEL_AUTHORITY
    authority_rel = PROOF_LEVEL_AUTHORITY

    for p in files:
        rp = rel(repo, p)
        if rp == authority_rel:
            continue
        text = read_text(p)
        for level in PROOF_LEVEL_ENUM:
            # 检查是否有"定义"性质的出现（枚举声明、枚举列表）
            # 允许：只是引用（如 proof_level: fixture_runtime_proven）
            # 不允许：重新列出枚举表（如 | fixture_runtime_proven | ...）
            if re.search(rf"^\s*[|`]\s*{re.escape(level)}\s*[|`]", text, re.M):
                findings.append(Finding(
                    "C5", "P1", rp, 0,
                    f"proof_level 枚举值 '{level}' 在非权威文件中以表格形式重新定义，"
                    f"应只在 {authority_rel} 维护",
                ))
                break  # 每个文件只报一次
    return findings


def check_c6_ai_review_no_routine_human_wait(
    repo: Path, files: list[Path]
) -> list[Finding]:
    """C6: 结构化声明为 AI 自动审核的节点不得等待人工逐条批准。"""
    findings: list[Finding] = []
    for p in files:
        if p.suffix not in {".yaml", ".yml", ".json"}:
            continue
        text = read_text(p)
        if not re.search(r"^\s*review_mode\s*:\s*ai_automated\s*$", text, re.M):
            continue
        wait_match = re.search(r"^\s*(?:work_status|next_state)\s*:\s*waiting_approval\s*$", text, re.M)
        if wait_match:
            line = text[:wait_match.start()].count("\n") + 1
            findings.append(Finding(
                "C6", "P0", rel(repo, p), line,
                "AI 自动审核节点不得进入 waiting_approval；应自动改写、重新审核、"
                "安全阻断或登记规则缺口",
            ))
    return findings


def _manifest_scalar(text: str, field: str) -> Optional[str]:
    match = re.search(
        rf"^\s*{re.escape(field)}\s*:\s*([^#\n]+?)\s*$",
        text,
        re.M,
    )
    if not match:
        return None
    value = match.group(1).strip().strip("'\"")
    return value or None


def check_c7_ai_review_manifest(repo: Path, files: list[Path]) -> list[Finding]:
    """C7: 校验 AI Review Verdict 实例的最小静态绑定。"""
    findings: list[Finding] = []
    required = [
        "subject_ref",
        "subject_hash",
        "generator_run_ref",
        "review_run_ref",
        "reviewer_actor_id",
        "reviewer_execution_node_ref",
        "rule_set_ref",
        "rule_set_hash",
        "evidence_refs",
        "decision",
        "max_rewrite_attempts",
    ]
    for p in files:
        if p.suffix not in {".yaml", ".yml", ".json"}:
            continue
        text = read_text(p)
        if _manifest_scalar(text, "object_type") != "ai_review_verdict":
            continue
        if _manifest_scalar(text, "contract_id"):
            continue

        missing = [field for field in required if _manifest_scalar(text, field) is None]
        if missing:
            findings.append(Finding(
                "C7", "P0", rel(repo, p), 0,
                "AI 审核裁决缺少必填绑定: " + ", ".join(missing),
            ))

        generator_run = _manifest_scalar(text, "generator_run_ref")
        review_run = _manifest_scalar(text, "review_run_ref")
        if generator_run and review_run and generator_run == review_run:
            findings.append(Finding(
                "C7", "P0", rel(repo, p), 0,
                "generator_run_ref 与 review_run_ref 必须独立",
            ))

        decision = _manifest_scalar(text, "decision")
        rewrite_limit = _manifest_scalar(text, "max_rewrite_attempts")
        if decision == "rewrite_required":
            try:
                valid_limit = int(rewrite_limit or "0") > 0
            except ValueError:
                valid_limit = False
            if not valid_limit:
                findings.append(Finding(
                    "C7", "P0", rel(repo, p), 0,
                    "rewrite_required 必须声明正整数 max_rewrite_attempts",
                ))
    return findings


def _load_yaml(repo: Path, path: Path, rule: str) -> tuple[object | None, list[Finding]]:
    """加载 YAML；解析错误是契约检查失败，不能静默降级。"""
    try:
        return yaml.safe_load(path.read_text(encoding="utf-8")), []
    except (OSError, yaml.YAMLError) as exc:
        return None, [Finding(rule, "P0", rel(repo, path), 0, f"YAML 无法解析: {exc}")]


def _dotted_value(data: object, dotted: str) -> tuple[bool, object | None]:
    current = data
    for part in dotted.split("."):
        if not isinstance(current, dict) or part not in current:
            return False, None
        current = current[part]
    return True, current


def check_c8_stage_gate_contract(repo: Path, files: list[Path]) -> list[Finding]:
    """C8: 阶段门禁契约完整覆盖阶段、独立坐标、记录和反例。"""
    del files
    path = repo / "contracts/governance/stage-exit-gates-contract.yaml"
    if not path.is_file():
        return [Finding("C8", "P0", rel(repo, path), 0, "阶段门禁契约不存在")]
    data, findings = _load_yaml(repo, path, "C8")
    if findings:
        return findings
    if not isinstance(data, dict):
        return [Finding("C8", "P0", rel(repo, path), 0, "阶段门禁契约顶层必须是映射")]

    expected_stages = {"R0", *(f"S{i}" for i in range(8))}
    stages = data.get("stages")
    if not isinstance(stages, dict) or set(stages) != expected_stages:
        findings.append(Finding("C8", "P0", rel(repo, path), 0, "stages 必须精确覆盖 R0、S0—S7"))
    stage_lists = (
        "required_inputs", "required_artifacts", "exit_criteria",
        "evidence_requirements", "invalidation_triggers", "reopen_targets",
    )
    if isinstance(stages, dict):
        for stage_name in sorted(expected_stages & set(stages)):
            stage = stages[stage_name]
            for field in stage_lists:
                if not isinstance(stage, dict) or not isinstance(stage.get(field), list) or not stage[field]:
                    findings.append(Finding("C8", "P0", rel(repo, path), 0, f"{stage_name}.{field} 必须是非空列表"))

    axes = {
        "stage", "work_status", "approval_status", "implementation_status",
        "proof_level", "framework_edition", "governance_profile",
    }
    independent_axes = data.get("independent_axes")
    if not isinstance(independent_axes, list) or any(not isinstance(item, str) for item in independent_axes):
        findings.append(Finding("C8", "P0", rel(repo, path), 0, "independent_axes 必须是 list[str]"))
    elif set(independent_axes) != axes:
        findings.append(Finding("C8", "P0", rel(repo, path), 0, "independent_axes 不完整或包含额外坐标"))
    if not isinstance(data.get("invariants"), list) or not data["invariants"]:
        findings.append(Finding("C8", "P0", rel(repo, path), 0, "顶层 invariants 必须非空"))

    record = data.get("stage_gate_record")
    required_record_fields = {
        "stage", "scope", "work_status", "approval_status", "implementation_status",
        "proof_level", "framework_edition", "governance_profile", "stage_definition_ref",
        "stage_definition_hash", "exit_criterion_results", "required_object_refs",
        "required_proof_level", "verification_commands", "result", "uncovered_items",
        "waivers", "approved_by", "verified_by", "checked_at", "valid_until",
        "invalidation_conditions", "reopen_target", "evidence_refs", "evidence_hashes",
    }
    criterion_fields = {"criterion_ref", "criterion_hash", "status", "evidence_refs", "waiver_ref"}
    if not isinstance(record, dict):
        findings.append(Finding("C8", "P0", rel(repo, path), 0, "stage_gate_record 必须存在"))
    else:
        record_fields = record.get("required_fields")
        if not isinstance(record_fields, list) or any(not isinstance(item, str) for item in record_fields):
            findings.append(Finding("C8", "P0", rel(repo, path), 0, "stage_gate_record.required_fields 必须是 list[str]"))
        elif not required_record_fields.issubset(set(record_fields)):
            findings.append(Finding("C8", "P0", rel(repo, path), 0, "stage_gate_record.required_fields 不完整"))
        criterion = record.get("exit_criterion_result")
        criterion_required_fields = criterion.get("required_fields") if isinstance(criterion, dict) else None
        if not isinstance(criterion_required_fields, list) or any(not isinstance(item, str) for item in criterion_required_fields):
            findings.append(Finding("C8", "P0", rel(repo, path), 0, "exit_criterion_result.required_fields 必须是 list[str]"))
        elif not criterion_fields.issubset(set(criterion_required_fields)):
            findings.append(Finding("C8", "P0", rel(repo, path), 0, "exit_criterion_result.required_fields 不完整"))
        if not isinstance(record.get("invariants"), list) or not record["invariants"]:
            findings.append(Finding("C8", "P0", rel(repo, path), 0, "stage_gate_record.invariants 必须非空"))

    manifest = data.get("manifest_example")
    manifest_required = {"stage", "exit_criterion_results", "evidence_refs", "evidence_hashes"}
    if not isinstance(manifest, dict) or not manifest_required.issubset(manifest):
        findings.append(Finding("C8", "P1", rel(repo, path), 0, "manifest_example 缺少记录、criterion 或 Evidence 示例"))
    negative = data.get("negative_examples")
    if not isinstance(negative, dict) or not negative or "missing_evidence" not in negative:
        findings.append(Finding("C8", "P1", rel(repo, path), 0, "negative_examples 必须包含 missing_evidence 反例"))
    return findings


def _markdown_has_section(text: str, section: str) -> bool:
    return any(
        line.lstrip("#").strip() == section
        for line in text.splitlines()
        if line.startswith("#")
    )


def _load_markdown_frontmatter_for_c9(
    repo: Path, path: Path
) -> tuple[dict | None, list[Finding]]:
    if not path.is_file():
        return None, []
    text = read_text(path)
    if not text.startswith("---\n"):
        return None, [Finding("C9", "P0", rel(repo, path), 0, "Markdown 缺少 YAML frontmatter")]
    end = text.find("\n---", 4)
    if end < 0:
        return None, [Finding("C9", "P0", rel(repo, path), 0, "Markdown frontmatter 未闭合")]
    try:
        document = yaml.safe_load(text[4:end])
    except yaml.YAMLError as exc:
        return None, [Finding("C9", "P0", rel(repo, path), 0, f"Markdown frontmatter 无法解析: {exc}")]
    if not isinstance(document, dict):
        return None, [Finding("C9", "P0", rel(repo, path), 0, "Markdown frontmatter 顶层必须是 mapping")]
    return document, []


def check_c9_template_packages(repo: Path, files: list[Path]) -> list[Finding]:
    """C9: template_root 契约声明的包必须满足全部机器约束。"""
    findings: list[Finding] = []
    contracts_root = repo / "contracts"
    contract_files = [p for p in files if contracts_root in p.parents and p.suffix in {".yaml", ".yml"}]
    for contract_path in contract_files:
        contract, parse_findings = _load_yaml(repo, contract_path, "C9")
        findings.extend(parse_findings)
        if parse_findings or not isinstance(contract, dict) or "template_root" not in contract:
            continue
        template_root_value = contract.get("template_root")
        template_root, path_findings = resolve_repo_path(repo, template_root_value, "C9", "template_root")
        findings.extend(path_findings)
        if path_findings or template_root is None:
            continue
        required_files = contract.get("required_files")
        if not isinstance(required_files, list) or not required_files:
            findings.append(Finding("C9", "P0", rel(repo, contract_path), 0, "required_files 必须是非空列表"))
            continue
        for required_file in required_files:
            joined = str(Path(template_root_value) / required_file) if isinstance(required_file, str) else required_file
            target, errors = resolve_repo_path(repo, joined, "C9", f"required_files[{required_file!r}]")
            findings.extend(errors)
            if errors or target is None:
                continue
            if not target.is_file():
                findings.append(Finding("C9", "P0", rel(repo, target), 0, f"模板缺少 required_file: {required_file}"))

        mapping_fields: dict[str, dict] = {}
        for field_name in (
            "required_fields",
            "required_values",
            "required_frontmatter_fields",
            "required_frontmatter_values",
            "required_sections",
        ):
            field_value = contract.get(field_name)
            if field_value is None:
                mapping_fields[field_name] = {}
            elif not isinstance(field_value, dict):
                findings.append(Finding("C9", "P0", rel(repo, contract_path), 0, f"{field_name} 必须是 mapping"))
                mapping_fields[field_name] = {}
            else:
                mapping_fields[field_name] = field_value

        yaml_cache: dict[str, object | None] = {}
        for filename, required_fields in mapping_fields["required_fields"].items():
            joined = str(Path(template_root_value) / filename) if isinstance(filename, str) else filename
            target, errors = resolve_repo_path(repo, joined, "C9", f"required_fields filename {filename!r}")
            findings.extend(errors)
            if errors or target is None:
                continue
            if not isinstance(required_fields, list) or any(not isinstance(field, str) for field in required_fields):
                findings.append(Finding("C9", "P0", rel(repo, contract_path), 0, f"required_fields[{filename}] 必须是 list[str]"))
                continue
            if not target.is_file():
                continue
            content, errors = _load_yaml(repo, target, "C9")
            findings.extend(errors)
            yaml_cache[filename] = content
            if errors:
                continue
            for field in required_fields:
                exists, _ = _dotted_value(content, field)
                if not exists:
                    findings.append(Finding("C9", "P0", rel(repo, target), 0, f"缺少 required_field: {field}"))

        for filename, expected_values in mapping_fields["required_values"].items():
            joined = str(Path(template_root_value) / filename) if isinstance(filename, str) else filename
            target, errors = resolve_repo_path(repo, joined, "C9", f"required_values filename {filename!r}")
            findings.extend(errors)
            if errors or target is None:
                continue
            if not isinstance(expected_values, dict):
                findings.append(Finding("C9", "P0", rel(repo, contract_path), 0, f"required_values[{filename}] 必须是 mapping"))
                continue
            if any(not isinstance(field, str) for field in expected_values):
                findings.append(Finding("C9", "P0", rel(repo, contract_path), 0, f"required_values[{filename}] field keys 必须是 string"))
                continue
            if not target.is_file():
                continue
            content = yaml_cache.get(filename)
            if filename not in yaml_cache:
                content, errors = _load_yaml(repo, target, "C9")
                findings.extend(errors)
            for field, expected in expected_values.items():
                exists, actual = _dotted_value(content, field)
                if not exists or actual != expected:
                    findings.append(Finding("C9", "P0", rel(repo, target), 0, f"required_value 不匹配: {field}"))

        frontmatter_cache: dict[str, dict | None] = {}
        for filename, required_fields in mapping_fields["required_frontmatter_fields"].items():
            joined = str(Path(template_root_value) / filename) if isinstance(filename, str) else filename
            target, errors = resolve_repo_path(repo, joined, "C9", f"required_frontmatter_fields filename {filename!r}")
            findings.extend(errors)
            if errors or target is None:
                continue
            if not isinstance(required_fields, list) or any(not isinstance(field, str) for field in required_fields):
                findings.append(Finding("C9", "P0", rel(repo, contract_path), 0, f"required_frontmatter_fields[{filename}] 必须是 list[str]"))
                continue
            content, errors = _load_markdown_frontmatter_for_c9(repo, target)
            findings.extend(errors)
            frontmatter_cache[filename] = content
            if errors or content is None:
                continue
            for field in required_fields:
                exists, _ = _dotted_value(content, field)
                if not exists:
                    findings.append(Finding("C9", "P0", rel(repo, target), 0, f"缺少 required_frontmatter_field: {field}"))

        for filename, expected_values in mapping_fields["required_frontmatter_values"].items():
            joined = str(Path(template_root_value) / filename) if isinstance(filename, str) else filename
            target, errors = resolve_repo_path(repo, joined, "C9", f"required_frontmatter_values filename {filename!r}")
            findings.extend(errors)
            if errors or target is None:
                continue
            if not isinstance(expected_values, dict):
                findings.append(Finding("C9", "P0", rel(repo, contract_path), 0, f"required_frontmatter_values[{filename}] 必须是 mapping"))
                continue
            if any(not isinstance(field, str) for field in expected_values):
                findings.append(Finding("C9", "P0", rel(repo, contract_path), 0, f"required_frontmatter_values[{filename}] field keys 必须是 string"))
                continue
            content = frontmatter_cache.get(filename)
            if filename not in frontmatter_cache:
                content, errors = _load_markdown_frontmatter_for_c9(repo, target)
                findings.extend(errors)
            if content is None:
                continue
            for field, expected in expected_values.items():
                exists, actual = _dotted_value(content, field)
                if not exists or actual != expected:
                    findings.append(Finding("C9", "P0", rel(repo, target), 0, f"required_frontmatter_value 不匹配: {field}"))

        for filename, sections in mapping_fields["required_sections"].items():
            joined = str(Path(template_root_value) / filename) if isinstance(filename, str) else filename
            target, errors = resolve_repo_path(repo, joined, "C9", f"required_sections filename {filename!r}")
            findings.extend(errors)
            if errors or target is None:
                continue
            if not isinstance(sections, list) or any(not isinstance(section, str) for section in sections):
                findings.append(Finding("C9", "P0", rel(repo, contract_path), 0, f"required_sections[{filename}] 必须是 list[str]"))
                continue
            text = read_text(target)
            if not target.is_file():
                continue
            for section in sections:
                if not _markdown_has_section(text, section):
                    findings.append(Finding("C9", "P1", rel(repo, target), 0, f"缺少 required_section: {section}"))

        task_authority = contract.get("task_authority")
        if "task_authority" in contract and not isinstance(task_authority, dict):
            findings.append(Finding("C9", "P0", rel(repo, contract_path), 0, "task_authority 必须是 mapping"))
        elif isinstance(task_authority, dict):
            for marker_key, allowed_key in (
                ("declaration_marker", "declarations_allowed_only_in"),
                ("reference_marker", "references_allowed_in"),
            ):
                marker = task_authority.get(marker_key)
                allowed = task_authority.get(allowed_key)
                if not isinstance(marker, str) or not isinstance(allowed, str):
                    findings.append(Finding("C9", "P0", rel(repo, contract_path), 0, f"task_authority.{marker_key}/{allowed_key} 无效"))
                    continue
                marker_pattern = re.compile(
                    rf"^\s*(?:#+\s*)?{re.escape(marker)}(?:\s*:.*)?$",
                    re.M,
                )
                occurrences = [
                    p for p in template_root.rglob("*")
                    if p.is_file() and marker_pattern.search(read_text(p))
                ]
                if not occurrences or any(p.relative_to(template_root).as_posix() != allowed for p in occurrences):
                    findings.append(Finding("C9", "P0", rel(repo, template_root), 0, f"task_authority marker '{marker}' 不在唯一允许文件 {allowed}"))
    return findings


TERM_ID_DEFINITION = re.compile(r"^\s*term-id\s*:\s*`([a-z][a-z0-9-]*)`\s*$", re.M)


def check_c10_terminology_authority(repo: Path, files: list[Path]) -> list[Finding]:
    """C10: 术语权威 term-id 与 project-os 机器清单精确一致。"""
    findings: list[Finding] = []
    project_path = repo / "project-os.yaml"
    project, errors = _load_yaml(repo, project_path, "C10")
    if errors:
        return errors
    if not isinstance(project, dict):
        return [Finding("C10", "P0", rel(repo, project_path), 0, "project-os.yaml 顶层必须是映射")]
    authority = project.get("authority")
    terminology_path = authority.get("terminology") if isinstance(authority, dict) else None
    if not isinstance(terminology_path, str):
        return [Finding("C10", "P0", rel(repo, project_path), 0, "authority.terminology 缺失")]
    terminology_file = repo / terminology_path
    if not terminology_file.is_file():
        return [Finding("C10", "P0", terminology_path, 0, "术语权威路径不存在")]
    ids = TERM_ID_DEFINITION.findall(read_text(terminology_file))
    duplicates = sorted({term_id for term_id in ids if ids.count(term_id) > 1})
    if duplicates:
        findings.append(Finding("C10", "P0", terminology_path, 0, "term-id 重复定义: " + ", ".join(duplicates)))
    manifest = project.get("terminology_manifest")
    required_ids = manifest.get("required_term_ids") if isinstance(manifest, dict) else None
    if not isinstance(required_ids, list) or any(not isinstance(item, str) for item in required_ids):
        findings.append(Finding("C10", "P0", rel(repo, project_path), 0, "terminology_manifest.required_term_ids 缺失或无效"))
    elif set(required_ids) != set(ids) or len(required_ids) != len(ids):
        findings.append(Finding("C10", "P0", rel(repo, project_path), 0, "术语清单必须精确覆盖权威 term-id"))
    for path in files:
        if path == terminology_file or path.suffix != ".md":
            continue
        if TERM_ID_DEFINITION.search(read_text(path)):
            findings.append(Finding("C10", "P1", rel(repo, path), 0, "活动文档不得定义 term-id；请引用术语权威"))
    if "selected_profile" in project:
        findings.append(Finding("C10", "P0", rel(repo, project_path), 0, "旧 selected_profile 字段已禁止"))
    profiles = project.get("profiles")
    if isinstance(profiles, dict) and any(
        isinstance(profile, dict) and "enabled" in profile
        for profile in profiles.values()
    ):
        findings.append(Finding("C10", "P0", rel(repo, project_path), 0, "旧 profiles.*.enabled 轴已禁止"))
    return findings


CONTRACT_REFERENCE = re.compile(r"\b([a-z][a-z0-9-]*-contract)@([0-9]+)\b")
MARKDOWN_INLINE_LINK = re.compile(
    r"\[[^\]\n]*\]\(\s*(?:<([^>\n]+)>|([^\s)\n]+))"
    r"(?:\s+(?:\"[^\"]*\"|'[^']*'|\([^)]*\)))?\s*\)"
)
MARKDOWN_REFERENCE_DEFINITION = re.compile(
    r"^\s{0,3}\[[^\]\n]+\]:\s*(?:<([^>\n]+)>|([^\s\n]+))",
    re.M,
)


def _active_markdown_for_c11(repo: Path, path: Path) -> bool:
    parts = path.relative_to(repo).parts
    excluded_prefixes = (
        ("docs", "superpowers", "plans"),
        ("docs", "superpowers", "specs"),
        ("docs", "superpowers", "reviews"),
        ("fixtures", "checker-positive"),
        ("fixtures", "checker-negative"),
    )
    return (
        path.suffix == ".md"
        and ".shopme" not in parts
        and not any(parts[:len(prefix)] == prefix for prefix in excluded_prefixes)
    )


def _markdown_without_fenced_code(text: str) -> tuple[str, bool]:
    visible: list[str] = []
    fence_char: str | None = None
    fence_length = 0
    for line in text.splitlines(keepends=True):
        raw_line = line.rstrip("\r\n")
        if fence_char is None:
            opening = re.match(r"^ {0,3}(`{3,}|~{3,})", raw_line)
            if opening:
                fence = opening.group(1)
                fence_char = fence[0]
                fence_length = len(fence)
                visible.append("\n" if line.endswith(("\n", "\r")) else "")
            else:
                visible.append(line)
        elif re.fullmatch(
            rf" {{0,3}}{re.escape(fence_char)}{{{fence_length},}}[ \t]*",
            raw_line,
        ):
            fence_char = None
            fence_length = 0
            visible.append("\n" if line.endswith("\n") else "")
        else:
            visible.append("\n" if line.endswith("\n") else "")
    return "".join(visible), fence_char is not None


def _markdown_relative_links(text: str) -> list[tuple[int, str]]:
    links: list[tuple[int, str]] = []
    for pattern in (MARKDOWN_INLINE_LINK, MARKDOWN_REFERENCE_DEFINITION):
        for match in pattern.finditer(text):
            target = match.group(1) or match.group(2)
            links.append((text[:match.start()].count("\n") + 1, target.strip()))
    return links


def check_c11_authority_and_contract_references(repo: Path, files: list[Path]) -> list[Finding]:
    """C11: 权威路径和活动契约引用必须存在、唯一并匹配版本。"""
    findings: list[Finding] = []
    project_path = repo / "project-os.yaml"
    project, errors = _load_yaml(repo, project_path, "C11")
    findings.extend(errors)
    authority = project.get("authority") if isinstance(project, dict) else None
    if not isinstance(authority, dict):
        if not errors:
            findings.append(Finding("C11", "P0", rel(repo, project_path), 0, "authority 必须是路径映射"))
        return findings
    authority_paths: dict[str, Path] = {}
    for name, value in authority.items():
        authority_path, path_findings = resolve_repo_path(repo, value, "C11", f"authority.{name}")
        findings.extend(path_findings)
        if path_findings or authority_path is None:
            continue
        authority_paths[name] = authority_path
        if Path(value).parts and Path(value).parts[0] == ".prompts":
            findings.append(Finding("C11", "P0", rel(repo, project_path), 0, f"authority.{name} 不得指向 .prompts"))
        if not authority_path.is_file():
            findings.append(Finding("C11", "P0", rel(repo, project_path), 0, f"authority.{name} 路径不存在: {value}"))

    registry: dict[str, tuple[int, Path]] = {}
    contracts_root = repo / "contracts"
    for path in files:
        if contracts_root not in path.parents or path.suffix not in {".yaml", ".yml"}:
            continue
        contract, parse_errors = _load_yaml(repo, path, "C11")
        findings.extend(parse_errors)
        if parse_errors or not isinstance(contract, dict) or "contract_id" not in contract:
            continue
        contract_id = contract.get("contract_id")
        version = contract.get("version", contract.get("contract_version"))
        if not isinstance(contract_id, str) or type(version) is not int or version <= 0:
            findings.append(Finding("C11", "P0", rel(repo, path), 0, "contract_id 必须稳定且 version 必须是正整数"))
            continue
        if contract_id in registry:
            findings.append(Finding("C11", "P0", rel(repo, path), 0, f"contract_id 重复: {contract_id}"))
        else:
            registry[contract_id] = (version, path)

    for name, value in authority.items():
        path = authority_paths.get(name)
        if not isinstance(value, str) or not value.startswith("contracts/") or path is None or not path.is_file():
            continue
        registered = next(((cid, item) for cid, item in registry.items() if item[1] == path), None)
        if registered is None:
            findings.append(Finding("C11", "P0", rel(repo, path), 0, f"authority.{name} 指向的契约无顶层 contract_id/version"))
            continue
        contract_id, _ = registered
        if path.stem != contract_id:
            findings.append(Finding("C11", "P0", rel(repo, path), 0, f"契约文件名与 contract_id 不匹配: {contract_id}"))

    for path in files:
        relative_parts = path.relative_to(repo).parts
        if path.suffix not in {".yaml", ".yml"} or (relative_parts and relative_parts[0] in {"plans", "specs", "reviews"}):
            continue
        text = read_text(path)
        for line_number, line in enumerate(text.splitlines(), 1):
            if "{{" in line or "}}" in line:
                continue
            for match in CONTRACT_REFERENCE.finditer(line):
                contract_id, version_text = match.groups()
                registered = registry.get(contract_id)
                if registered is None or registered[0] != int(version_text):
                    findings.append(Finding("C11", "P1", rel(repo, path), line_number, f"契约引用无法唯一解析: {match.group(0)}"))
    policies_root = repo / "policies"
    if policies_root.exists():
        for path in policies_root.rglob("*-contract.yaml"):
            findings.append(Finding("C11", "P1", rel(repo, path), 0, "policies/ 不得承载 *-contract.yaml"))

    repo_resolved = repo.resolve()
    ignored_link_prefixes = ("http://", "https://", "mailto:", "#")
    for path in files:
        if not _active_markdown_for_c11(repo, path):
            continue
        markdown, unclosed_fence = _markdown_without_fenced_code(read_text(path))
        if unclosed_fence:
            findings.append(Finding("C11", "P1", rel(repo, path), 0, "Markdown fenced code block 未闭合"))
            continue
        for line_number, target in _markdown_relative_links(markdown):
            if target.lower().startswith(ignored_link_prefixes) or "{{" in target or "}}" in target:
                continue
            target_without_fragment = target.split("#", 1)[0].split("?", 1)[0]
            if not target_without_fragment:
                continue
            resolved = (path.parent / target_without_fragment).resolve()
            try:
                relative_target = resolved.relative_to(repo_resolved).as_posix()
            except ValueError:
                findings.append(Finding("C11", "P1", rel(repo, path), line_number, f"Markdown 相对链接越过仓库边界: {target}"))
                continue
            if not resolved.exists():
                findings.append(Finding("C11", "P1", rel(repo, path), line_number, f"Markdown 相对链接目标不存在: {relative_target}"))
    return findings


def _diagram_frontmatter(repo: Path, path: Path) -> tuple[dict | None, list[Finding]]:
    text = read_text(path)
    if not text.startswith("---\n"):
        return None, []
    end = text.find("\n---", 4)
    if end < 0:
        return None, [Finding("C12", "P1", rel(repo, path), 0, "图文档 frontmatter 未闭合")]
    try:
        data = yaml.safe_load(text[4:end])
    except yaml.YAMLError as exc:
        return None, [Finding("C12", "P1", rel(repo, path), 0, f"图文档 frontmatter 无法解析: {exc}")]
    if isinstance(data, dict) and ("diagram_type" in data or "governs_object" in data):
        if "```mermaid" not in text:
            return data, [Finding("C12", "P1", rel(repo, path), 0, "图文档必须包含 Mermaid 代码块")]
        return data, []
    return None, []


def check_c12_diagram_coverage(repo: Path, files: list[Path]) -> list[Finding]:
    """C12: chain.yaml 的结构字段决定 flowchart/sequence/state/boundary 图。"""
    findings: list[Finding] = []
    chains: dict[str, tuple[Path, dict]] = {}
    for path in files:
        parts = path.relative_to(repo).parts
        if "templates" in parts or path.name != "chain.yaml":
            continue
        data, errors = _load_yaml(repo, path, "C12")
        if errors:
            findings.extend(errors)
            continue
        if isinstance(data, dict) and data.get("object_type") in {"business_chain", "engineering_chain"}:
            required_fields = ("stable_id", "priority", "cross_node", "multi_state", "authorization_or_data_boundary")
            missing = [field for field in required_fields if field not in data]
            if missing:
                findings.append(Finding("C12", "P1", rel(repo, path), 0, "结构化 chain 缺字段: " + ", ".join(missing)))
                continue
            stable_id = data.get("stable_id")
            if not isinstance(stable_id, str):
                findings.append(Finding("C12", "P1", rel(repo, path), 0, "chain stable_id 必须是字符串"))
                continue
            chains[stable_id] = (path, data)

    coverage: dict[str, set[str]] = {stable_id: set() for stable_id in chains}
    allowed_diagram_types = {"flowchart", "sequence", "state", "boundary"}
    for stable_id, (chain_path, _) in chains.items():
        diagram_root = chain_path.parent / "diagrams"
        for path in files:
            if path.suffix != ".md" or diagram_root not in path.parents:
                continue
            diagram, errors = _diagram_frontmatter(repo, path)
            findings.extend(errors)
            if errors:
                continue
            if diagram is None:
                findings.append(Finding("C12", "P1", rel(repo, path), 0, "chain diagram 必须声明 frontmatter"))
                continue
            diagram_type = diagram.get("diagram_type")
            governs = diagram.get("governs_object")
            if not isinstance(diagram_type, str) or not isinstance(governs, str):
                findings.append(Finding("C12", "P1", rel(repo, path), 0, "图文档必须声明 diagram_type 和 governs_object"))
            elif diagram_type not in allowed_diagram_types:
                findings.append(Finding("C12", "P1", rel(repo, path), 0, f"非法 diagram_type: {diagram_type}；允许值为 flowchart/sequence/state/boundary"))
            elif governs != stable_id:
                findings.append(Finding("C12", "P1", rel(repo, path), 0, f"orphan diagram 未治理同目录 chain: {governs}"))
            else:
                coverage[stable_id].add(diagram_type)

    for stable_id, (path, chain) in chains.items():
        required: set[str] = set()
        if chain.get("object_type") in {"business_chain", "engineering_chain"} and str(chain.get("priority")).lower() in {"p0", "p1"}:
            required.add("flowchart")
        if chain.get("cross_node") is True:
            required.add("sequence")
        if chain.get("multi_state") is True:
            required.add("state")
        if chain.get("authorization_or_data_boundary") is True:
            required.add("boundary")
        for diagram_type in sorted(required - coverage[stable_id]):
            findings.append(Finding("C12", "P1", rel(repo, path), 0, f"{stable_id} 缺少必需 {diagram_type} diagram"))
    return findings


REVIEW_POLICY_COMPONENT_FINGERPRINTS = {
    "rule_set_hash",
    "prompt_template_hash",
    "input_schema_hash",
    "output_schema_hash",
    "context_policy_hash",
    "model_fingerprint",
    "tool_set_hash",
    "permission_set_hash",
}
REVIEW_POLICY_CORE_CATEGORIES = {"positive", "negative", "boundary", "adversarial"}
REVIEW_POLICY_ALL_CATEGORIES = REVIEW_POLICY_CORE_CATEGORIES | {
    "unknown",
    "rule_conflict",
    "stale_rule",
    "cross_project",
    "multilingual",
    "rewrite_limit",
    "recovery",
}
REVIEW_POLICY_METRICS = {
    "false_allow_rate",
    "false_block_rate",
    "decision_stability",
    "rule_citation_accuracy",
    "schema_valid_rate",
    "rule_gap_detection_rate",
    "rewrite_success_rate",
    "cross_project_leakage_rate",
}
REVIEW_POLICY_TEMPLATE_FILES = {
    "审核策略包说明.md",
    "审核策略测试集.yaml",
    "审核策略激活策略.yaml",
}


def _c14_non_empty(value: object) -> bool:
    return isinstance(value, str) and bool(value.strip())


def _c14_mapping(value: object) -> dict:
    return value if isinstance(value, dict) else {}


def _c14_list(value: object) -> list:
    return value if isinstance(value, list) else []


def _c14_template_root(repo: Path) -> Path | None:
    candidates = (
        repo / "templates/standard-project/governance/review-certification",
        repo / "governance/review-certification",
    )
    return next((candidate for candidate in candidates if candidate.exists()), None)


def _c14_load_frontmatter(repo: Path, path: Path) -> tuple[dict | None, list[Finding]]:
    text = read_text(path)
    if not text.startswith("---\n"):
        return None, [Finding("C14", "P0", rel(repo, path), 0, "审核策略包说明缺少 YAML frontmatter")]
    end = text.find("\n---", 4)
    if end < 0:
        return None, [Finding("C14", "P0", rel(repo, path), 0, "审核策略包说明 frontmatter 未闭合")]
    try:
        data = yaml.safe_load(text[4:end])
    except yaml.YAMLError as exc:
        return None, [Finding("C14", "P0", rel(repo, path), 0, f"审核策略包说明 YAML 无法解析: {exc}")]
    if not isinstance(data, dict):
        return None, [Finding("C14", "P0", rel(repo, path), 0, "审核策略包说明 frontmatter 必须是 mapping")]
    return data, []


def _c14_repeat_findings(
    repo: Path,
    path: Path,
    suite: dict,
    require_all_categories: bool,
) -> tuple[list[Finding], int]:
    findings: list[Finding] = []
    categories = suite.get("required_categories")
    cases = suite.get("cases")
    minimums = suite.get("minimum_repeat_policy")
    if not isinstance(categories, list) or any(not isinstance(item, str) for item in categories):
        findings.append(Finding("C14", "P0", rel(repo, path), 0, "预注册测试类别必须是 list[str]"))
        categories_set: set[str] = set()
    else:
        categories_set = set(categories)
    required = REVIEW_POLICY_ALL_CATEGORIES if require_all_categories else REVIEW_POLICY_CORE_CATEGORIES
    if not required <= categories_set:
        findings.append(Finding("C14", "P0", rel(repo, path), 0, "预注册测试类别缺少必需正例、反例、边界、对抗或适用扩展类别"))
    if not isinstance(cases, list) or not cases:
        findings.append(Finding("C14", "P0", rel(repo, path), 0, "预注册测试 cases 必须是非空列表"))
        return findings, 0
    case_categories = {
        case.get("category") for case in cases if isinstance(case, dict) and isinstance(case.get("category"), str)
    }
    if case_categories != categories_set:
        findings.append(Finding("C14", "P0", rel(repo, path), 0, "required_categories 与实际 case 类别不一致"))
    if not isinstance(minimums, dict):
        findings.append(Finding("C14", "P0", rel(repo, path), 0, "minimum_repeat_policy 必须是 mapping"))
        minimums = {}
    total_attempts = 0
    for index, case in enumerate(cases):
        if not isinstance(case, dict):
            findings.append(Finding("C14", "P0", rel(repo, path), 0, f"case[{index}] 必须是 mapping"))
            continue
        deterministic = case.get("deterministic")
        repeat_count = case.get("repeat_count")
        risk_level = case.get("risk_level")
        if type(deterministic) is not bool:
            findings.append(Finding("C14", "P0", rel(repo, path), 0, f"case[{index}] deterministic 必须是 boolean"))
        base_key = "deterministic" if deterministic is True else "nondeterministic"
        base_minimum = minimums.get(base_key)
        high_minimum = minimums.get("high_or_critical_risk")
        if type(repeat_count) is not int or repeat_count <= 0:
            findings.append(Finding("C14", "P0", rel(repo, path), 0, f"case[{index}] 重复次数必须是正整数"))
            continue
        total_attempts += repeat_count
        required_repeat = base_minimum if type(base_minimum) is int else None
        if risk_level in {"high", "critical"} and type(high_minimum) is int:
            required_repeat = max(required_repeat or 0, high_minimum)
        if required_repeat is None or repeat_count < required_repeat:
            findings.append(Finding("C14", "P0", rel(repo, path), 0, f"case[{index}] 重复次数低于预注册最小值"))
    return findings, total_attempts


def _c14_template_findings(repo: Path) -> list[Finding]:
    root = _c14_template_root(repo)
    if root is None:
        return []
    findings: list[Finding] = []
    existing = {path.name for path in root.iterdir() if path.is_file()}
    missing = REVIEW_POLICY_TEMPLATE_FILES - existing
    for filename in sorted(missing):
        findings.append(Finding("C14", "P0", rel(repo, root / filename), 0, "审核策略认证模板缺少必需文件"))
    if missing:
        return findings

    bundle_path = root / "审核策略包说明.md"
    bundle, errors = _c14_load_frontmatter(repo, bundle_path)
    findings.extend(errors)
    if isinstance(bundle, dict):
        component_refs = bundle.get("component_refs")
        fingerprints = bundle.get("component_fingerprints")
        if not isinstance(component_refs, dict) or set(component_refs) != {
            "rule_set_ref",
            "prompt_template_ref",
            "input_schema_ref",
            "output_schema_ref",
            "context_policy_ref",
            "model_ref",
            "tool_set_ref",
            "permission_set_ref",
        }:
            findings.append(Finding("C14", "P0", rel(repo, bundle_path), 0, "审核策略包必须精确引用全部组件"))
        if not isinstance(fingerprints, dict) or set(fingerprints) != REVIEW_POLICY_COMPONENT_FINGERPRINTS:
            findings.append(Finding("C14", "P0", rel(repo, bundle_path), 0, "审核策略包必须精确覆盖规则、Prompt、I/O Schema、Context、模型、Tool 与权限指纹"))
        elif any(not _c14_non_empty(value) for value in fingerprints.values()):
            findings.append(Finding("C14", "P0", rel(repo, bundle_path), 0, "审核策略包组件指纹不得为空"))
        if bundle.get("bundle_state") != "candidate":
            findings.append(Finding("C14", "P0", rel(repo, bundle_path), 0, "复制模板不得伪装为已认证策略包"))

    suite_path = root / "审核策略测试集.yaml"
    suite, errors = _load_yaml(repo, suite_path, "C14")
    findings.extend(errors)
    if isinstance(suite, dict):
        repeat_findings, _ = _c14_repeat_findings(repo, suite_path, suite, True)
        findings.extend(repeat_findings)
        case_fields = {
            "case_id",
            "category",
            "input_ref",
            "input_hash",
            "expected_decision",
            "expected_rule_refs",
            "forbidden_decisions",
            "required_finding_codes",
            "required_evidence",
            "risk_level",
            "deterministic",
            "repeat_count",
        }
        for index, case in enumerate(_c14_list(suite.get("cases"))):
            if not isinstance(case, dict) or not case_fields <= set(case):
                findings.append(Finding("C14", "P0", rel(repo, suite_path), 0, f"case[{index}] 缺少预注册输入、预期、规则、Evidence、风险或重复字段"))
        if set(_c14_list(suite.get("metrics"))) != REVIEW_POLICY_METRICS:
            findings.append(Finding("C14", "P0", rel(repo, suite_path), 0, "测试集 metrics 必须完整覆盖认证指标"))
        thresholds = suite.get("thresholds")
        if not isinstance(thresholds, dict) or any(
            not any(key.startswith(metric) for key in thresholds)
            for metric in REVIEW_POLICY_METRICS
        ):
            findings.append(Finding("C14", "P0", rel(repo, suite_path), 0, "每个认证指标必须有预注册阈值"))

    activation_path = root / "审核策略激活策略.yaml"
    activation, errors = _load_yaml(repo, activation_path, "C14")
    findings.extend(errors)
    if isinstance(activation, dict):
        if activation.get("extends") != "review-policy-activation-routing@1":
            findings.append(Finding("C14", "P0", rel(repo, activation_path), 0, "L2 激活策略必须扩展 L1 权威政策"))
        if set(_c14_list(activation.get("allowed_routes"))) != {"policy_certified", "human_signoff", "blocked"}:
            findings.append(Finding("C14", "P0", rel(repo, activation_path), 0, "激活策略路由必须完整且 fail closed"))
        if activation.get("external_action_authorization") != "always_independent":
            findings.append(Finding("C14", "P0", rel(repo, activation_path), 0, "审核策略认证不能替代外部动作授权"))
        if activation.get("route_precedence") != ["blocked", "human_signoff", "policy_certified"]:
            findings.append(Finding("C14", "P0", rel(repo, activation_path), 0, "激活策略必须保持 blocked 最高优先级"))
        for field in ("policy_certified_constraints", "human_signoff_triggers", "blocked_triggers"):
            if not activation.get(field):
                findings.append(Finding("C14", "P0", rel(repo, activation_path), 0, f"激活策略缺少非空 {field}"))
    return findings


def _c14_scenario_findings(repo: Path, path: Path, scenario: dict) -> list[Finding]:
    findings: list[Finding] = []
    bundle = _c14_mapping(scenario.get("bundle"))
    suite = _c14_mapping(scenario.get("test_suite"))
    certification = _c14_mapping(scenario.get("certification"))
    activation = _c14_mapping(scenario.get("activation"))

    fingerprints = bundle.get("component_fingerprints")
    if not isinstance(fingerprints, dict) or set(fingerprints) != REVIEW_POLICY_COMPONENT_FINGERPRINTS:
        findings.append(Finding("C14", "P0", rel(repo, path), 0, "策略包指纹不完整"))
    elif any(not _c14_non_empty(value) for value in fingerprints.values()):
        findings.append(Finding("C14", "P0", rel(repo, path), 0, "策略包指纹不得为空"))

    repeat_findings, total_attempts = _c14_repeat_findings(repo, path, suite, False)
    findings.extend(repeat_findings)
    excluded = certification.get("excluded_attempts_and_reasons")
    included_count = certification.get("included_attempt_count")
    exclusions_valid = isinstance(excluded, list) and all(
        isinstance(item, dict)
        and _c14_non_empty(item.get("attempt_ref"))
        and _c14_non_empty(item.get("reason"))
        for item in excluded
    )
    if (
        type(included_count) is not int
        or not exclusions_valid
        or included_count + len(excluded) != total_attempts
    ):
        findings.append(Finding("C14", "P0", rel(repo, path), 0, "认证未覆盖全部重复尝试或排除项缺少理由"))

    binding_pairs = (
        (bundle.get("bundle_ref"), certification.get("subject_bundle_ref")),
        (bundle.get("bundle_hash"), certification.get("subject_bundle_hash")),
        (suite.get("test_suite_ref"), certification.get("test_suite_ref")),
        (suite.get("test_suite_hash"), certification.get("test_suite_hash")),
    )
    if any(not _c14_non_empty(left) or left != right for left, right in binding_pairs):
        findings.append(Finding("C14", "P0", rel(repo, path), 0, "认证 subject/test suite 引用或 hash 与当前策略包不匹配"))

    generator_ref = bundle.get("generator_ref")
    verifier_ref = certification.get("verifier_ref")
    reviewer_refs = _c14_list(certification.get("reviewer_refs"))
    if (
        not _c14_non_empty(verifier_ref)
        or verifier_ref == generator_ref
        or verifier_ref in reviewer_refs
        or not _c14_non_empty(certification.get("verifier_independence_evidence_ref"))
    ):
        findings.append(Finding("C14", "P0", rel(repo, path), 0, "认证 verifier 必须独立于策略生成者和 review Run"))

    run_refs = certification.get("run_refs")
    evidence_refs = certification.get("evidence_refs")
    if not isinstance(run_refs, list) or not run_refs or not isinstance(evidence_refs, list) or not evidence_refs:
        findings.append(Finding("C14", "P0", rel(repo, path), 0, "认证必须绑定非空 Run 与 Evidence"))

    threshold_results = certification.get("threshold_results")
    thresholds_pass = (
        isinstance(threshold_results, dict)
        and set(threshold_results) == REVIEW_POLICY_METRICS
        and all(result == "passed" for result in threshold_results.values())
    )
    active = activation.get("active") is True
    decision = certification.get("certification_decision")
    if active and (not thresholds_pass or decision not in {"certified", "certified_with_ceiling"}):
        findings.append(Finding("C14", "P0", rel(repo, path), 0, "存在未通过阈值或无效认证结论时不得激活"))
    if active and (
        certification.get("certification_freshness") != "fresh"
        or certification.get("scope_match") is not True
    ):
        findings.append(Finding("C14", "P0", rel(repo, path), 0, "过期或 scope 不匹配的认证不得激活"))

    route = activation.get("requested_route")
    eligible_routes = _c14_list(certification.get("eligible_activation_routes"))
    inputs = _c14_mapping(activation.get("decision_inputs"))
    if active and route not in eligible_routes:
        findings.append(Finding("C14", "P0", rel(repo, path), 0, "激活路由不在认证允许范围内"))
    if inputs.get("unresolved_unknown") is not False:
        findings.append(Finding("C14", "P0", rel(repo, path), 0, "未决 Unknown 必须阻断激活路由"))
    policy_safe = (
        inputs.get("scope_change") in {"none", "reduced"}
        and inputs.get("threshold_change") in {"unchanged", "stricter"}
        and inputs.get("blocking_rule_change") in {"unchanged", "stronger"}
        and inputs.get("permission_change") in {"none", "reduced"}
        and inputs.get("objective_or_responsibility_change") is False
        and inputs.get("residual_risk_acceptance") is False
        and inputs.get("external_side_effect") in {"none", "read_external", "write_reversible"}
    )
    human_trigger = (
        inputs.get("scope_change") == "expanded"
        or inputs.get("threshold_change") == "reduced"
        or inputs.get("blocking_rule_change") == "removed"
        or inputs.get("permission_change") == "increased"
        or inputs.get("objective_or_responsibility_change") is True
        or inputs.get("residual_risk_acceptance") is True
        or inputs.get("external_side_effect") == "write_irreversible"
    )
    if route == "policy_certified" and not policy_safe:
        findings.append(Finding("C14", "P0", rel(repo, path), 0, "高风险变化与 policy_certified 激活路由不匹配"))
    elif route == "human_signoff":
        human_ref = activation.get("human_signoff_ref")
        if not human_trigger or not isinstance(human_ref, str) or not human_ref.startswith("human-"):
            findings.append(Finding("C14", "P0", rel(repo, path), 0, "human_signoff 路由必须有高风险触发和可验证人类引用"))
    elif route == "blocked":
        if active:
            findings.append(Finding("C14", "P0", rel(repo, path), 0, "blocked 路由不得处于 active"))
    elif route != "policy_certified":
        findings.append(Finding("C14", "P0", rel(repo, path), 0, "未知激活路由必须 fail closed"))

    if activation.get("external_action_authorization_granted") is not False:
        findings.append(Finding("C14", "P0", rel(repo, path), 0, "审核策略认证不能签发或替代外部动作授权"))

    recovery = scenario.get("recovery")
    if recovery is not None:
        recovery_fields = {
            "previous_rule_gap_ref",
            "superseded_bundle_ref",
            "new_rule_set_ref",
            "new_certification_ref",
            "reopened_subject_refs",
            "new_review_run_refs",
        }
        if not isinstance(recovery, dict) or not recovery_fields <= set(recovery):
            findings.append(Finding("C14", "P0", rel(repo, path), 0, "Rule Gap 恢复必须绑定新规则、新认证、新 Run 与重开对象"))
    return findings


def check_c14_review_policy_certification(repo: Path, files: list[Path]) -> list[Finding]:
    """C14: 审核策略模板与 synthetic certification fixture 必须静态闭合。"""
    findings = _c14_template_findings(repo)
    catalog = repo / "fixtures/review-policy-certification"
    if catalog.is_dir():
        scenario_paths = sorted((catalog / "positive").glob("*/scenario.yaml"))
    else:
        scenario_paths = sorted(
            path for path in files if path.name == "scenario.yaml" and path.suffix in {".yaml", ".yml"}
        )
    for path in scenario_paths:
        scenario, errors = _load_yaml(repo, path, "C14")
        findings.extend(errors)
        if errors:
            continue
        if not isinstance(scenario, dict) or scenario.get("fixture_kind") != "review_policy_certification_scenario":
            findings.append(Finding("C14", "P0", rel(repo, path), 0, "认证 fixture 必须声明 review_policy_certification_scenario"))
            continue
        findings.extend(_c14_scenario_findings(repo, path, scenario))
    return findings


def check_l2_mode(repo: Path) -> list[Finding]:
    """L2 模式：额外检查 project-os.lock 是否存在。"""
    findings: list[Finding] = []
    lock_candidates = [
        repo / "project-os.lock",
        repo / "project-os.lock.yaml",
        repo / "project-os.lock.yml",
    ]
    if not any(p.exists() for p in lock_candidates):
        findings.append(Finding(
            "L2-LOCK", "P0", ".",  0,
            "L2 项目缺少 project-os.lock（或 .yaml/.yml），无法验证 L1 版本锁定",
        ))
    return findings


def exit_code_for_findings(findings: list[Finding]) -> int:
    """P0/P1 都是声明的门禁失败；INFO 只用于观测。"""
    return 1 if any(f.severity in {"P0", "P1"} for f in findings) else 0


# ── 主流程 ────────────────────────────────────────────────────────────────────

def main() -> int:
    args = sys.argv[1:]
    repo_arg = args[0] if args else "."
    verbose = "--report" in args
    l2_mode = "--l2-mode" in args

    repo = Path(repo_arg).resolve()
    if not repo.exists():
        print(f"[ERROR] 路径不存在: {repo}", file=sys.stderr)
        return 2

    files = iter_repo_files(repo, skip_run_artifacts=True)

    all_findings: list[Finding] = []
    all_findings += check_c1_stable_id_unique(repo, files)
    all_findings += check_c2_source_no_bypass(repo, files)
    all_findings += check_c3_p0p1_has_spec_traceability(repo, files)
    # C4 只对 L1 仓库检查单向依赖；L2 项目文件引用 L3 路径是合法的
    if not l2_mode:
        all_findings += check_c4_l1_no_l2_refs(repo, files)
    all_findings += check_c5_proof_level_single_authority(repo, files)
    all_findings += check_c6_ai_review_no_routine_human_wait(repo, files)
    all_findings += check_c7_ai_review_manifest(repo, files)
    # C8-C11 校验 L1 自身的契约、模板注册和机器权威；L2 只消费锁定后的协议，
    # 不复制 project-os.yaml、L1 contracts 或 L1 术语清单。
    if not l2_mode:
        all_findings += check_c8_stage_gate_contract(repo, files)
        all_findings += check_c9_template_packages(repo, files)
        all_findings += check_c10_terminology_authority(repo, files)
        all_findings += check_c11_authority_and_contract_references(repo, files)
    all_findings += check_c12_diagram_coverage(repo, files)
    all_findings += check_c14_review_policy_certification(repo, files)
    if l2_mode:
        all_findings += check_l2_mode(repo)

    # 排序：P0 优先
    sev_order = {"P0": 0, "P1": 1, "INFO": 2}
    all_findings.sort(key=lambda f: (sev_order.get(f.severity, 9), f.rule, f.file))

    p0 = [f for f in all_findings if f.severity == "P0"]
    p1 = [f for f in all_findings if f.severity == "P1"]

    # ── 输出 ──
    print("=" * 70)
    print("ai-project-os 追溯检查报告")
    print(f"扫描路径: {repo}")
    print(f"文件数:   {len(files)}")
    print("=" * 70)

    if verbose or all_findings:
        for f in all_findings:
            print(f"[{f.severity}] {f.rule}  {f.file}:{f.line}")
            print(f"      {f.message}")

    print("-" * 70)
    print(f"P0={len(p0)}  P1={len(p1)}  总计={len(all_findings)}")

    if not all_findings:
        print("✅ 无发现，检查通过")
    elif not p0:
        print("❌ 有 P1 发现（门禁失败）")
    else:
        print("❌ 有 P0 发现（必须修复）")
    print("=" * 70)

    # 输出机器可读 JSON（供保存为 Evidence）
    report = {
        "checker": "check_controlled_objects",
        "version": "0.5.0",
        "repo": str(repo),
        "files_scanned": len(files),
        "p0_count": len(p0),
        "p1_count": len(p1),
        "pass": not p0 and not p1,
        "findings": [f.as_dict() for f in all_findings],
    }
    print("\n# JSON Evidence (保存此段到 reviews/phase0-checker-evidence.yaml)")
    print(json.dumps(report, ensure_ascii=False, indent=2))

    return exit_code_for_findings(all_findings)


if __name__ == "__main__":
    sys.exit(main())
