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
import itertools
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


def _markdown_table_cell(value: str) -> str:
    value = value.strip()
    if len(value) >= 2 and value.startswith("`") and value.endswith("`"):
        return value[1:-1].strip()
    return value


def _parse_markdown_table(
    text: str,
    section: str,
) -> tuple[list[str], list[dict[str, str]], str | None]:
    """解析指定 Markdown section 中的首个标准 pipe table。"""
    lines = text.splitlines()
    section_indexes: list[int] = []
    heading = re.compile(rf"^#+\s+{re.escape(section)}\s*$")
    for index, line in enumerate(lines):
        if heading.match(line):
            section_indexes.append(index)
    if not section_indexes:
        return [], [], "missing section"
    if len(section_indexes) > 1:
        return [], [], "duplicate section"
    section_index = section_indexes[0]

    table_index = None
    for index in range(section_index + 1, len(lines)):
        line = lines[index]
        if line.startswith("#"):
            break
        if line.strip().startswith("|"):
            table_index = index
            break
    if table_index is None or table_index + 1 >= len(lines):
        return [], [], "missing table"

    def cells(line: str) -> list[str]:
        return [
            _markdown_table_cell(cell)
            for cell in line.strip().strip("|").split("|")
        ]

    columns = cells(lines[table_index])
    separator = cells(lines[table_index + 1])
    if len(separator) != len(columns) or any(
        not re.fullmatch(r":?-{3,}:?", cell) for cell in separator
    ):
        return columns, [], "invalid table separator"

    rows: list[dict[str, str]] = []
    for line in lines[table_index + 2 :]:
        if not line.strip().startswith("|"):
            break
        values = cells(line)
        if len(values) != len(columns):
            return columns, rows, "row width does not match columns"
        rows.append(dict(zip(columns, values)))
    return columns, rows, None


def _contains_placeholder(value: object) -> bool:
    if isinstance(value, str):
        return "{{" in value and "}}" in value
    if isinstance(value, dict):
        return any(_contains_placeholder(key) or _contains_placeholder(item) for key, item in value.items())
    if isinstance(value, list):
        return any(_contains_placeholder(item) for item in value)
    return False


def _profile_chain(contract: dict, validation_profile: str) -> tuple[list[str], list[str]]:
    profiles = contract.get("validation_profiles")
    if not isinstance(profiles, dict):
        return [], ["validation_profiles must be a mapping"]
    chain: list[str] = []
    visited: set[str] = set()
    current: object = validation_profile
    while isinstance(current, str):
        if current in visited:
            return chain, [f"profile_inheritance_cycle: {current}"]
        visited.add(current)
        profile = profiles.get(current)
        if not isinstance(profile, dict):
            return chain, [f"unknown_profile: {current}"]
        chain.append(current)
        current = profile.get("inherits")
        if current is not None and not isinstance(current, str):
            return chain, [f"invalid_profile_inheritance: {chain[-1]}"]
    return chain, []


def _package_path(package_root: Path, raw: object) -> Path | None:
    if not isinstance(raw, str) or not raw:
        return None
    relative = Path(raw)
    if relative.is_absolute() or ".." in relative.parts:
        return None
    resolved = (package_root / relative).resolve()
    try:
        resolved.relative_to(package_root.resolve())
    except ValueError:
        return None
    return resolved


def _load_package_yaml(path: Path) -> tuple[object | None, str | None]:
    try:
        return yaml.safe_load(path.read_text(encoding="utf-8")), None
    except (OSError, yaml.YAMLError) as exc:
        return None, f"YAML cannot be parsed: {path.name}: {exc}"


def _parse_fenced_yaml(text: str, section: str) -> tuple[object | None, str | None]:
    lines = text.splitlines()
    indexes = [
        index
        for index, line in enumerate(lines)
        if re.fullmatch(rf"#+\s+{re.escape(section)}\s*", line)
    ]
    if not indexes:
        return None, f"embedded_yaml missing section: {section}"
    if len(indexes) > 1:
        return None, f"embedded_yaml duplicate section: {section}"
    start = indexes[0] + 1
    end = len(lines)
    for index in range(start, len(lines)):
        if lines[index].startswith("#"):
            end = index
            break
    block = "\n".join(lines[start:end])
    match = re.search(r"```ya?ml\s*\n(.*?)\n```", block, re.S)
    if not match:
        return None, f"embedded_yaml missing yaml fence: {section}"
    try:
        return yaml.safe_load(match.group(1)), None
    except yaml.YAMLError as exc:
        return None, f"embedded_yaml invalid YAML: {section}: {exc}"


def _parse_contract_tables(
    contract: dict,
    package_root: Path,
    required_table_names: set[str] | None = None,
) -> tuple[dict[str, tuple[list[str], list[dict[str, str]]]], list[str]]:
    errors: list[str] = []
    parsed: dict[str, tuple[list[str], list[dict[str, str]]]] = {}
    table_specs = contract.get("markdown_tables", {})
    if not isinstance(table_specs, dict):
        return parsed, ["markdown_tables must be a mapping"]
    known_tables = {
        section
        for section_specs in table_specs.values()
        if isinstance(section_specs, dict)
        for section in section_specs
        if isinstance(section, str)
    }
    if required_table_names is not None:
        for missing in sorted(required_table_names - known_tables):
            errors.append(f"required table is not declared: {missing}")
    for filename, section_specs in table_specs.items():
        if not isinstance(filename, str) or not isinstance(section_specs, dict):
            errors.append("markdown_tables file rule must be a mapping")
            continue
        path = _package_path(package_root, filename)
        if path is None or not path.is_file():
            errors.append(f"missing table file: {filename}")
            continue
        text = read_text(path)
        for section, rule in section_specs.items():
            if required_table_names is not None and section not in required_table_names:
                continue
            if not isinstance(rule, dict):
                errors.append(f"invalid table rule: {section}")
                continue
            columns, rows, parse_error = _parse_markdown_table(text, section)
            if parse_error:
                errors.append(f"Markdown table {section}: {parse_error}")
                continue
            expected = rule.get("columns")
            if columns != expected:
                errors.append(f"Markdown table {section} columns mismatch")
                continue
            minimum_rows = rule.get("minimum_rows", 0)
            if isinstance(minimum_rows, bool) or not isinstance(minimum_rows, int):
                errors.append(f"Markdown table {section} minimum_rows invalid")
            elif len(rows) < minimum_rows:
                errors.append(f"Markdown table {section} has fewer than minimum_rows")
            primary_key = rule.get("primary_key")
            if not isinstance(primary_key, str) or primary_key not in columns:
                errors.append(f"Markdown table {section} primary_key invalid")
            else:
                keys = [row.get(primary_key, "") for row in rows]
                if any(not key for key in keys):
                    errors.append(f"Markdown table {section} primary key is empty")
                if len(keys) != len(set(keys)):
                    errors.append(f"Markdown table {section} duplicate primary key")
            allowed_enums = rule.get("allowed_enums", {})
            if not isinstance(allowed_enums, dict):
                errors.append(f"Markdown table {section} allowed_enums invalid")
            else:
                for field, allowed in allowed_enums.items():
                    if field not in columns or not isinstance(allowed, list):
                        errors.append(f"Markdown table {section} allowed enum {field} invalid")
                        continue
                    for row in rows:
                        value = row.get(field, "")
                        if not _contains_placeholder(value) and value not in allowed:
                            errors.append(f"Markdown table {section} field {field} violates allowed enum")
            parsed[section] = (columns, rows)
    return parsed, errors


def _is_forbidden_assignment(
    assignment: dict[str, object],
    forbidden_assignments: list[dict[str, object]],
) -> bool:
    return any(
        all(assignment.get(dimension) == value for dimension, value in forbidden.items())
        for forbidden in forbidden_assignments
    )


def validate_strength_two_coverage(
    dimensions: dict[str, list[object]],
    rows: list[dict[str, object]],
    forbidden_assignments: list[dict[str, object]] | None = None,
    max_cartesian_size: int = 100_000,
) -> list[str]:
    """重算受约束 strength-2 覆盖；维度和值完全由调用方 inventory 提供。"""
    errors: list[str] = []
    forbidden = forbidden_assignments or []
    if not isinstance(dimensions, dict) or len(dimensions) < 2:
        return ["strength_two requires at least two dimensions"]
    if not isinstance(rows, list) or not isinstance(forbidden, list):
        return ["strength_two rows and forbidden_assignments must be lists"]
    for name, values in dimensions.items():
        if not isinstance(name, str) or not name or not isinstance(values, list) or not values:
            errors.append(f"invalid dimension domain: {name!r}")
            continue
        serialized = [json.dumps(value, ensure_ascii=False, sort_keys=True) for value in values]
        if len(serialized) != len(set(serialized)):
            errors.append(f"duplicate dimension member: {name}")
    if errors:
        return errors
    if any(not isinstance(item, dict) or not item for item in forbidden):
        return ["forbidden assignment must be a non-empty mapping"]
    for forbidden_index, forbidden_item in enumerate(forbidden):
        for name, value in forbidden_item.items():
            if name not in dimensions:
                errors.append(
                    f"forbidden assignment {forbidden_index} references unknown dimension: {name}"
                )
            elif value not in dimensions[name]:
                errors.append(
                    f"forbidden assignment {forbidden_index} contains out-of-domain value: {name}"
                )
    if errors:
        return errors
    names = list(dimensions)
    cartesian_size = 1
    for values in dimensions.values():
        cartesian_size *= len(values)
    if cartesian_size > max_cartesian_size:
        return [f"cartesian space {cartesian_size} exceeds declared validation budget {max_cartesian_size}"]

    allowed_full_rows = [
        dict(zip(names, values))
        for values in itertools.product(*(dimensions[name] for name in names))
        if not _is_forbidden_assignment(dict(zip(names, values)), forbidden)
    ]
    if not allowed_full_rows:
        return ["constraints remove every assignment from the test space"]
    valid_rows: list[dict[str, object]] = []
    serialized_rows: set[str] = set()
    for index, row in enumerate(rows):
        if not isinstance(row, dict) or set(row) != set(names):
            errors.append(f"covering row {index} dimensions mismatch")
            continue
        if any(row[name] not in dimensions[name] for name in names):
            errors.append(f"covering row {index} contains out-of-domain value")
            continue
        if _is_forbidden_assignment(row, forbidden):
            errors.append(f"covering row {index} violates forbidden assignment")
            continue
        serialized = json.dumps(row, ensure_ascii=False, sort_keys=True)
        if serialized in serialized_rows:
            errors.append(f"duplicate covering assignment at row {index}")
            continue
        serialized_rows.add(serialized)
        valid_rows.append(row)

    for left_index, left in enumerate(names):
        for right in names[left_index + 1 :]:
            expected = {
                (
                    json.dumps(row[left], ensure_ascii=False, sort_keys=True),
                    json.dumps(row[right], ensure_ascii=False, sort_keys=True),
                )
                for row in allowed_full_rows
            }
            observed = {
                (
                    json.dumps(row[left], ensure_ascii=False, sort_keys=True),
                    json.dumps(row[right], ensure_ascii=False, sort_keys=True),
                )
                for row in valid_rows
            }
            for pair in sorted(expected - observed):
                errors.append(f"missing allowed pair: {left}={pair[0]}, {right}={pair[1]}")
    return errors


def _validate_package_shape(shape: dict, package_root: Path) -> list[str]:
    errors: list[str] = []
    required_files = shape.get("required_files")
    if not isinstance(required_files, list) or not required_files:
        return ["package shape required_files must be a non-empty list"]
    for filename in required_files:
        path = _package_path(package_root, filename)
        if path is None or not path.is_file():
            errors.append(f"missing required file: {filename}")
    yaml_cache: dict[str, object] = {}
    required_fields = shape.get("required_fields", {})
    if not isinstance(required_fields, dict):
        errors.append("package shape required_fields must be a mapping")
        required_fields = {}
    for filename, fields in required_fields.items():
        path = _package_path(package_root, filename)
        if path is None or not path.is_file() or not isinstance(fields, list):
            errors.append(f"invalid required_fields declaration: {filename}")
            continue
        document, parse_error = _load_package_yaml(path)
        if parse_error:
            errors.append(parse_error)
            continue
        yaml_cache[filename] = document
        for field in fields:
            exists, _ = _dotted_value(document, field) if isinstance(field, str) else (False, None)
            if not exists:
                errors.append(f"missing required field: {filename}#{field}")
    required_values = shape.get("required_values", {})
    if not isinstance(required_values, dict):
        errors.append("package shape required_values must be a mapping")
        required_values = {}
    for filename, expected_values in required_values.items():
        path = _package_path(package_root, filename)
        if path is None or not path.is_file() or not isinstance(expected_values, dict):
            errors.append(f"invalid required_values declaration: {filename}")
            continue
        document = yaml_cache.get(filename)
        if document is None:
            document, parse_error = _load_package_yaml(path)
            if parse_error:
                errors.append(parse_error)
                continue
        for field, expected in expected_values.items():
            exists, actual = _dotted_value(document, field)
            if not exists or actual != expected:
                errors.append(f"required value mismatch: {filename}#{field}")
    required_sections = shape.get("required_sections", {})
    if not isinstance(required_sections, dict):
        errors.append("package shape required_sections must be a mapping")
        required_sections = {}
    for filename, sections in required_sections.items():
        path = _package_path(package_root, filename)
        if path is None or not path.is_file() or not isinstance(sections, list):
            errors.append(f"invalid required_sections declaration: {filename}")
            continue
        text = read_text(path)
        for section in sections:
            if not isinstance(section, str) or not _markdown_has_section(text, section):
                errors.append(f"missing required section: {filename}#{section}")
    return errors


def _validate_embedded_yaml(contract: dict, package_root: Path) -> tuple[dict[str, object], list[str]]:
    documents: dict[str, object] = {}
    errors: list[str] = []
    rules = contract.get("embedded_yaml", {})
    if not isinstance(rules, dict):
        return documents, ["embedded_yaml must be a mapping"]
    for filename, rule in rules.items():
        path = _package_path(package_root, filename)
        if path is None or not path.is_file() or not isinstance(rule, dict):
            errors.append(f"invalid embedded_yaml rule: {filename}")
            continue
        section = rule.get("section")
        if not isinstance(section, str):
            errors.append(f"embedded_yaml section invalid: {filename}")
            continue
        document, parse_error = _parse_fenced_yaml(read_text(path), section)
        if parse_error:
            errors.append(f"{filename}: {parse_error}")
            continue
        documents[filename] = document
        for field in rule.get("required_fields", []):
            exists, value = _dotted_value(document, field) if isinstance(field, str) else (False, None)
            if not exists or value in (None, [], ""):
                errors.append(f"{filename} missing embedded field: {field}")
        list_field = rule.get("list_field")
        if list_field is not None:
            exists, items = _dotted_value(document, list_field) if isinstance(list_field, str) else (False, None)
            if not exists or not isinstance(items, list) or not items:
                errors.append(f"{filename} missing embedded list: {list_field}")
                continue
            required = rule.get("item_required_fields", [])
            for index, item in enumerate(items):
                if not isinstance(item, dict):
                    errors.append(f"{filename} {list_field}[{index}] must be a mapping")
                    continue
                for field in required:
                    exists, value = _dotted_value(item, field) if isinstance(field, str) else (False, None)
                    if not exists or value in (None, [], ""):
                        errors.append(f"{filename} {list_field}[{index}] missing field: {field}")
    return documents, errors


def _reference_key(value: object) -> str | None:
    if not isinstance(value, str) or not value or _contains_placeholder(value) or value == "*":
        return None
    if value.endswith(":*"):
        return None
    return value.rsplit(":", 1)[-1] if "#" in value and ":" in value else value


def _validate_chain_profile_tables(
    tables: dict[str, tuple[list[str], list[dict[str, str]]]],
) -> list[str]:
    errors: list[str] = []
    behavior_specs = {row["behavior_spec_id"] for row in tables.get("Behavior Specification", ([], []))[1]}
    behavior_rows = tables.get("Behavior Case Registry", ([], []))[1]
    behavior_cases = {row["case_id"]: row for row in behavior_rows}
    test_spaces = {row["test_space_id"]: row for row in tables.get("Test Space Model", ([], []))[1]}
    coverage_rows = tables.get("Acceptance Coverage Matrix", ([], []))[1]
    coverage = {row["coverage_id"]: row for row in coverage_rows}
    combination_rows = tables.get("Derived Combination Registry", ([], []))[1]
    oracle_rows = tables.get("Failure Recovery Oracle", ([], []))[1]

    for test_space_id, row in test_spaces.items():
        ref = _reference_key(row.get("behavior_spec_ref"))
        if ref is not None and ref not in behavior_specs:
            errors.append(f"unresolved Behavior Specification reference: {ref}")
        inventory_fields = (
            row.get("inventory_members_json"),
            row.get("coverage_obligations_json"),
        )
        if not any(_contains_placeholder(item) for item in inventory_fields):
            try:
                inventory_members = json.loads(row["inventory_members_json"])
                obligations = json.loads(row["coverage_obligations_json"])
            except (KeyError, TypeError, json.JSONDecodeError) as exc:
                errors.append(f"test space {test_space_id} inventory obligations invalid: {exc}")
            else:
                if not isinstance(inventory_members, dict) or not inventory_members:
                    errors.append(f"test space {test_space_id} inventory_members_json must be a non-empty mapping")
                    inventory_members = {}
                if not isinstance(obligations, list) or not obligations:
                    errors.append(f"test space {test_space_id} coverage_obligations_json must be a non-empty list")
                    obligations = []
                all_members = {
                    member
                    for members in inventory_members.values()
                    if isinstance(members, list)
                    for member in members
                }
                inventory_ref = row.get("semantic_inventory_ref")
                applicable_coverage: list[tuple[dict[str, str], list[object], list[object], list[object]]] = []
                for coverage_row in coverage_rows:
                    if coverage_row.get("semantic_inventory_ref") != inventory_ref:
                        continue
                    try:
                        partition_refs = json.loads(coverage_row["inventory_partition_refs_json"])
                        member_refs = json.loads(coverage_row["inventory_member_refs_json"])
                        obligation_refs = json.loads(coverage_row["obligation_refs_json"])
                    except (KeyError, TypeError, json.JSONDecodeError) as exc:
                        errors.append(
                            f"coverage {coverage_row.get('coverage_id')} inventory refs invalid: {exc}"
                        )
                        continue
                    if not all(isinstance(item, list) for item in (partition_refs, member_refs, obligation_refs)):
                        errors.append(
                            f"coverage {coverage_row.get('coverage_id')} inventory refs must be JSON lists"
                        )
                        continue
                    unknown_partitions = set(partition_refs) - set(inventory_members)
                    unknown_members = set(member_refs) - all_members
                    if unknown_partitions:
                        errors.append(
                            f"coverage {coverage_row.get('coverage_id')} references unknown inventory partition"
                        )
                    if unknown_members:
                        errors.append(
                            f"coverage {coverage_row.get('coverage_id')} references unknown inventory member"
                        )
                    applicable_coverage.append(
                        (coverage_row, partition_refs, member_refs, obligation_refs)
                    )
                obligation_ids: set[str] = set()
                for obligation in obligations:
                    if not isinstance(obligation, dict):
                        errors.append(f"test space {test_space_id} obligation must be a mapping")
                        continue
                    obligation_id = obligation.get("obligation_id")
                    scope = obligation.get("scope")
                    partitions = obligation.get("partition_refs")
                    relation = obligation.get("required_relation")
                    if (
                        not isinstance(obligation_id, str)
                        or not obligation_id
                        or obligation_id in obligation_ids
                        or scope not in {"per_partition", "per_member"}
                        or not isinstance(partitions, list)
                        or not partitions
                        or relation
                        not in {
                            "positive",
                            "boundary",
                            "negative",
                            "failure_recovery",
                            "contrastive",
                            "metamorphic",
                        }
                    ):
                        errors.append(f"test space {test_space_id} obligation schema invalid")
                        continue
                    obligation_ids.add(obligation_id)
                    if set(partitions) - set(inventory_members):
                        errors.append(
                            f"test space {test_space_id} obligation {obligation_id} references unknown partition"
                        )
                        continue
                    if scope == "per_partition":
                        expected_items = partitions
                        item_index = 1
                    else:
                        expected_items = [
                            member
                            for partition in partitions
                            for member in inventory_members.get(partition, [])
                        ]
                        item_index = 2
                    for expected_item in expected_items:
                        if not any(
                            obligation_id in coverage_item[3]
                            and expected_item in coverage_item[item_index]
                            and coverage_item[0].get("case_relation") == relation
                            for coverage_item in applicable_coverage
                        ):
                            errors.append(
                                f"test space {test_space_id} missing obligation coverage: "
                                f"{obligation_id}/{expected_item}/{relation}"
                            )
                for coverage_row, _, _, obligation_refs in applicable_coverage:
                    unknown_obligations = set(obligation_refs) - obligation_ids
                    if unknown_obligations:
                        errors.append(
                            f"coverage {coverage_row.get('coverage_id')} references unknown obligation"
                        )

        concrete_fields = (
            row.get("dimension_domains_json"),
            row.get("forbidden_assignments_json"),
            row.get("interaction_strength"),
            row.get("generation_budget"),
        )
        if any(_contains_placeholder(item) for item in concrete_fields):
            continue
        try:
            domains = json.loads(row["dimension_domains_json"])
            forbidden = json.loads(row["forbidden_assignments_json"])
            strength = int(row["interaction_strength"])
            budget = int(row["generation_budget"])
        except (KeyError, TypeError, ValueError, json.JSONDecodeError) as exc:
            errors.append(f"test space {test_space_id} machine fields invalid: {exc}")
            continue
        if strength != 2:
            errors.append(f"test space {test_space_id} unsupported interaction_strength: {strength}")
            continue
        assignments: list[dict[str, object]] = []
        for combination in combination_rows:
            ref = _reference_key(combination.get("test_space_ref"))
            if ref != test_space_id:
                continue
            try:
                assignments.append(json.loads(combination["dimension_assignment_json"]))
            except (KeyError, TypeError, json.JSONDecodeError) as exc:
                errors.append(f"combination {combination.get('combination_id')} assignment invalid: {exc}")
        if len(assignments) > budget:
            errors.append(
                f"test space {test_space_id}: covering rows exceed generation_budget {budget}"
            )
        for error in validate_strength_two_coverage(domains, assignments, forbidden):
            errors.append(f"test space {test_space_id}: {error}")

    for combination in combination_rows:
        ref = _reference_key(combination.get("test_space_ref"))
        if ref is not None and ref not in test_spaces:
            errors.append(f"unresolved Test Space reference: {ref}")
    for coverage_id, row in coverage.items():
        ref = _reference_key(row.get("behavior_case_ref"))
        if ref is not None and ref not in behavior_cases:
            errors.append(f"unresolved Behavior Case reference: {ref}")

    oracle_refs = {_reference_key(row.get("coverage_ref")) for row in oracle_rows}
    for ref in sorted(item for item in oracle_refs if item is not None and item not in coverage):
        errors.append(f"unresolved Failure Recovery coverage reference: {ref}")
    failure_case_ids = {
        case_id
        for case_id, row in behavior_cases.items()
        if row.get("case_type") == "failure_recovery"
    }
    for case_id in sorted(failure_case_ids):
        related = [
            coverage_id
            for coverage_id, row in coverage.items()
            if _reference_key(row.get("behavior_case_ref")) == case_id
        ]
        if not related:
            errors.append(f"failure_recovery case has no coverage: {case_id}")
        for coverage_id in related:
            if coverage_id not in oracle_refs:
                errors.append(f"failure_recovery coverage has no oracle: {coverage_id}")
    return errors


def _table_keys(
    contract: dict,
    package_root: Path,
    table_name: str,
    key_column: str,
) -> tuple[set[str], list[str]]:
    tables, errors = _parse_contract_tables(contract, package_root, {table_name})
    if table_name not in tables:
        return set(), errors
    return {row.get(key_column, "") for row in tables[table_name][1]}, errors


def _validate_spec_cross_package_refs(
    contract: dict,
    package_root: Path,
    tables: dict[str, tuple[list[str], list[dict[str, str]]]],
    embedded: dict[str, object],
    related_packages: dict[str, tuple[dict, Path]],
) -> list[str]:
    errors: list[str] = []
    rules = contract.get("cross_package_reference_rules", {})
    source_ref = rules.get("source_contract_ref") if isinstance(rules, dict) else None
    source = related_packages.get(source_ref) if isinstance(source_ref, str) else None
    if source is None:
        return [f"missing related package for cross-package validation: {source_ref}"]
    source_contract, source_root = source
    behavior_keys, source_errors = _table_keys(
        source_contract, source_root, "Behavior Case Registry", "case_id"
    )
    errors.extend(source_errors)
    coverage_keys, source_errors = _table_keys(
        source_contract, source_root, "Acceptance Coverage Matrix", "coverage_id"
    )
    errors.extend(source_errors)
    behavior_spec_keys, source_errors = _table_keys(
        source_contract, source_root, "Behavior Specification", "behavior_spec_id"
    )
    errors.extend(source_errors)

    spec_yaml, parse_error = _load_package_yaml(package_root / "spec.yaml")
    if parse_error:
        errors.append(parse_error)
        spec_yaml = {}
    if isinstance(spec_yaml, dict):
        ref = _reference_key(spec_yaml.get("behavior_specification_ref"))
        if ref is not None and ref not in behavior_spec_keys:
            errors.append(f"unresolved Behavior Specification reference: {ref}")

    behavior_refs: list[object] = []
    coverage_refs: list[object] = []
    spec_document = embedded.get("spec.md")
    if isinstance(spec_document, dict):
        behavior_refs.extend(spec_document.get("behavior_case_refs", []))
        coverage_refs.extend(spec_document.get("acceptance_coverage_refs", []))
    tasks_document = embedded.get("tasks.md")
    tasks = tasks_document.get("task_declarations", []) if isinstance(tasks_document, dict) else []
    criteria = {row["Criterion"] for row in tables.get("验收判据", ([], []))[1]}
    for task in tasks:
        if not isinstance(task, dict):
            continue
        behavior_refs.extend(task.get("behavior_case_refs", []))
        coverage_refs.extend(task.get("acceptance_coverage_refs", []))
        criterion = _reference_key(task.get("criterion_ref"))
        if criterion is not None and criterion not in criteria:
            errors.append(f"unresolved criterion reference: {criterion}")
    for row in tables.get("验收判据", ([], []))[1]:
        behavior_refs.append(row.get("Behavior Case Ref"))
        coverage_refs.append(row.get("Coverage Ref"))
    for row in tables.get("追溯", ([], []))[1]:
        if row.get("关系") == "implements_behavior":
            behavior_refs.append(row.get("上游批准对象"))
            coverage_refs.append(row.get("验收出口"))
    for value in behavior_refs:
        ref = _reference_key(value)
        if ref is not None and ref not in behavior_keys:
            errors.append(f"unresolved Behavior Case reference: {ref}")
    for value in coverage_refs:
        ref = _reference_key(value)
        if ref is not None and ref not in coverage_keys:
            errors.append(f"unresolved Coverage reference: {ref}")
    return errors


def validate_package_profile(
    contract: dict,
    package_root: Path,
    contract_ref: str,
    validation_profile: str,
    related_packages: dict[str, tuple[dict, Path]] | None = None,
    allow_placeholders: bool = False,
) -> list[str]:
    """按显式 profile 读取并验证真实 package；v1 只读 shape 与 v2 阶段退出分离。"""
    errors = validate_profile_dispatch(contract, contract_ref, validation_profile)
    if errors:
        return errors
    version = int(contract_ref.rsplit("@", 1)[1])
    if version != contract.get("version"):
        historical = contract.get("historical_package_shapes")
        shape = historical.get(version) if isinstance(historical, dict) else None
        if not isinstance(shape, dict):
            return [f"missing historical package shape for version {version}"]
        errors.extend(_validate_package_shape(shape, package_root))
        return errors

    chain, chain_errors = _profile_chain(contract, validation_profile)
    errors.extend(chain_errors)
    profiles = contract.get("validation_profiles", {})
    if errors:
        return errors

    if contract.get("contract_id") == "spec-package-contract":
        delegated_to = next(
            (
                profiles[profile_name].get("delegated_to")
                for profile_name in chain
                if isinstance(profiles.get(profile_name), dict)
                and isinstance(profiles[profile_name].get("delegated_to"), str)
            ),
            None,
        )
        if delegated_to is not None:
            source_ref, separator, source_profile = delegated_to.partition("#")
            source = (related_packages or {}).get(source_ref)
            if not separator or not source_profile or source is None:
                errors.append(f"unresolved delegated profile: {delegated_to}")
            else:
                source_contract, source_root = source
                errors.extend(
                    validate_package_profile(
                        source_contract,
                        source_root,
                        source_ref,
                        source_profile,
                        allow_placeholders=allow_placeholders,
                    )
                )
        if validation_profile != "s5_exit":
            return errors

    errors.extend(_validate_package_shape(contract, package_root))
    if errors:
        return errors

    required_tables: set[str] = set()
    required_root_references: set[str] = set()
    for profile_name in chain:
        profile = profiles.get(profile_name, {})
        required_tables.update(profile.get("required_tables", []))
        required_root_references.update(profile.get("required_root_references", []))
    tables, table_errors = _parse_contract_tables(contract, package_root, required_tables or None)
    errors.extend(table_errors)
    embedded, embedded_errors = _validate_embedded_yaml(contract, package_root)
    errors.extend(embedded_errors)
    if not allow_placeholders:
        for table_name, (_, rows) in tables.items():
            if _contains_placeholder(rows):
                errors.append(f"unresolved template placeholder in table: {table_name}")
        for filename, document in embedded.items():
            if _contains_placeholder(document):
                errors.append(f"unresolved template placeholder in embedded YAML: {filename}")

    dispatch = contract.get("profile_dispatch", {})
    root_source = dispatch.get("contract_ref_source") if isinstance(dispatch, dict) else None
    root_filename = root_source.split("#", 1)[0] if isinstance(root_source, str) else None
    root_document: object = None
    if required_root_references:
        root_path = _package_path(package_root, root_filename)
        if root_path is None or not root_path.is_file():
            errors.append(f"missing profile root document: {root_filename}")
        else:
            root_document, parse_error = _load_package_yaml(root_path)
            if parse_error:
                errors.append(parse_error)
            for field in sorted(required_root_references):
                exists, value = _dotted_value(root_document, field)
                if not exists or not isinstance(value, str) or not value:
                    errors.append(f"missing profile root reference: {field}")
                elif not allow_placeholders and _contains_placeholder(value):
                    errors.append(f"unresolved template placeholder in root reference: {field}")

    root_rules = contract.get("root_references", {})
    if isinstance(root_document, dict) and isinstance(root_rules, dict) and root_filename in root_rules:
        for field in sorted(required_root_references):
            rule = root_rules[root_filename].get(field)
            exists, reference = _dotted_value(root_document, field)
            if not exists or not isinstance(reference, str) or not isinstance(rule, dict):
                continue
            if allow_placeholders and _contains_placeholder(reference):
                continue
            target_file = rule.get("target_file")
            canonical_section = rule.get("canonical_section")
            table_section = rule.get("table_section")
            key_column = rule.get("key_column")
            prefix = f"{target_file}#{canonical_section}:"
            key = reference[len(prefix):] if reference.startswith(prefix) else None
            table = tables.get(table_section)
            if key == "*" and rule.get("allow_wildcard") is True:
                continue
            if (
                key is None
                or table is None
                or not isinstance(key_column, str)
                or key not in {row.get(key_column) for row in table[1]}
            ):
                errors.append(f"unresolved profile root reference: {field}")

    if contract.get("contract_id") == "chain-package-contract" and "s4_exit" in chain:
        errors.extend(_validate_chain_profile_tables(tables))
    if contract.get("contract_id") == "spec-package-contract" and "s5_exit" in chain:
        errors.extend(
            _validate_spec_cross_package_refs(
                contract,
                package_root,
                tables,
                embedded,
                related_packages or {},
            )
        )
    return errors


def validate_profile_dispatch(
    contract: dict,
    contract_ref: str,
    validation_profile: str,
) -> list[str]:
    """验证显式 profile 与 contract major 的确定性绑定；不做隐式选择。"""
    profiles = contract.get("validation_profiles")
    if not isinstance(profiles, dict) or validation_profile not in profiles:
        return [f"unknown_profile: {validation_profile}"]
    if not isinstance(contract_ref, str) or "@" not in contract_ref:
        return [f"profile_contract_mismatch: invalid contract_ref {contract_ref!r}"]
    contract_id, raw_version = contract_ref.rsplit("@", 1)
    try:
        version = int(raw_version)
    except ValueError:
        return [f"profile_contract_mismatch: invalid contract version {raw_version!r}"]
    if contract_id != contract.get("contract_id"):
        return [f"profile_contract_mismatch: expected {contract.get('contract_id')}, got {contract_id}"]

    errors: list[str] = []
    dispatch = contract.get("profile_dispatch")
    required_profile_fields = (
        dispatch.get("required_profile_fields") if isinstance(dispatch, dict) else None
    )
    if not isinstance(required_profile_fields, dict):
        errors.append("profile_dispatch.required_profile_fields must be a mapping")
        required_profile_fields = {}
    for profile_name, required_fields in required_profile_fields.items():
        profile = profiles.get(profile_name)
        if not isinstance(profile, dict) or not isinstance(required_fields, list):
            errors.append(f"invalid required_profile_fields declaration: {profile_name}")
            continue
        for field in required_fields:
            if not isinstance(field, str) or field not in profile:
                errors.append(f"validation_profile {profile_name} missing required field: {field}")
    all_table_names = {
        section
        for section_specs in contract.get("markdown_tables", {}).values()
        if isinstance(section_specs, dict)
        for section in section_specs
    } if isinstance(contract.get("markdown_tables", {}), dict) else set()
    for profile_name, profile in profiles.items():
        if not isinstance(profile, dict):
            continue
        required_tables = profile.get("required_tables", [])
        if not isinstance(required_tables, list) or any(
            not isinstance(table, str) for table in required_tables
        ):
            errors.append(f"validation_profile {profile_name} required_tables must be list[str]")
        else:
            for table in required_tables:
                if table not in all_table_names:
                    errors.append(f"validation_profile {profile_name} references unknown required_table: {table}")
        if profile_name == "historical_read_v1":
            shapes = contract.get("historical_package_shapes")
            historical_versions = profile.get("allowed_contract_versions", [])
            for historical_version in historical_versions:
                if not isinstance(shapes, dict) or historical_version not in shapes:
                    errors.append(
                        f"historical_read_v1 missing package shape for version {historical_version}"
                    )
    visited: set[str] = set()
    current = validation_profile
    while current:
        if current in visited:
            errors.append(f"profile_inheritance_cycle: {current}")
            break
        visited.add(current)
        profile = profiles.get(current)
        if not isinstance(profile, dict):
            errors.append(f"unknown_profile: {current}")
            break
        allowed = profile.get("allowed_contract_versions")
        if not isinstance(allowed, list) or any(
            isinstance(item, bool) or not isinstance(item, int) for item in allowed
        ):
            errors.append(f"invalid_profile_versions: {current}")
        elif version not in allowed:
            errors.append(
                f"profile_contract_mismatch: {current} does not allow {contract_ref}"
            )
        inherited = profile.get("inherits")
        if inherited is not None and not isinstance(inherited, str):
            errors.append(f"invalid_profile_inheritance: {current}")
            break
        current = inherited
    return errors


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

        table_specs = contract.get("markdown_tables")
        parsed_tables: dict[tuple[str, str], tuple[list[str], list[dict[str, str]]]] = {}
        if table_specs is not None and not isinstance(table_specs, dict):
            findings.append(Finding("C9", "P0", rel(repo, contract_path), 0, "markdown_tables 必须是 mapping"))
        elif isinstance(table_specs, dict):
            expected_parsing = {
                "dialect": "commonmark_pipe_table_subset",
                "heading_match": "exact_text",
                "table_selection": "first_pipe_table_after_heading_before_next_heading",
                "cell_normalization": "trim_whitespace_and_single_backtick_wrapper",
                "unescaped_pipe_or_row_width_mismatch": "invalid_package",
                "duplicate_section": "invalid_package",
            }
            if contract.get("markdown_parsing") != expected_parsing:
                findings.append(Finding("C9", "P0", rel(repo, contract_path), 0, "markdown_parsing 必须声明统一受支持子集"))
            forbidden_fields = contract.get("forbidden_execution_fields", [])
            if not isinstance(forbidden_fields, list) or any(
                not isinstance(field, str) for field in forbidden_fields
            ):
                findings.append(Finding("C9", "P0", rel(repo, contract_path), 0, "forbidden_execution_fields 必须是 list[str]"))
                forbidden_fields = []
            for filename, section_specs in table_specs.items():
                if not isinstance(filename, str) or not isinstance(section_specs, dict):
                    findings.append(Finding("C9", "P0", rel(repo, contract_path), 0, "markdown_tables 文件规则必须是 mapping"))
                    continue
                target, errors = resolve_repo_path(
                    repo,
                    str(Path(template_root_value) / filename),
                    "C9",
                    f"markdown_tables filename {filename!r}",
                )
                findings.extend(errors)
                if errors or target is None or not target.is_file():
                    continue
                text = read_text(target)
                for section, table_rule in section_specs.items():
                    if not isinstance(section, str) or not isinstance(table_rule, dict):
                        findings.append(Finding("C9", "P0", rel(repo, contract_path), 0, f"markdown_tables[{filename}] section rule 必须是 mapping"))
                        continue
                    expected_columns = table_rule.get("columns")
                    if not isinstance(expected_columns, list) or any(
                        not isinstance(column, str) for column in expected_columns
                    ):
                        findings.append(Finding("C9", "P0", rel(repo, contract_path), 0, f"markdown_tables[{filename}][{section}].columns 必须是 list[str]"))
                        continue
                    columns, rows, parse_error = _parse_markdown_table(text, section)
                    if parse_error:
                        findings.append(Finding("C9", "P0", rel(repo, target), 0, f"Markdown table {section}: {parse_error}"))
                        continue
                    parsed_tables[(filename, section)] = (columns, rows)
                    if columns != expected_columns:
                        findings.append(Finding("C9", "P0", rel(repo, target), 0, f"Markdown table {section} columns 不匹配"))
                        continue
                    if set(columns) & set(forbidden_fields):
                        findings.append(Finding("C9", "P0", rel(repo, target), 0, f"Markdown table {section} 包含执行后 forbidden field"))
                    minimum_rows = table_rule.get("minimum_rows", 0)
                    if isinstance(minimum_rows, bool) or not isinstance(minimum_rows, int) or minimum_rows < 0:
                        findings.append(Finding("C9", "P0", rel(repo, contract_path), 0, f"markdown_tables[{filename}][{section}].minimum_rows 必须是非负整数"))
                    elif len(rows) < minimum_rows:
                        findings.append(Finding("C9", "P0", rel(repo, target), 0, f"Markdown table {section} rows 少于 minimum_rows"))
                    primary_key = table_rule.get("primary_key")
                    if not isinstance(primary_key, str) or primary_key not in columns:
                        findings.append(Finding("C9", "P0", rel(repo, contract_path), 0, f"Markdown table {section} primary_key 无效"))
                    else:
                        keys = [row.get(primary_key, "") for row in rows]
                        if any(not key for key in keys):
                            findings.append(Finding("C9", "P0", rel(repo, target), 0, f"Markdown table {section} primary key 为空"))
                        if len(keys) != len(set(keys)):
                            findings.append(Finding("C9", "P0", rel(repo, target), 0, f"Markdown table {section} duplicate primary key"))
                    allowed_enums = table_rule.get("allowed_enums", {})
                    if not isinstance(allowed_enums, dict):
                        findings.append(Finding("C9", "P0", rel(repo, contract_path), 0, f"Markdown table {section} allowed_enums 必须是 mapping"))
                    else:
                        for field, allowed_values in allowed_enums.items():
                            if field not in columns or not isinstance(allowed_values, list) or any(not isinstance(value, str) for value in allowed_values):
                                findings.append(Finding("C9", "P0", rel(repo, contract_path), 0, f"Markdown table {section} allowed enum {field} 无效"))
                                continue
                            for row in rows:
                                value = row.get(field, "")
                                if "{{" in value and "}}" in value:
                                    continue
                                if value not in allowed_values:
                                    findings.append(Finding("C9", "P0", rel(repo, target), 0, f"Markdown table {section} field {field} violates allowed enum"))

        root_references = contract.get("root_references")
        if root_references is not None and not isinstance(root_references, dict):
            findings.append(Finding("C9", "P0", rel(repo, contract_path), 0, "root_references 必须是 mapping"))
        elif isinstance(root_references, dict):
            for filename, reference_specs in root_references.items():
                if not isinstance(filename, str) or not isinstance(reference_specs, dict):
                    findings.append(Finding("C9", "P0", rel(repo, contract_path), 0, "root_references 文件规则必须是 mapping"))
                    continue
                target, errors = resolve_repo_path(repo, str(Path(template_root_value) / filename), "C9", f"root_references filename {filename!r}")
                findings.extend(errors)
                if errors or target is None or not target.is_file():
                    continue
                document = yaml_cache.get(filename)
                if filename not in yaml_cache:
                    document, errors = _load_yaml(repo, target, "C9")
                    findings.extend(errors)
                for field, reference_rule in reference_specs.items():
                    exists, reference = _dotted_value(document, field)
                    if not exists or not isinstance(reference, str) or not isinstance(reference_rule, dict):
                        findings.append(Finding("C9", "P0", rel(repo, target), 0, f"unresolved canonical reference: {field}"))
                        continue
                    target_file = reference_rule.get("target_file")
                    canonical_section = reference_rule.get("canonical_section")
                    table_section = reference_rule.get("table_section")
                    key_column = reference_rule.get("key_column")
                    expected_prefix = f"{target_file}#{canonical_section}:"
                    key = reference[len(expected_prefix):] if reference.startswith(expected_prefix) else None
                    table = parsed_tables.get((target_file, table_section))
                    if key is None or table is None or not isinstance(key_column, str):
                        findings.append(Finding("C9", "P0", rel(repo, target), 0, f"unresolved canonical reference: {field}"))
                        continue
                    if key == "*" and reference_rule.get("allow_wildcard") is True:
                        continue
                    _, rows = table
                    if key not in {row.get(key_column) for row in rows}:
                        findings.append(Finding("C9", "P0", rel(repo, target), 0, f"unresolved canonical reference: {field}"))

        profiles = contract.get("validation_profiles")
        if profiles is not None:
            if not isinstance(profiles, dict):
                findings.append(Finding("C9", "P0", rel(repo, contract_path), 0, "validation_profiles 必须是 mapping"))
            else:
                for profile_name, profile in profiles.items():
                    if not isinstance(profile_name, str) or not isinstance(profile, dict):
                        findings.append(Finding("C9", "P0", rel(repo, contract_path), 0, "validation_profile 定义无效"))
                        continue
                    for version in profile.get("allowed_contract_versions", []):
                        contract_ref = f"{contract.get('contract_id')}@{version}"
                        for error in validate_profile_dispatch(contract, contract_ref, profile_name):
                            findings.append(Finding("C9", "P0", rel(repo, contract_path), 0, error))

                related_packages: dict[str, tuple[dict, Path]] = {}
                cross_rules = contract.get("cross_package_reference_rules")
                source_contract_ref = (
                    cross_rules.get("source_contract_ref")
                    if isinstance(cross_rules, dict)
                    else None
                )
                if isinstance(source_contract_ref, str) and "@" in source_contract_ref:
                    source_contract_id = source_contract_ref.rsplit("@", 1)[0]
                    for candidate_path in contract_files:
                        candidate, candidate_errors = _load_yaml(repo, candidate_path, "C9")
                        if candidate_errors or not isinstance(candidate, dict):
                            continue
                        if candidate.get("contract_id") != source_contract_id:
                            continue
                        source_template = _package_path(
                            repo, candidate.get("template_root")
                        )
                        if source_template is not None and source_template.is_dir():
                            related_packages[source_contract_ref] = (
                                candidate,
                                source_template,
                            )
                        break

                current_version = contract.get("version")
                if isinstance(current_version, int) and not isinstance(current_version, bool):
                    current_ref = f"{contract.get('contract_id')}@{current_version}"
                    for profile_name, profile in profiles.items():
                        if not isinstance(profile_name, str) or not isinstance(profile, dict):
                            continue
                        if current_version not in profile.get("allowed_contract_versions", []):
                            continue
                        for error in validate_package_profile(
                            contract,
                            template_root,
                            current_ref,
                            profile_name,
                            related_packages,
                            allow_placeholders=True,
                        ):
                            findings.append(
                                Finding(
                                    "C9",
                                    "P0",
                                    rel(repo, contract_path),
                                    0,
                                    f"profile {profile_name}: {error}",
                                )
                            )

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
    readable_versions: dict[str, set[int]] = {}
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
            compatibility = contract.get("compatibility")
            historical = (
                compatibility.get("historical_read_contract_versions", [])
                if isinstance(compatibility, dict)
                else []
            )
            if not isinstance(historical, list) or any(
                isinstance(item, bool) or not isinstance(item, int) or item <= 0
                for item in historical
            ):
                findings.append(Finding("C11", "P0", rel(repo, path), 0, "compatibility.historical_read_contract_versions 必须是正整数列表"))
                historical = []
            readable_versions[contract_id] = {version, *historical}

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
                if registered is None or int(version_text) not in readable_versions.get(contract_id, {registered[0]}):
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
