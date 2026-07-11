#!/usr/bin/env python3
"""
最小追溯检查器 — ai-project-os Phase 0 核心产物

检查项直接来自 reviews/p0-design-revision-score.yaml open_items：
  C1  stable_id 在本仓库内唯一，且 canonical_path 文件存在
  C2  object_type=source 不得驱动 Spec/Task/Workflow/Skill（绕过批准事实）
  C3  p0/p1 优先级需求必须有对应 spec + traceability 文件出口
  C4  L1 文件不得反向引用 L2/L3 具体仓库路径（单向依赖强制）
  C5  proof_level 枚举只在 GATES_PROOF_SCORING.md 一处定义

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

# L2/L3 仓库路径特征（L1 文件不得引用这些路径）
L2_PATH_PATTERNS = [
    r"operate-auto-customer/",
    r"projects/[a-zA-Z0-9_\-]+/",   # L3 项目 namespace
]

# 豁免：这些文件允许出现 L2 路径（模板、接入指南、linter 自身的模式定义）
C4_EXEMPT_FILES = {
    "docs/workflows/L2_ONBOARDING.md",    # 接入指南本身需要引用 L2 示例路径
    "linters/check_controlled_objects.py", # linter 自身定义的模式字符串
}

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


def exit_code_for_findings(findings: list[Finding]) -> int:
    """P0 或 P1 都表示治理门禁失败。"""
    return 0 if gate_pass_for_findings(findings) else 1


def gate_pass_for_findings(findings: list[Finding]) -> bool:
    """机器 Evidence 与进程退出码共享同一门禁语义。"""
    return not any(f.severity in {"P0", "P1"} for f in findings)


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


def iter_repo_files(repo: Path, skip_run_artifacts: bool = False) -> list[Path]:
    """遍历仓库所有受扫描文件，跳过 .git 和 linters 自身。"""
    result = []
    for p in repo.rglob("*"):
        if not p.is_file():
            continue
        parts = p.parts
        if ".git" in parts:
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
            m = re.search(r"stable_id\s*:\s*['\"]?([a-zA-Z0-9_\-\.]+)['\"]?", line)
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
                # 跳过模板占位符（如 path/to/authority、{{ xxx }}）
                if cp_val.startswith("path/to") or "{{" in cp_val or cp_val == "null":
                    pass
                else:
                    cp = repo / cp_val
                    if not cp.exists():
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
        # 跳过模板和豁免文件（接入指南、linter 自身的模式定义字符串）
        if "templates/" in rp or rp in C4_EXEMPT_FILES:
            continue
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
    """C6: AI 自动审核不得回退到逐条人工等待。"""
    findings: list[Finding] = []
    for p in files:
        if p.suffix not in {".yaml", ".yml"}:
            continue
        text = read_text(p)
        if not re.search(r"^\s*review_mode\s*:\s*ai_automated\s*$", text, re.M):
            continue
        for line_number, line in enumerate(text.splitlines(), 1):
            if re.search(r"\bwaiting_approval\b", line):
                findings.append(Finding(
                    "C6", "P0", rel(repo, p), line_number,
                    "AI 自动审核 Workflow 不得进入 waiting_approval；应自动改写、阻断或记录规则缺口",
                ))
                break
    return findings


AI_REVIEW_REQUIRED_FIELDS = {
    "subject_ref",
    "generator_run_ref",
    "generator_execution_node_ref",
    "review_run_ref",
    "reviewer_actor_id",
    "reviewer_execution_node_ref",
    "rule_set_ref",
    "rule_set_hash",
    "evidence_refs",
    "decision",
    "max_rewrite_attempts",
}


def check_c7_ai_review_manifest(repo: Path, files: list[Path]) -> list[Finding]:
    """C7: AI 审核裁决必须绑定规则集、独立 Run 和有界改写。"""
    findings: list[Finding] = []
    for p in files:
        if p.suffix not in {".yaml", ".yml"}:
            continue
        text = read_text(p)
        if not re.search(r"^\s*object_type\s*:\s*ai_review_verdict\s*$", text, re.M):
            continue
        present_fields = {
            match.group(1)
            for match in re.finditer(r"^\s*([a-zA-Z_][a-zA-Z0-9_]*)\s*:", text, re.M)
        }
        missing = sorted(AI_REVIEW_REQUIRED_FIELDS - present_fields)
        if missing:
            findings.append(Finding(
                "C7", "P0", rel(repo, p), 0,
                "ai_review_verdict 缺少必需字段: " + ", ".join(missing),
            ))

        decision_match = re.search(r"^\s*decision\s*:\s*([a-z_]+)\s*$", text, re.M)
        limit_match = re.search(r"^\s*max_rewrite_attempts\s*:\s*(-?\d+)\s*$", text, re.M)
        if (
            decision_match
            and decision_match.group(1) == "rewrite_required"
            and (not limit_match or int(limit_match.group(1)) <= 0)
        ):
            findings.append(Finding(
                "C7", "P0", rel(repo, p), 0,
                "rewrite_required 必须声明正整数 max_rewrite_attempts",
            ))
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
        "version": "0.1.0",
        "repo": str(repo),
        "files_scanned": len(files),
        "p0_count": len(p0),
        "p1_count": len(p1),
        "pass": gate_pass_for_findings(all_findings),
        "findings": [f.as_dict() for f in all_findings],
    }
    print("\n# JSON Evidence (保存此段到 reviews/phase0-checker-evidence.yaml)")
    print(json.dumps(report, ensure_ascii=False, indent=2))

    return exit_code_for_findings(all_findings)


if __name__ == "__main__":
    sys.exit(main())
