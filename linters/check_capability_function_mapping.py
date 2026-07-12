#!/usr/bin/env python3
"""C13：检查 Capability → Function → Functional Requirement → Spec 静态闭环。"""
from __future__ import annotations

import argparse
import re
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml


@dataclass(frozen=True)
class Finding:
    severity: str
    code: str
    path: str
    message: str


def _frontmatter(path: Path) -> dict[str, Any] | None:
    text = path.read_text(encoding="utf-8")
    if not text.startswith("---\n"):
        return None
    end = text.find("\n---", 4)
    if end < 0:
        raise ValueError(f"frontmatter 未闭合: {path}")
    payload = yaml.safe_load(text[4:end]) or {}
    if not isinstance(payload, dict):
        raise ValueError(f"frontmatter 必须是 mapping: {path}")
    return payload


def _is_placeholder(value: Any) -> bool:
    return isinstance(value, str) and ("{{" in value or value.startswith("CAP-UPSTREAM"))


def _refs(value: Any) -> list[str]:
    if value in (None, ""):
        return []
    if isinstance(value, str):
        return [] if _is_placeholder(value) else [value]
    if isinstance(value, list):
        return [item for item in value if isinstance(item, str) and not _is_placeholder(item)]
    return []


def load_records(root: Path) -> tuple[dict[str, dict[str, Any]], dict[str, Path], list[Finding]]:
    registry: dict[str, dict[str, Any]] = {}
    origins: dict[str, Path] = {}
    findings: list[Finding] = []
    requirements_root = root / "requirements"
    if not requirements_root.exists():
        return registry, origins, findings
    for path in sorted(requirements_root.rglob("*.md")):
        try:
            record = _frontmatter(path)
        except (OSError, ValueError, yaml.YAMLError) as exc:
            findings.append(Finding("P0", "C13-PARSE", str(path.relative_to(root)), str(exc)))
            continue
        if not record or "stable_id" not in record:
            continue
        stable_id = record.get("stable_id")
        if not isinstance(stable_id, str) or not stable_id:
            findings.append(Finding("P0", "C13-ID", str(path.relative_to(root)), "stable_id 必须是非空字符串"))
            continue
        if stable_id in registry:
            findings.append(Finding("P0", "C13-DUPLICATE", str(path.relative_to(root)), f"stable_id 重复: {stable_id}"))
            continue
        registry[stable_id] = record
        origins[stable_id] = path
    return registry, origins, findings


def validate(root: Path) -> list[Finding]:
    registry, origins, findings = load_records(root)
    capabilities = {
        stable_id: record
        for stable_id, record in registry.items()
        if record.get("object_type") == "business_capability"
    }
    functional_requirements = {
        stable_id: record
        for stable_id, record in registry.items()
        if record.get("object_type") == "requirement"
        and record.get("requirement_kind") == "functional"
    }

    for stable_id, capability in capabilities.items():
        path = str(origins[stable_id].relative_to(root))
        parent = capability.get("parent_capability_ref")
        if isinstance(parent, str) and parent and not _is_placeholder(parent) and parent not in capabilities:
            findings.append(Finding("P0", "C13-ORPHAN-PARENT", path, f"父级 Capability 无法解析: {parent}"))
        for child in _refs(capability.get("child_capability_refs")):
            if child not in capabilities:
                findings.append(Finding("P0", "C13-ORPHAN-CHILD", path, f"子 Capability 无法解析: {child}"))
        for function_id in _refs(capability.get("function_refs")):
            if not any(record.get("function_id") == function_id for record in functional_requirements.values()):
                findings.append(Finding("P1", "C13-FUNCTION-WITHOUT-REQUIREMENT", path, f"Function 缺少功能需求卡: {function_id}"))

    graph = {
        stable_id: [child for child in _refs(record.get("child_capability_refs")) if child in capabilities]
        for stable_id, record in capabilities.items()
    }
    visiting: set[str] = set()
    visited: set[str] = set()

    def walk(node: str, stack: list[str]) -> None:
        if node in visiting:
            cycle = " -> ".join(stack + [node])
            findings.append(Finding("P0", "C13-CAPABILITY-CYCLE", str(origins[node].relative_to(root)), f"Capability 循环: {cycle}"))
            return
        if node in visited:
            return
        visiting.add(node)
        for child in graph.get(node, []):
            walk(child, stack + [node])
        visiting.remove(node)
        visited.add(node)

    for capability_id in sorted(graph):
        walk(capability_id, [])

    for stable_id, requirement in functional_requirements.items():
        path = str(origins[stable_id].relative_to(root))
        capability_refs = _refs(requirement.get("capability_refs"))
        if not capability_refs:
            findings.append(Finding("P0", "C13-ORPHAN-FUNCTION", path, "功能需求没有 capability_refs"))
        for capability_ref in capability_refs:
            if capability_ref not in capabilities:
                findings.append(Finding("P0", "C13-UNKNOWN-CAPABILITY", path, f"Capability 无法解析: {capability_ref}"))
        spec_refs = _refs(requirement.get("spec_refs"))
        approval = requirement.get("approval_status")
        approved_intent = (requirement.get("intent") or {}).get("approved_intent") if isinstance(requirement.get("intent"), dict) else None
        approver = str(requirement.get("approver") or "")
        if spec_refs and approval != "approved":
            findings.append(Finding("P0", "C13-UNAPPROVED-SPEC", path, "未批准功能需求不得被 active Spec 消费"))
        if approval == "approved" and (not approved_intent or not approver.startswith("human-")):
            findings.append(Finding("P0", "C13-INVALID-APPROVAL", path, "approved 功能需求必须具有 approved_intent 和可验证人类 approver"))
        if requirement.get("candidate_solution_status") != "candidate":
            findings.append(Finding("P1", "C13-SOLUTION-PROMOTION", path, "候选方案不得在需求卡内自动升格"))

    return sorted(findings, key=lambda item: (item.severity, item.code, item.path, item.message))


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("repo_root", nargs="?", default=".")
    parser.add_argument("--report", action="store_true")
    args = parser.parse_args()
    root = Path(args.repo_root).resolve()
    findings = validate(root)
    p0 = sum(item.severity == "P0" for item in findings)
    p1 = sum(item.severity == "P1" for item in findings)
    print(f"C13 capability/function traceability: P0={p0} P1={p1}")
    if args.report:
        for finding in findings:
            print(f"[{finding.severity}] {finding.code} {finding.path}: {finding.message}")
    return 1 if findings else 0


if __name__ == "__main__":
    sys.exit(main())
