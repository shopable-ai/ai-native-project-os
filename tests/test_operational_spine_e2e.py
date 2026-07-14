"""匿名 operational-spine fixture 的端到端结构与恢复不变量测试。"""

from __future__ import annotations

import copy
import hashlib
import re
import unittest
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Iterable

import yaml


ROOT = Path(__file__).resolve().parents[1]
POSITIVE = ROOT / "fixtures" / "operational-spine" / "positive"
NEGATIVE = ROOT / "fixtures" / "operational-spine" / "negative"
SNAPSHOT = ROOT / "reviews" / "operational-spine-static-and-fixture-evidence.yaml"
GATES = ROOT / "docs" / "governance" / "GATES_PROOF_SCORING.md"
ACCEPTANCE_CONTRACT = ROOT / "contracts" / "governance" / "acceptance-verdict-claim-contract.yaml"
GOVERNANCE_CONTRACTS = {
    "ROUTE-FIX-001": ROOT / "contracts" / "governance" / "route-decision-contract.yaml",
    "CONTROL-FIX-001": ROOT / "contracts" / "governance" / "control-set-contract.yaml",
    "AUTH-FIX-001": ROOT / "contracts" / "governance" / "authorization-snapshot-contract.yaml",
    "AI-REVIEW-FIX-001": ROOT / "contracts" / "governance" / "ai-review-verdict-contract.yaml",
}
OBJECT_ID_FIELDS = (
    "stable_id",
    "requirement_id",
    "criterion_id",
    "diagram_id",
    "spec_id",
    "task_id",
    "workflow_id",
    "skill_id",
    "tool_id",
    "run_id",
    "checkpoint_id",
    "evidence_id",
    "verdict_id",
    "claim_id",
    "recovery_id",
    "route_decision_id",
    "overlay_status_snapshot_id",
    "control_set_id",
    "review_verdict_id",
    "authorization_snapshot_id",
    "signature_id",
    "baseline_id",
    "rule_set_id",
    "rule_id",
    "execution_node_id",
    "capability_grant_id",
    "principal_id",
    "attempt_id",
)


def load_proof_order() -> tuple[str, ...]:
    text = GATES.read_text(encoding="utf-8")
    evidence_ladder = text.split("## 1. 证据阶梯", 1)[1].split("## 2. 门禁公式", 1)[0]
    return tuple(re.findall(r"(?m)^\| `([a-z_]+)` \|", evidence_ladder))


PROOF_ORDER = load_proof_order()


def load_yaml(path: Path) -> Any:
    return yaml.safe_load(path.read_text(encoding="utf-8"))


def derive_overlay_requirement(
    route_inputs: dict[str, Any],
    overlay_policy: dict[str, Any],
) -> bool | str:
    for field, unknown_values in overlay_policy.get("unknown_when_any", {}).items():
        if route_inputs.get(field) in unknown_values:
            return "unknown"
    for field, required_values in overlay_policy.get("when_any", {}).items():
        if route_inputs.get(field) in required_values:
            return True
    return False


def iter_records(value: Any) -> Iterable[dict[str, Any]]:
    if isinstance(value, dict):
        if any(key in value for key in OBJECT_ID_FIELDS):
            yield value
        for child in value.values():
            yield from iter_records(child)
    elif isinstance(value, list):
        for child in value:
            yield from iter_records(child)


def build_registry(root: Path) -> tuple[dict[str, dict[str, Any]], dict[str, Path]]:
    registry: dict[str, dict[str, Any]] = {}
    origins: dict[str, Path] = {}
    for path in sorted(root.rglob("*.yaml")):
        document = load_yaml(path)
        for record in iter_records(document):
            for key in OBJECT_ID_FIELDS:
                value = record.get(key)
                if isinstance(value, str):
                    if value in registry:
                        raise AssertionError(f"duplicate stable id: {value}")
                    registry[value] = record
                    origins[value] = path
    for authority_root in (ROOT / "contracts", ROOT / "policies"):
        for path in sorted(authority_root.rglob("*.yaml")):
            try:
                record = load_yaml(path)
            except yaml.YAMLError:
                continue
            if not isinstance(record, dict):
                continue
            authority_id = record.get("contract_id") or record.get("policy_id")
            version = record.get("contract_version") or record.get("policy_version") or record.get("version")
            if not isinstance(authority_id, str) or not isinstance(version, int):
                continue
            compatibility = record.get("compatibility")
            historical_versions = (
                compatibility.get("historical_read_contract_versions", [])
                if isinstance(compatibility, dict)
                else []
            )
            readable_versions = {version, *historical_versions}
            aliases = [authority_id, *(f"{authority_id}@{item}" for item in sorted(readable_versions))]
            for alias in aliases:
                if alias in registry:
                    raise AssertionError(f"duplicate authority alias: {alias}")
                registry[alias] = record
                origins[alias] = path
            if authority_id == "project-governance-routing":
                fragment = f"{authority_id}@{version}#route_input_required_fields"
                registry[fragment] = record
                origins[fragment] = path
    return registry, origins


def iter_refs(value: Any) -> Iterable[tuple[str, str]]:
    if isinstance(value, dict):
        for key, child in value.items():
            if key.endswith("_ref") and isinstance(child, str):
                yield key, child
            elif key.endswith("_refs") and isinstance(child, list):
                for ref in child:
                    if isinstance(ref, str):
                        yield key, ref
            yield from iter_refs(child)
    elif isinstance(value, list):
        for child in value:
            yield from iter_refs(child)


def validate_reference_types_and_resolution(value: Any, registry: dict[str, dict[str, Any]]) -> None:
    if isinstance(value, dict):
        for key, child in value.items():
            if key.endswith("_ref"):
                if not isinstance(child, str):
                    raise ValueError(f"{key} must be a string reference")
                if child not in registry:
                    raise ValueError(f"unresolved reference: {key}={child}")
            elif key.endswith("_refs"):
                if not isinstance(child, list) or not all(isinstance(ref, str) for ref in child):
                    raise ValueError(f"{key} must be a list of string references")
                unresolved = [ref for ref in child if ref not in registry]
                if unresolved:
                    raise ValueError(f"unresolved references: {key}={unresolved}")
            validate_reference_types_and_resolution(child, registry)
    elif isinstance(value, list):
        for child in value:
            validate_reference_types_and_resolution(child, registry)


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def fixture_content_paths() -> tuple[Path, ...]:
    positive_files = [path for path in POSITIVE.rglob("*") if path.is_file()]
    negative_recovery = NEGATIVE / "missing-reopen-target" / "recovery.yaml"
    return tuple(sorted((*positive_files, negative_recovery), key=lambda path: path.relative_to(ROOT).as_posix()))


def fixture_tree_manifest_sha256(paths: Iterable[Path]) -> str:
    manifest = "".join(
        f"{sha256(path)}  {path.relative_to(ROOT).as_posix()}\n"
        for path in paths
    )
    return hashlib.sha256(manifest.encode("utf-8")).hexdigest()


def required_contract_fields(key: str) -> set[str]:
    contract = load_yaml(ACCEPTANCE_CONTRACT)
    return set(contract[key])


def canonical_object_hash(record: dict[str, Any], excludes: Iterable[str] = ("content_hash",)) -> str:
    payload = copy.deepcopy(record)
    for field in excludes:
        payload.pop(field, None)
    canonical = yaml.safe_dump(
        payload,
        allow_unicode=True,
        default_flow_style=False,
        sort_keys=True,
    ).encode("utf-8")
    return hashlib.sha256(canonical).hexdigest()


def bound_object_hash(
    ref: str,
    registry: dict[str, dict[str, Any]],
    origins: dict[str, Path],
) -> str:
    record = registry[ref]
    if "content_hash" in record:
        expected = canonical_object_hash(record)
        if record["content_hash"] != expected:
            raise ValueError(f"content hash mismatch for {ref}")
        return record["content_hash"]
    return sha256(origins[ref])


def assert_hash_pairs(
    refs: Any,
    hashes: Any,
    registry: dict[str, dict[str, Any]],
    origins: dict[str, Path],
    label: str,
) -> None:
    if not isinstance(refs, list) or not refs:
        raise ValueError(f"{label} refs must be non-empty")
    if not isinstance(hashes, list) or len(refs) != len(hashes):
        raise ValueError(f"{label} refs/hashes cardinality mismatch")
    for ref, digest in zip(refs, hashes, strict=True):
        if ref not in registry or not isinstance(digest, str):
            raise ValueError(f"{label} contains unresolved or invalid binding")
        if digest != bound_object_hash(ref, registry, origins):
            raise ValueError(f"{label} hash mismatch for {ref}")


def validate_run_evidence_contracts(
    registry: dict[str, dict[str, Any]],
    origins: dict[str, Path],
    contract: dict[str, Any],
) -> None:
    run_ids = (
        "RUN-FIX-SUCCESS-001",
        "RUN-FIX-FAILED-001",
        "RUN-FIX-RESUMED-001",
        "RUN-FIX-REVIEW-001",
        "RUN-FIX-CONTROL-VERIFY-001",
    )
    evidence_bindings = {
        "EVIDENCE-FIX-SUCCESS-001": ("RUN-FIX-SUCCESS-001", ["RUN-FIX-SUCCESS-001"]),
        "EVIDENCE-FIX-RESUMED-001": ("RUN-FIX-RESUMED-001", ["RUN-FIX-RESUMED-001"]),
        "EVIDENCE-FIX-CONTROL-001": ("RUN-FIX-CONTROL-VERIFY-001", ["CONTROL-FIX-001"]),
    }
    run_contract = contract["run"]
    evidence_contract = contract["evidence"]
    required_run_fields = set(run_contract["required_fields"])
    required_attempt_fields = set(run_contract["attempt_required_fields"])
    fingerprint_fields = (
        "input_fingerprints",
        "code_fingerprint",
        "dependency_fingerprint",
        "config_fingerprint",
        "model_fingerprints",
        "prompt_fingerprints",
        "context_fingerprints",
        "tool_fingerprints",
        "policy_fingerprints",
    )

    for run_id in run_ids:
        run = registry[run_id]
        missing = required_run_fields - set(run)
        if missing:
            raise ValueError(f"missing required Run fields: {run_id}={sorted(missing)}")
        if run["extends"] != "controlled_object_base/v1" or run["immutable"] is not True:
            raise ValueError(f"completed Run must extend the base and be immutable: {run_id}")
        if run["execution_outcome"] not in run_contract["enums"]["execution_outcome"]:
            raise ValueError(f"invalid Run execution_outcome: {run_id}")
        if run["semantic_result"] not in run_contract["enums"]["semantic_result"]:
            raise ValueError(f"invalid Run semantic_result: {run_id}")
        if run["review_mode"] not in run_contract["enums"]["review_mode"]:
            raise ValueError(f"invalid Run review_mode: {run_id}")
        for field in fingerprint_fields:
            value = run[field]
            if value in (None, "", []):
                raise ValueError(f"Run fingerprint is missing: {run_id}.{field}")
        if (
            run["route_decision_ref"] != "ROUTE-FIX-001"
            or run["control_set_ref"] != "CONTROL-FIX-001"
            or run["control_set_hash"] != registry["CONTROL-FIX-001"]["content_hash"]
            or run["workflow_ref"] != "WF-FIX-001"
            or run["workflow_version"] != 1
        ):
            raise ValueError(f"Run route/control/workflow binding mismatch: {run_id}")
        started_at = datetime.fromisoformat(run["started_at"])
        finished_at = datetime.fromisoformat(run["finished_at"])
        if not started_at.tzinfo or not finished_at.tzinfo or finished_at < started_at:
            raise ValueError(f"Run timestamps are invalid: {run_id}")
        attempts = run["attempt_manifest"]
        if not isinstance(attempts, list) or not attempts:
            raise ValueError(f"attempt manifest must be non-empty: {run_id}")
        attempt_ids = []
        for attempt in attempts:
            if required_attempt_fields - set(attempt):
                raise ValueError(f"attempt manifest entry is incomplete: {run_id}")
            if attempt["timeout_status"] not in run_contract["attempt_enums"]["timeout_status"]:
                raise ValueError(f"attempt timeout status is invalid: {run_id}")
            if attempt["output_status"] not in run_contract["attempt_enums"]["output_status"]:
                raise ValueError(f"attempt output status is invalid: {run_id}")
            attempt_id = attempt["attempt_id"]
            if attempt_id not in registry or registry[attempt_id] != attempt:
                raise ValueError(f"attempt_id is unresolved: {attempt_id}")
            attempt_ids.append(attempt_id)
        if len(attempt_ids) != len(set(attempt_ids)):
            raise ValueError(f"attempt manifest contains duplicate attempt IDs: {run_id}")

        checkpoint = run["checkpoint"]
        if isinstance(checkpoint, dict):
            missing_checkpoint = set(run_contract["checkpoint_required_fields"]) - set(checkpoint)
            if missing_checkpoint:
                raise ValueError(f"checkpoint is incomplete: {run_id}")
            if checkpoint["content_hash"] != canonical_object_hash(checkpoint):
                raise ValueError(f"checkpoint content hash mismatch: {run_id}")
        elif checkpoint is not None and checkpoint not in registry:
            raise ValueError(f"checkpoint reference is unresolved: {run_id}")

    failed = registry["RUN-FIX-FAILED-001"]
    if (
        failed["status"] != "failed"
        or failed["execution_outcome"] != "failure"
        or failed["semantic_result"] != "failed"
        or failed["exit_code"] == 0
    ):
        raise ValueError("failed Run history is inconsistent")
    resumed = registry["RUN-FIX-RESUMED-001"]
    if (
        resumed.get("resumes_run_ref") != failed["run_id"]
        or resumed.get("checkpoint_ref") != failed["checkpoint"]["checkpoint_id"]
        or resumed["run_id"] == failed["run_id"]
    ):
        raise ValueError("resumed Run must be a new Run bound to failed Run checkpoint")
    if registry["RUN-FIX-REVIEW-001"]["review_mode"] != "independent_ai_review":
        raise ValueError("review Run must use independent_ai_review mode")
    if registry["RUN-FIX-CONTROL-VERIFY-001"].get("run_kind") != "control_set_verification":
        raise ValueError("control verification Run has invalid run_kind")

    required_evidence_fields = set(evidence_contract["required_fields"])
    required_criterion_fields = set(evidence_contract["criterion_result_required_fields"])
    critical_evidence_refs = {
        *registry["VERDICT-FIX-001"]["evidence_refs"],
        *registry["CONTROL-FIX-001"]["base_profile_implementation_evidence_refs"],
    }
    for evidence_id, (run_id, subject_refs) in evidence_bindings.items():
        evidence = registry[evidence_id]
        missing = required_evidence_fields - set(evidence)
        if missing:
            raise ValueError(f"missing required Evidence fields: {evidence_id}={sorted(missing)}")
        if evidence["extends"] != "controlled_object_base/v1" or "status" in evidence:
            raise ValueError(f"Evidence must use authoritative verification/stale axes: {evidence_id}")
        if evidence["verification_status"] != "verified":
            raise ValueError("Evidence verification_status must be verified")
        if evidence["stale_status"] != "fresh":
            raise ValueError("Evidence stale_status must be fresh")
        if evidence_id in critical_evidence_refs and not evidence["criterion_results"]:
            raise ValueError("critical Evidence requires non-empty criterion results")
        if evidence["proof_level"] not in PROOF_ORDER:
            raise ValueError(f"Evidence proof level is unknown: {evidence_id}")
        if not evidence["content_and_environment_fingerprints"]:
            raise ValueError(f"Evidence fingerprints are missing: {evidence_id}")
        captured_at = datetime.fromisoformat(evidence["captured_at"])
        expires_at = datetime.fromisoformat(evidence["expires_at"])
        if not captured_at.tzinfo or not expires_at.tzinfo or not captured_at < expires_at:
            raise ValueError(f"Evidence timestamps are invalid: {evidence_id}")
        expected_subject_hash = bound_object_hash(subject_refs[0], registry, origins)
        if (
            evidence["run_ref"] != run_id
            or evidence["subject_refs"] != subject_refs
            or evidence["subject_hash"] != expected_subject_hash
        ):
            raise ValueError("Evidence subject or Run binding mismatch")
        run_attempt_ids = [item["attempt_id"] for item in registry[run_id]["attempt_manifest"]]
        if evidence_id == "EVIDENCE-FIX-CONTROL-001":
            control_attempt_refs = [
                item["attempt_id"]
                for item in registry[run_id]["attempt_manifest"]
                if item.get("attempt_kind") == "control_verification"
            ]
            raw_refs = [
                ref
                for criterion in evidence["criterion_results"]
                for ref in criterion.get("raw_evidence_refs", [])
            ]
            if (
                control_attempt_refs != run_attempt_ids
                or evidence["included_attempt_refs"] != control_attempt_refs
                or evidence["artifact_refs"] != control_attempt_refs
                or raw_refs != control_attempt_refs
            ):
                raise ValueError("control Evidence must use control verification attempt")
        if evidence["included_attempt_refs"] != run_attempt_ids:
            raise ValueError(f"Evidence attempt coverage is incomplete: {evidence_id}")
        if any(ref not in registry for ref in evidence["included_attempt_refs"]):
            raise ValueError(f"Evidence attempt reference is unresolved: {evidence_id}")
        excluded_refs = []
        for exclusion in evidence["excluded_attempts_and_reasons"]:
            if not exclusion.get("attempt_ref") or not exclusion.get("reason"):
                raise ValueError(f"Evidence attempt exclusion lacks reason: {evidence_id}")
            excluded_refs.append(exclusion["attempt_ref"])
        if set(evidence["included_attempt_refs"]) | set(excluded_refs) != set(run_attempt_ids):
            raise ValueError(f"Evidence selection does not cover Run attempts: {evidence_id}")
        for criterion in evidence["criterion_results"]:
            if required_criterion_fields - set(criterion):
                raise ValueError(f"Evidence criterion result is incomplete: {evidence_id}")
            if criterion["result"] not in evidence_contract["enums"]["criterion_result"]:
                raise ValueError(f"Evidence criterion result is invalid: {evidence_id}")
            if criterion["criterion_ref"] not in registry or any(
                ref not in registry for ref in criterion["raw_evidence_refs"]
            ):
                raise ValueError(f"Evidence criterion references are unresolved: {evidence_id}")


def validate_governance_bindings(
    verdict: dict[str, Any],
    registry: dict[str, dict[str, Any]],
    origins: dict[str, Path],
    as_of: datetime,
) -> None:
    route = registry[verdict["route_decision_ref"]]
    control = registry[verdict["control_set_ref"]]
    overlay = registry[verdict["overlay_status_snapshot_ref"]]
    review = registry[verdict["ai_review_verdict_refs"][0]]
    authorization = registry[verdict["approval_and_permission_snapshot_refs"][0]]

    for object_id, record in (
        ("ROUTE-FIX-001", route),
        ("CONTROL-FIX-001", control),
        ("AUTH-FIX-001", authorization),
        ("AI-REVIEW-FIX-001", review),
    ):
        required = set(load_yaml(GOVERNANCE_CONTRACTS[object_id])["required_fields"])
        missing = required - set(record)
        if missing:
            raise ValueError(f"{object_id} missing required fields: {sorted(missing)}")

    control_contract = load_yaml(GOVERNANCE_CONTRACTS["CONTROL-FIX-001"])
    if control_contract["hash_policy"]["canonicalization"] != "canonical-yaml-v1":
        raise ValueError("unsupported control-set canonicalization")
    if control["content_hash"] != canonical_object_hash(
        control,
        control_contract["hash_policy"]["excludes"],
    ):
        raise ValueError("control set content hash mismatch")
    if control["base_governance_profile"] != "standard":
        raise ValueError("accepted fixture requires standard control set")
    required_categories = set(
        control_contract["base_profile_contracts"][control["base_governance_profile"]][
            "required_control_categories"
        ]
    )
    if set(control["base_control_refs_by_category"]) != required_categories:
        raise ValueError("control categories must exactly match selected base profile contract")
    if control["base_profile_implementation_status"] != "implemented":
        raise ValueError("control set base profile must be implemented")
    if not control["base_profile_implementation_evidence_refs"]:
        raise ValueError("implemented control set requires implementation evidence")
    for evidence_ref in control["base_profile_implementation_evidence_refs"]:
        evidence = registry[evidence_ref]
        if evidence.get("evidence_id") != evidence_ref:
            raise ValueError("control implementation evidence must resolve to an independent Evidence")
        if evidence.get("verification_status") != "verified" or evidence.get("stale_status") != "fresh":
            raise ValueError("control implementation evidence must be verified and fresh")
        if evidence.get("subject_refs") != [control["control_set_id"]]:
            raise ValueError("control implementation evidence does not exactly bind control set subject")
        if evidence.get("subject_hash") != control["content_hash"]:
            raise ValueError("control implementation evidence subject hash mismatch")
        evidence_run = registry[evidence.get("run_ref")]
        if evidence_run.get("run_kind") != "control_set_verification":
            raise ValueError("control implementation evidence requires control verification Run")
        if (
            evidence.get("scope") != verdict["subject_and_scope"]
            or evidence.get("environment") != verdict["environment_and_input_class"]
        ):
            raise ValueError("control implementation evidence scope or environment mismatch")
        if evidence.get("proof_level") not in PROOF_ORDER:
            raise ValueError("control implementation evidence has unknown proof level")
    authority_refs = []
    for refs in control["base_control_refs_by_category"].values():
        if not refs or any(ref not in registry for ref in refs):
            raise ValueError("standard control categories require non-empty resolvable refs")
        authority_refs.extend(refs)
        if any(origins[ref].relative_to(ROOT).parts[0] not in {"contracts", "policies"} for ref in refs):
            raise ValueError("control category must reference repository authority, not fixture object")
    if len(set(authority_refs)) < 8:
        raise ValueError("control categories reuse a weak placeholder instead of real authorities")

    if route["base_governance_profile"] != "standard":
        raise ValueError("route must select standard base governance profile")
    if route["control_set_ref"] != control["control_set_id"]:
        raise ValueError("route/control mismatch")
    if route["control_set_hash"] != control["content_hash"]:
        raise ValueError("route/control hash mismatch")
    expected_policy_ref = "project-governance-routing@1"
    expected_input_ref = f"{expected_policy_ref}#route_input_required_fields"
    if route["route_input_contract_ref"] != expected_input_ref or route["routing_policy_ref"] != expected_policy_ref:
        raise ValueError("route must pin the repository routing policy authority")
    assert_hash_pairs(
        [route["route_input_contract_ref"], route["routing_policy_ref"]],
        [route["route_input_contract_hash"], route["routing_policy_hash"]],
        registry,
        origins,
        "route authority",
    )
    policy = registry[expected_policy_ref]
    required_inputs = set(policy["route_input_required_fields"])
    if set(route["route_inputs"]) != required_inputs:
        raise ValueError("route inputs must exactly cover pinned policy required fields")
    for field, enum_name in policy["route_input_schema"].items():
        if field == "every_field_may_explicitly_use":
            continue
        value = route["route_inputs"][field]
        if value == policy["enums"]["unknown_value"]:
            raise ValueError("unknown route input blocks accepted claim")
        if value not in policy["enums"][enum_name]:
            raise ValueError(f"invalid route input enum: {field}={value}")
    required_overlay_policies = policy["required_overlays"]
    if set(route["overlays"]) != set(required_overlay_policies):
        raise ValueError("route overlays must exactly cover pinned policy overlays")
    required_overlay_fields = set(
        load_yaml(GOVERNANCE_CONTRACTS["ROUTE-FIX-001"])["overlay_required_fields"]
    )
    for overlay_id, overlay_state in route["overlays"].items():
        if set(overlay_state) != required_overlay_fields:
            raise ValueError(f"route overlay fields do not match contract: {overlay_id}")
        required = overlay_state["required"]
        if required == "unknown":
            raise ValueError(f"required overlay is unknown: {overlay_id}")
        derived_required = derive_overlay_requirement(
            route["route_inputs"],
            required_overlay_policies[overlay_id],
        )
        if required is not derived_required:
            raise ValueError(f"derived overlay requirement mismatch: {overlay_id}")
        if required is True and (
            overlay_state["selected"] is not True
            or overlay_state["enabled"] is not True
            or overlay_state["implementation_status"] != "implemented"
            or overlay_state["verification_status"] != "verified"
        ):
            raise ValueError(f"required overlay is disabled: {overlay_id}")
        if overlay_state["enabled"] is True:
            authorization_ref = overlay_state["authorization_snapshot_ref"]
            activation_verdict_ref = overlay_state["overlay_activation_verdict_ref"]
            if (
                overlay_state["selected"] is not True
                or overlay_state["implementation_status"] != "implemented"
                or overlay_state["verification_status"] != "verified"
                or not isinstance(authorization_ref, str)
                or authorization_ref not in registry
                or authorization_ref != authorization["authorization_snapshot_id"]
                or not isinstance(activation_verdict_ref, str)
                or activation_verdict_ref not in registry
            ):
                raise ValueError(f"enabled overlay invariant is incomplete: {overlay_id}")
            overlay_authorization = registry[authorization_ref]
            if (
                overlay_authorization.get("verification_status") != "verified"
                or overlay_authorization.get("revocation_status") != "active"
                or overlay_authorization.get("route_decision_ref") != route["route_decision_id"]
                or overlay_authorization.get("control_set_ref") != control["control_set_id"]
                or overlay_authorization.get("control_set_hash") != control["content_hash"]
                or not (
                    datetime.fromisoformat(overlay_authorization["valid_from"])
                    <= as_of
                    < datetime.fromisoformat(overlay_authorization["expires_at"])
                )
            ):
                raise ValueError(f"enabled overlay authorization is invalid: {overlay_id}")
            activation_verdict = registry[activation_verdict_ref]
            if (
                activation_verdict.get("decision") != "accepted"
                or activation_verdict.get("overlay_id") != overlay_id
                or activation_verdict.get("route_v1_ref") != route["route_decision_id"]
                or activation_verdict.get("route_v1_hash")
                != bound_object_hash(route["route_decision_id"], registry, origins)
                or activation_verdict.get("control_set_ref") != control["control_set_id"]
                or activation_verdict.get("control_set_hash") != control["content_hash"]
                or activation_verdict.get("authorization_snapshot_ref") != authorization_ref
            ):
                raise ValueError(f"enabled overlay activation verdict is invalid: {overlay_id}")

    if overlay["route_decision_ref"] != route["route_decision_id"]:
        raise ValueError("overlay snapshot route mismatch")
    if overlay["route_decision_hash"] != bound_object_hash(route["route_decision_id"], registry, origins):
        raise ValueError("overlay snapshot route hash mismatch")
    if overlay["control_set_ref"] != control["control_set_id"] or overlay["control_set_hash"] != control["content_hash"]:
        raise ValueError("overlay snapshot control binding mismatch")
    bound_object_hash(overlay["overlay_status_snapshot_id"], registry, origins)

    if authorization["content_hash"] != canonical_object_hash(authorization):
        raise ValueError("authorization content hash mismatch")
    if authorization["verification_status"] != "verified":
        raise ValueError("permission snapshot must be verified")
    if authorization["revocation_status"] != "active":
        raise ValueError("permission snapshot is revoked or expired")
    decided_at = datetime.fromisoformat(verdict["decided_at"])
    if not (
        datetime.fromisoformat(authorization["valid_from"])
        <= decided_at
        <= as_of
        < datetime.fromisoformat(authorization["expires_at"])
    ):
        raise ValueError("permission snapshot expired")
    if not authorization["actor_bindings"] or not authorization["verification_refs"]:
        raise ValueError("verified permission requires actor and verification bindings")
    for binding in authorization["actor_bindings"]:
        principal_ref = binding.get("principal_ref")
        if principal_ref not in registry:
            raise ValueError("actor binding principal is unresolved")
        principal = registry[principal_ref]
        if principal.get("principal_status") != "verified_fixture":
            raise ValueError("actor binding principal is not verified")
        if principal.get("actor_id") != binding.get("actor_id"):
            raise ValueError("actor_id and principal binding are inconsistent")
    assert_hash_pairs(
        authorization["capability_grant_refs"],
        authorization["capability_grant_hashes"],
        registry,
        origins,
        "capability grant",
    )
    grant = registry[authorization["capability_grant_refs"][0]]
    if grant.get("status") != "active" or not (
        grant.get("project_id") == authorization["project_id"]
        and grant.get("route_decision_ref") == route["route_decision_id"]
        and grant.get("control_set_ref") == control["control_set_id"]
        and grant.get("principal_ref") == authorization["actor_bindings"][0]["principal_ref"]
    ):
        raise ValueError("capability grant binding is invalid")
    if not (
        datetime.fromisoformat(grant["valid_from"])
        <= decided_at
        <= as_of
        < datetime.fromisoformat(grant["expires_at"])
    ):
        raise ValueError("capability grant expired")
    for ref in (*authorization["approval_ticket_refs"], *authorization["secret_lease_refs"]):
        record = registry[ref]
        if record.get("status") != "active" or record.get("project_id") != authorization["project_id"]:
            raise ValueError("ticket or lease binding is invalid")
    if authorization["route_decision_ref"] != route["route_decision_id"]:
        raise ValueError("authorization route mismatch")
    if authorization["route_decision_hash"] != bound_object_hash(route["route_decision_id"], registry, origins):
        raise ValueError("authorization route hash mismatch")
    if authorization["control_set_ref"] != control["control_set_id"] or authorization["control_set_hash"] != control["content_hash"]:
        raise ValueError("authorization control mismatch")
    if authorization["signature_ref"] not in registry:
        raise ValueError("authorization signature unresolved")
    authorization_signature = registry[authorization["signature_ref"]]
    if (
        authorization_signature.get("signed_subject_ref") != authorization["authorization_snapshot_id"]
        or authorization_signature.get("signer") != authorization["created_by"]
    ):
        raise ValueError("authorization signature misbinding")

    if review["decision"] != "allow":
        raise ValueError("accepted verdict requires allow AI review")
    rewrite_attempt = review["rewrite_attempt"]
    max_rewrite_attempts = review["max_rewrite_attempts"]
    if (
        not isinstance(rewrite_attempt, int)
        or isinstance(rewrite_attempt, bool)
        or not isinstance(max_rewrite_attempts, int)
        or isinstance(max_rewrite_attempts, bool)
        or max_rewrite_attempts < 0
        or not 0 <= rewrite_attempt <= max_rewrite_attempts
    ):
        raise ValueError("AI rewrite attempt is out of bounds")
    if review["decision"] != "blocked" and rewrite_attempt >= max_rewrite_attempts:
        raise ValueError("rewrite limit requires blocked decision")
    if review["subject_hash"] != bound_object_hash(review["subject_ref"], registry, origins):
        raise ValueError("AI review subject hash mismatch")
    if review["rule_set_hash"] != bound_object_hash(review["rule_set_ref"], registry, origins):
        raise ValueError("AI review rule hash mismatch")
    rule_set = registry[review["rule_set_ref"]]
    if rule_set.get("status") != "active" or rule_set.get("freshness") != "fresh":
        raise ValueError("AI review rule set must be active and fresh")
    if rule_set.get("scope") != verdict["subject_and_scope"]:
        raise ValueError("AI review rule scope mismatch")
    if review["generator_run_ref"] == review["review_run_ref"]:
        raise ValueError("AI review run must be independent from generator run")
    if review.get("generator_execution_node_ref") == review["reviewer_execution_node_ref"]:
        raise ValueError("AI review execution node must be independent")
    if not review["rule_results"] or any(result.get("result") != "passed" for result in review["rule_results"]):
        raise ValueError("allow AI review requires non-empty passed rule results")
    rule_ids = {rule.get("rule_id") for rule in rule_set.get("rules", [])}
    applicable_blocking_rule_ids = {
        rule.get("rule_id")
        for rule in rule_set.get("rules", [])
        if rule.get("severity") == "blocking" and rule.get("applicable", True) is True
    }
    result_rule_ids = {result.get("rule_ref") for result in review["rule_results"]}
    if result_rule_ids != applicable_blocking_rule_ids:
        raise ValueError("applicable blocking rules must be exactly covered by review results")
    for result in review["rule_results"]:
        if result.get("rule_ref") not in rule_ids or not result.get("evidence_refs"):
            raise ValueError("AI review rule result lacks rule or evidence basis")
        if any(ref not in registry for ref in result["evidence_refs"]):
            raise ValueError("AI review rule result evidence is unresolved")
    assert_hash_pairs(review["evidence_refs"], review["evidence_hashes"], registry, origins, "AI review evidence")

    criterion_results = []
    for evidence_ref in verdict["evidence_refs"]:
        evidence = registry[evidence_ref]
        if evidence.get("verification_status") != "verified" or evidence.get("stale_status") != "fresh":
            raise ValueError("verdict evidence must be verified and fresh")
        if evidence.get("subject_refs") != verdict["subject_refs"]:
            raise ValueError("verdict evidence subject mismatch")
        criterion_results.extend(evidence.get("criterion_results", []))
    if not criterion_results or any(result.get("result") != "passed" for result in criterion_results):
        raise ValueError("all acceptance criteria must be passed")
    if {result.get("criterion_ref") for result in criterion_results} != set(verdict["criteria_refs"]):
        raise ValueError("criterion results must exactly cover verdict criteria")
    if verdict["subject_refs"] != [review["subject_ref"]]:
        raise ValueError("AI review subject must exactly match verdict subject")
    if review["evidence_refs"] != verdict["evidence_refs"]:
        raise ValueError("AI review evidence must exactly match verdict evidence")

    generator_run = registry[review["generator_run_ref"]]
    review_run = registry[review["review_run_ref"]]
    if review_run.get("run_kind") != "independent_ai_review":
        raise ValueError("review_run must be an explicit independent AI review Run")
    if review_run.get("execution_node_ref") != review["reviewer_execution_node_ref"]:
        raise ValueError("review Run node binding mismatch")
    if generator_run.get("execution_node_ref") != review.get("generator_execution_node_ref"):
        raise ValueError("generator Run node binding mismatch")
    review_context = review_run.get("prompt_context", {})
    generator_context = generator_run.get("prompt_context", {})
    if (
        review_context.get("role") != "independent_reviewer"
        or not isinstance(review_context.get("attempt"), int)
        or review_context.get("attempt", 0) < 1
        or review_context == generator_context
    ):
        raise ValueError("reviewer prompt/context/role/attempt is not separated")

    verdict_signature = registry[verdict["signature_ref"]]
    if (
        verdict_signature.get("signed_subject_ref") != verdict["verdict_id"]
        or verdict_signature.get("signer") != verdict["decided_by"]
    ):
        raise ValueError("verdict signature misbinding")


def validate_acceptance_bundle(
    verdict: dict[str, Any],
    claim: dict[str, Any],
    registry: dict[str, dict[str, Any]],
    origins: dict[str, Path],
    as_of: datetime | None = None,
) -> None:
    as_of = as_of or datetime.now(timezone.utc)
    if as_of.tzinfo is None:
        raise ValueError("as_of must be timezone-aware")
    missing_verdict = required_contract_fields("acceptance_verdict_required_fields") - set(verdict)
    missing_claim = required_contract_fields("completion_claim_required_fields") - set(claim)
    if missing_verdict or missing_claim:
        raise ValueError(f"missing required fields: verdict={sorted(missing_verdict)} claim={sorted(missing_claim)}")

    validate_reference_types_and_resolution(verdict, registry)
    validate_reference_types_and_resolution(claim, registry)
    for field in (
        "subject_refs",
        "criteria_refs",
        "evidence_refs",
        "evidence_hashes",
        "ai_review_verdict_refs",
        "ai_review_verdict_hashes",
        "approval_and_permission_snapshot_refs",
        "approval_and_permission_snapshot_hashes",
    ):
        if not isinstance(verdict[field], list) or not verdict[field]:
            raise ValueError(f"accepted verdict requires non-empty {field}")
    if verdict["decision"] != "accepted":
        raise ValueError("fixture verdict must be accepted")
    if claim["claim_status"] != "issued":
        raise ValueError("fixture claim must be issued")

    assert_hash_pairs(verdict["evidence_refs"], verdict["evidence_hashes"], registry, origins, "evidence")
    assert_hash_pairs(
        verdict["ai_review_verdict_refs"],
        verdict["ai_review_verdict_hashes"],
        registry,
        origins,
        "AI review",
    )
    assert_hash_pairs(
        verdict["approval_and_permission_snapshot_refs"],
        verdict["approval_and_permission_snapshot_hashes"],
        registry,
        origins,
        "permission snapshot",
    )
    assert_hash_pairs(claim["evidence_refs"], claim["evidence_hashes"], registry, origins, "claim evidence")
    verdict_evidence_pairs = set(zip(verdict["evidence_refs"], verdict["evidence_hashes"], strict=True))
    claim_evidence_pairs = set(zip(claim["evidence_refs"], claim["evidence_hashes"], strict=True))
    if not claim_evidence_pairs.issubset(verdict_evidence_pairs):
        raise ValueError("claim evidence pairs expand verdict")

    for ref_field, hash_field in (
        ("overlay_status_snapshot_ref", "overlay_status_snapshot_hash"),
        ("control_set_ref", "control_set_hash"),
    ):
        ref = verdict[ref_field]
        if verdict[hash_field] != bound_object_hash(ref, registry, origins):
            raise ValueError(f"verdict {hash_field} mismatch")

    exact_bindings = (
        "requirement_baseline_id",
        "route_decision_ref",
        "overlay_status_snapshot_ref",
        "overlay_status_snapshot_hash",
        "control_set_ref",
        "control_set_hash",
        "ai_review_verdict_refs",
        "ai_review_verdict_hashes",
        "approval_and_permission_snapshot_refs",
        "approval_and_permission_snapshot_hashes",
    )
    for field in exact_bindings:
        if claim[field] != verdict[field]:
            raise ValueError(f"claim binding differs from verdict: {field}")

    if claim["verdict_ref"] != verdict["verdict_id"]:
        raise ValueError("claim must reference its accepted verdict")
    if not set(claim["subject_refs"]).issubset(verdict["subject_refs"]):
        raise ValueError("claim subject expands verdict")
    if claim["scope"] != verdict["subject_and_scope"]:
        raise ValueError("claim scope expands verdict")
    if claim["environment"] != verdict["environment_and_input_class"]:
        raise ValueError("claim environment differs from verdict")
    if PROOF_ORDER.index(claim["proof_level"]) > PROOF_ORDER.index(verdict["claim_ceiling"]):
        raise ValueError("claim proof expands verdict ceiling")
    if not isinstance(claim["verification_commands"], list) or not claim["verification_commands"]:
        raise ValueError("issued claim requires verification_commands")

    decided_at = datetime.fromisoformat(verdict["decided_at"])
    verdict_expires_at = datetime.fromisoformat(verdict["expires_at"])
    issued_at = datetime.fromisoformat(claim["issued_at"])
    claim_expires_at = datetime.fromisoformat(claim["expires_at"])
    if not decided_at.tzinfo or not issued_at.tzinfo:
        raise ValueError("decision and issue timestamps must be timezone-aware")
    if not (decided_at <= issued_at < claim_expires_at <= verdict_expires_at):
        raise ValueError("claim requires accepted unexpired verdict")

    if not (decided_at <= as_of < verdict_expires_at and issued_at <= as_of < claim_expires_at):
        raise ValueError("accepted verdict or issued claim expired at validation time")

    validate_governance_bindings(verdict, registry, origins, as_of)

    proof_levels = [verdict["claim_ceiling"]]
    review = registry[verdict["ai_review_verdict_refs"][0]]
    proof_levels.append(review["claim_ceiling"])
    for run_ref in claim["subject_refs"]:
        run = registry[run_ref]
        proof_levels.append(run["proof_level"])
        workflow = registry[run["workflow_ref"]]
        proof_levels.append(workflow["claim_ceiling"])
    for evidence_ref in {*verdict["evidence_refs"], *claim["evidence_refs"]}:
        proof_levels.append(registry[evidence_ref]["proof_level"])
    control = registry[verdict["control_set_ref"]]
    for evidence_ref in control["base_profile_implementation_evidence_refs"]:
        proof_levels.append(registry[evidence_ref]["proof_level"])
    for run_ref in {review["generator_run_ref"], review["review_run_ref"]}:
        proof_levels.append(registry[run_ref]["proof_level"])
    try:
        effective_ceiling = min(proof_levels, key=PROOF_ORDER.index)
    except ValueError as exc:
        raise ValueError("critical path contains unknown proof level") from exc
    if PROOF_ORDER.index(claim["proof_level"]) > PROOF_ORDER.index(effective_ceiling):
        raise ValueError("claim proof exceeds critical path ceiling")


def validate_recovery(recovery: dict[str, Any], registry: dict[str, dict[str, Any]]) -> None:
    reopen_target = recovery.get("reopen_target")
    if not isinstance(reopen_target, str) or not reopen_target:
        raise ValueError("recovery must fail closed when reopen_target is missing")

    failed = registry[recovery["failed_run_ref"]]
    resumed = registry[recovery["resumed_run_ref"]]
    checkpoint = registry[recovery["checkpoint_ref"]]
    new_evidence = registry[recovery["new_evidence_ref"]]

    if failed["status"] != "failed" or failed["immutable"] is not True:
        raise ValueError("failed run must remain immutable")
    if recovery.get("failed_run_mutation") != "forbidden":
        raise ValueError("failed run mutation must remain forbidden")
    if recovery["failure_stage"] != "S6" or reopen_target != "S4":
        raise ValueError("S6 contract failure must reopen S4")
    if checkpoint["status"] != "paused":
        raise ValueError("recovery checkpoint must record a pause")
    if resumed["run_id"] == failed["run_id"]:
        raise ValueError("resume must create a new run")
    if resumed["resumes_run_ref"] != failed["run_id"]:
        raise ValueError("resumed run must reference the original failed run")
    if resumed["checkpoint_ref"] != checkpoint["checkpoint_id"]:
        raise ValueError("resumed run must reference the paused checkpoint")
    if new_evidence["run_ref"] != resumed["run_id"]:
        raise ValueError("new Evidence must bind the new resumed Run")


class OperationalSpineFixtureTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.registry, cls.origins = build_registry(POSITIVE)

    def test_positive_registry_resolves_every_reference_and_closes_spine(self) -> None:
        self.assertIn("chain-package-contract@1", self.registry)
        self.assertIn("spec-package-contract@1", self.registry)
        unresolved = sorted(
            (key, ref)
            for path in sorted(POSITIVE.rglob("*.yaml"))
            for key, ref in iter_refs(load_yaml(path))
            if ref not in self.registry
        )
        self.assertEqual([], unresolved)

        required_ids = {
            "REQ-FIX-001",
            "CRITERION-FIX-001",
            "CHAIN-FIX-001",
            "SPEC-FIX-001",
            "TASK-FIX-001",
            "WF-FIX-001",
            "SKILL-FIX-001",
            "TOOL-FIX-001",
            "RUN-FIX-SUCCESS-001",
            "EVIDENCE-FIX-SUCCESS-001",
            "EVIDENCE-FIX-CONTROL-001",
            "RUN-FIX-REVIEW-001",
            "VERDICT-FIX-001",
            "CLAIM-FIX-001",
            "ROUTE-FIX-001",
            "OVERLAY-FIX-001",
            "CONTROL-FIX-001",
            "AI-REVIEW-FIX-001",
            "AUTH-FIX-001",
            "SIGNATURE-FIX-001",
            "BASELINE-FIX-001",
        }
        self.assertTrue(required_ids.issubset(self.registry))
        self.assertNotIn("PROJECT-FIX-001", self.registry, "project_id is context, not an object primary ID")
        for weak_authority in ("route-input-contract.yaml", "routing-policy.yaml", "control-authority.yaml"):
            self.assertFalse((POSITIVE / weak_authority).exists())

        chain = self.registry["CHAIN-FIX-001"]
        requirement = self.registry["REQ-FIX-001"]
        spec = self.registry["SPEC-FIX-001"]
        task = self.registry["TASK-FIX-001"]
        workflow = self.registry["WF-FIX-001"]
        run = self.registry["RUN-FIX-SUCCESS-001"]
        evidence = self.registry["EVIDENCE-FIX-SUCCESS-001"]
        verdict = self.registry["VERDICT-FIX-001"]
        claim = self.registry["CLAIM-FIX-001"]
        self.assertEqual(["CHAIN-FIX-001"], requirement["chain_refs"])
        self.assertEqual(["REQ-FIX-001"], chain["requirement_refs"])
        self.assertEqual(["SPEC-FIX-001"], chain["spec_refs"])
        self.assertEqual("CHAIN-FIX-001", spec["chain_ref"])
        self.assertEqual(["TASK-FIX-001"], spec["task_refs"])
        self.assertEqual("SPEC-FIX-001", task["spec_ref"])
        self.assertEqual(["TASK-FIX-001"], workflow["task_refs"])
        self.assertEqual("WF-FIX-001", task["workflow_ref"])
        self.assertEqual(["SKILL-FIX-001"], workflow["skill_refs"])
        self.assertEqual(["TOOL-FIX-001"], workflow["tool_refs"])
        self.assertEqual(["WF-FIX-001"], self.registry["SKILL-FIX-001"]["workflow_refs"])
        self.assertEqual(["WF-FIX-001"], self.registry["TOOL-FIX-001"]["workflow_refs"])
        self.assertEqual(
            [
                "RUN-FIX-SUCCESS-001",
                "RUN-FIX-FAILED-001",
                "RUN-FIX-RESUMED-001",
                "RUN-FIX-REVIEW-001",
                "RUN-FIX-CONTROL-VERIFY-001",
            ],
            workflow["run_refs"],
        )
        for run_id in workflow["run_refs"]:
            self.assertEqual("WF-FIX-001", self.registry[run_id]["workflow_ref"])
        self.assertEqual("WF-FIX-001", run["workflow_ref"])
        self.assertEqual("RUN-FIX-SUCCESS-001", evidence["run_ref"])
        self.assertEqual(["EVIDENCE-FIX-SUCCESS-001"], run["evidence_refs"])
        self.assertEqual(["VERDICT-FIX-001"], evidence["verdict_refs"])
        self.assertEqual(["EVIDENCE-FIX-SUCCESS-001"], verdict["evidence_refs"])
        self.assertEqual("VERDICT-FIX-001", claim["verdict_ref"])
        self.assertEqual(["CLAIM-FIX-001"], verdict["claim_refs"])

    def test_task_is_derived_from_spec_and_acceptance_criterion(self) -> None:
        requirement = self.registry["REQ-FIX-001"]
        self.assertIn("CRITERION-FIX-001", self.registry)
        criterion = self.registry["CRITERION-FIX-001"]
        spec = self.registry["SPEC-FIX-001"]
        task = self.registry["TASK-FIX-001"]

        self.assertEqual("REQ-FIX-001", criterion["requirement_ref"])
        self.assertEqual(["CRITERION-FIX-001"], requirement["acceptance_criterion_refs"])
        self.assertEqual(["CRITERION-FIX-001"], spec["acceptance_criterion_refs"])
        self.assertEqual(["CRITERION-FIX-001"], task["acceptance_criterion_refs"])
        self.assertEqual("SPEC-FIX-001", task["spec_ref"])

    def test_hash_subject_proof_and_scope_invariants(self) -> None:
        run = self.registry["RUN-FIX-SUCCESS-001"]
        evidence = self.registry["EVIDENCE-FIX-SUCCESS-001"]
        verdict = self.registry["VERDICT-FIX-001"]
        claim = self.registry["CLAIM-FIX-001"]

        self.assertEqual(8, len(PROOF_ORDER), "proof order must come from the GATES authority")

        self.assertEqual(sha256(self.origins[run["run_id"]]), evidence["subject_hash"])
        resumed_run = self.registry["RUN-FIX-RESUMED-001"]
        resumed_evidence = self.registry["EVIDENCE-FIX-RESUMED-001"]
        self.assertEqual(
            sha256(self.origins[resumed_run["run_id"]]),
            resumed_evidence["subject_hash"],
        )
        self.assertEqual(
            ["RUN-FIX-RESUMED-001"],
            resumed_evidence["subject_refs"],
        )
        evidence_hash = sha256(self.origins[evidence["evidence_id"]])
        self.assertNotEqual(
            self.origins[evidence["evidence_id"]],
            self.origins[resumed_evidence["evidence_id"]],
            "each Evidence must have an independently verifiable file hash",
        )
        self.assertEqual([evidence_hash], verdict["evidence_hashes"])
        self.assertEqual(["EVIDENCE-FIX-SUCCESS-001"], claim["evidence_refs"])
        self.assertEqual([evidence_hash], claim["evidence_hashes"])
        self.assertEqual(len(claim["evidence_refs"]), len(claim["evidence_hashes"]))
        self.assertTrue(set(claim["subject_refs"]).issubset(verdict["subject_refs"]))
        self.assertEqual("operational_spine_fixture_only", claim["scope"])
        for record in (run, resumed_run, evidence, resumed_evidence, verdict, claim):
            self.assertEqual("operational_spine_fixture_only", record["scope"])
            self.assertEqual("anonymous_fixture", record["environment"])
            self.assertEqual("fixture_runtime_proven", record["proof_level"])
            self.assertLessEqual(
                PROOF_ORDER.index(record["proof_level"]),
                PROOF_ORDER.index(verdict["proof_level_ceiling"]),
            )
        self.assertLessEqual(PROOF_ORDER.index(claim["proof_level"]), PROOF_ORDER.index(verdict["proof_level_ceiling"]))
        self.assertLessEqual(PROOF_ORDER.index(claim["proof_level"]), PROOF_ORDER.index("fixture_runtime_proven"))

    def test_chain_is_visible_to_c12_and_flowchart_governs_stable_id(self) -> None:
        chain = self.registry["CHAIN-FIX-001"]
        self.assertEqual("business_chain", chain.get("object_type"))
        self.assertEqual("p1", chain.get("priority"))
        self.assertIs(chain.get("cross_node"), False)
        self.assertIs(chain.get("multi_state"), False)
        self.assertIs(chain.get("authorization_or_data_boundary"), False)
        self.assertNotIn("chain_id", chain)

        diagram = (POSITIVE / "chain" / "diagrams" / "flowchart.md").read_text(encoding="utf-8")
        self.assertTrue(diagram.startswith("---\n"))
        frontmatter = yaml.safe_load(diagram.split("---", 2)[1])
        self.assertEqual("flowchart", frontmatter["diagram_type"])
        self.assertEqual("CHAIN-FIX-001", frontmatter["governs_object"])
        self.assertTrue(frontmatter["title"])
        self.assertTrue(frontmatter["description"])

    def test_recovery_preserves_failed_run_and_creates_new_resumed_evidence(self) -> None:
        validate_recovery(self.registry["RECOVERY-FIX-001"], self.registry)

    def test_verdict_and_claim_follow_authoritative_contract_and_invariants(self) -> None:
        verdict = self.registry["VERDICT-FIX-001"]
        claim = self.registry["CLAIM-FIX-001"]
        self.assertIn("AI-REVIEW-FIX-001", self.registry)
        self.assertEqual(
            ["EVIDENCE-FIX-CONTROL-001"],
            self.registry["CONTROL-FIX-001"]["base_profile_implementation_evidence_refs"],
        )
        self.assertEqual(
            ["CONTROL-FIX-001"],
            self.registry["EVIDENCE-FIX-CONTROL-001"]["subject_refs"],
        )
        self.assertEqual(
            "project-governance-routing@1#route_input_required_fields",
            self.registry["ROUTE-FIX-001"]["route_input_contract_ref"],
        )
        self.assertEqual(
            "project-governance-routing@1",
            self.registry["ROUTE-FIX-001"]["routing_policy_ref"],
        )
        self.assertEqual(
            set(),
            required_contract_fields("acceptance_verdict_required_fields") - set(verdict),
        )
        self.assertEqual(
            set(),
            required_contract_fields("completion_claim_required_fields") - set(claim),
        )
        validate_acceptance_bundle(verdict, claim, self.registry, self.origins)
        self.assertIn("content_hash", self.registry["AI-REVIEW-FIX-001"])
        success_evidence = self.registry["EVIDENCE-FIX-SUCCESS-001"]
        review = self.registry["AI-REVIEW-FIX-001"]
        review_run = self.registry[review["review_run_ref"]]
        generator_run = self.registry[review["generator_run_ref"]]
        self.assertEqual(["RUN-FIX-SUCCESS-001"], verdict["subject_refs"])
        self.assertEqual(verdict["subject_refs"], success_evidence["subject_refs"])
        self.assertEqual(["EVIDENCE-FIX-SUCCESS-001"], verdict["evidence_refs"])
        self.assertEqual("RUN-FIX-SUCCESS-001", review["subject_ref"])
        self.assertEqual("RUN-FIX-REVIEW-001", review["review_run_ref"])
        self.assertEqual("independent_ai_review", review_run["run_kind"])
        self.assertEqual(review["reviewer_execution_node_ref"], review_run["execution_node_ref"])
        self.assertEqual(review["generator_execution_node_ref"], generator_run["execution_node_ref"])
        self.assertNotEqual(review_run["prompt_context"], generator_run["prompt_context"])
        self.assertEqual("independent_reviewer", review_run["prompt_context"]["role"])
        self.assertGreaterEqual(review_run["prompt_context"]["attempt"], 1)

        for object_id, contract_path in GOVERNANCE_CONTRACTS.items():
            with self.subTest(object_id=object_id):
                self.assertIn(object_id, self.registry)
                required = set(load_yaml(contract_path)["required_fields"])
                self.assertEqual(set(), required - set(self.registry[object_id]))
        self.assertIn("review_verdict_id", self.registry["AI-REVIEW-FIX-001"])
        self.assertNotIn("ai_review_verdict_id", self.registry["AI-REVIEW-FIX-001"])

    def test_acceptance_and_recovery_tampering_fail_closed(self) -> None:
        verdict = self.registry["VERDICT-FIX-001"]
        claim = self.registry["CLAIM-FIX-001"]
        self.assertIn("AI-REVIEW-FIX-001", self.registry)

        tampered_verdict = copy.deepcopy(verdict)
        tampered_verdict["evidence_hashes"][0] = "0" * 64
        with self.assertRaisesRegex(ValueError, "hash mismatch"):
            validate_acceptance_bundle(tampered_verdict, claim, self.registry, self.origins)

        wrong_type_claim = copy.deepcopy(claim)
        wrong_type_claim["verdict_ref"] = ["VERDICT-FIX-001"]
        with self.assertRaisesRegex(ValueError, "must be a string reference"):
            validate_acceptance_bundle(verdict, wrong_type_claim, self.registry, self.origins)

        unresolved_claim = copy.deepcopy(claim)
        unresolved_claim["route_decision_ref"] = "ROUTE-MISSING"
        with self.assertRaisesRegex(ValueError, "unresolved reference"):
            validate_acceptance_bundle(verdict, unresolved_claim, self.registry, self.origins)

        expanded_scope_claim = copy.deepcopy(claim)
        expanded_scope_claim["scope"] = "production"
        with self.assertRaisesRegex(ValueError, "scope expands"):
            validate_acceptance_bundle(verdict, expanded_scope_claim, self.registry, self.origins)

        expanded_proof_claim = copy.deepcopy(claim)
        expanded_proof_claim["proof_level"] = "production_proof"
        with self.assertRaisesRegex(ValueError, "proof expands"):
            validate_acceptance_bundle(verdict, expanded_proof_claim, self.registry, self.origins)

        recovery = self.registry["RECOVERY-FIX-001"]
        mutation_allowed = copy.deepcopy(recovery)
        mutation_allowed["failed_run_mutation"] = "allowed"
        with self.assertRaisesRegex(ValueError, "mutation must remain forbidden"):
            validate_recovery(mutation_allowed, self.registry)

        resumed_same_run = copy.deepcopy(recovery)
        resumed_same_run["resumed_run_ref"] = "RUN-FIX-FAILED-001"
        with self.assertRaisesRegex(ValueError, "new run"):
            validate_recovery(resumed_same_run, self.registry)

        evidence_bound_old_run_registry = copy.deepcopy(self.registry)
        evidence_bound_old_run_registry["EVIDENCE-FIX-RESUMED-001"]["run_ref"] = "RUN-FIX-FAILED-001"
        with self.assertRaisesRegex(ValueError, "new Evidence"):
            validate_recovery(recovery, evidence_bound_old_run_registry)

    def test_governance_binding_tampering_fails_closed(self) -> None:
        verdict = self.registry["VERDICT-FIX-001"]
        claim = self.registry["CLAIM-FIX-001"]
        self.assertIn("AI-REVIEW-FIX-001", self.registry)
        self.assertIn("EVIDENCE-FIX-CONTROL-001", self.registry)

        bad_rule_hash_registry = copy.deepcopy(self.registry)
        bad_rule_hash_verdict = copy.deepcopy(verdict)
        bad_rule_hash_claim = copy.deepcopy(claim)
        bad_rule_review = bad_rule_hash_registry["AI-REVIEW-FIX-001"]
        bad_rule_review["rule_set_hash"] = "0" * 64
        bad_rule_review["content_hash"] = canonical_object_hash(bad_rule_review)
        bad_rule_hash_verdict["ai_review_verdict_hashes"] = [bad_rule_review["content_hash"]]
        bad_rule_hash_claim["ai_review_verdict_hashes"] = [bad_rule_review["content_hash"]]
        with self.assertRaisesRegex(ValueError, "rule hash mismatch"):
            validate_acceptance_bundle(
                bad_rule_hash_verdict,
                bad_rule_hash_claim,
                bad_rule_hash_registry,
                self.origins,
            )

        bad_subject_hash_registry = copy.deepcopy(self.registry)
        bad_subject_hash_verdict = copy.deepcopy(verdict)
        bad_subject_hash_claim = copy.deepcopy(claim)
        bad_subject_review = bad_subject_hash_registry["AI-REVIEW-FIX-001"]
        bad_subject_review["subject_hash"] = "0" * 64
        bad_subject_review["content_hash"] = canonical_object_hash(bad_subject_review)
        bad_subject_hash_verdict["ai_review_verdict_hashes"] = [bad_subject_review["content_hash"]]
        bad_subject_hash_claim["ai_review_verdict_hashes"] = [bad_subject_review["content_hash"]]
        with self.assertRaisesRegex(ValueError, "subject hash mismatch"):
            validate_acceptance_bundle(
                bad_subject_hash_verdict,
                bad_subject_hash_claim,
                bad_subject_hash_registry,
                self.origins,
            )

        for mutation, expected_error in (
            ({"expires_at": "2026-07-11T11:59:59+00:00"}, "permission snapshot expired"),
            ({"revocation_status": "revoked"}, "revoked or expired"),
        ):
            mutated_registry = copy.deepcopy(self.registry)
            mutated_verdict = copy.deepcopy(verdict)
            mutated_claim = copy.deepcopy(claim)
            authorization = mutated_registry["AUTH-FIX-001"]
            authorization.update(mutation)
            authorization["content_hash"] = canonical_object_hash(authorization)
            digest = authorization["content_hash"]
            mutated_verdict["approval_and_permission_snapshot_hashes"] = [digest]
            mutated_claim["approval_and_permission_snapshot_hashes"] = [digest]
            with self.assertRaisesRegex(ValueError, expected_error):
                validate_acceptance_bundle(mutated_verdict, mutated_claim, mutated_registry, self.origins)

        unimplemented_registry = copy.deepcopy(self.registry)
        unimplemented_verdict = copy.deepcopy(verdict)
        unimplemented_claim = copy.deepcopy(claim)
        control = unimplemented_registry["CONTROL-FIX-001"]
        control["base_profile_implementation_status"] = "partial"
        control["content_hash"] = canonical_object_hash(control)
        control_hash = control["content_hash"]
        unimplemented_verdict["control_set_hash"] = control_hash
        unimplemented_claim["control_set_hash"] = control_hash
        with self.assertRaisesRegex(ValueError, "must be implemented"):
            validate_acceptance_bundle(unimplemented_verdict, unimplemented_claim, unimplemented_registry, self.origins)

        failed_criterion_registry = copy.deepcopy(self.registry)
        failed_criterion_registry["EVIDENCE-FIX-SUCCESS-001"]["criterion_results"][0]["result"] = "failed"
        with self.assertRaisesRegex(ValueError, "criteria must be passed"):
            validate_acceptance_bundle(verdict, claim, failed_criterion_registry, self.origins)

        route_mismatch_registry = copy.deepcopy(self.registry)
        route_mismatch_registry["ROUTE-FIX-001"]["control_set_ref"] = "CONTROL-MISSING"
        with self.assertRaisesRegex(ValueError, "route/control mismatch"):
            validate_acceptance_bundle(verdict, claim, route_mismatch_registry, self.origins)

        unknown_route_registry = copy.deepcopy(self.registry)
        unknown_route_registry["ROUTE-FIX-001"]["route_inputs"]["uncertainty"] = "unknown"
        with self.assertRaisesRegex(ValueError, "unknown route input"):
            validate_acceptance_bundle(verdict, claim, unknown_route_registry, self.origins)

        signature_misbinding_registry = copy.deepcopy(self.registry)
        signature_misbinding_registry["AUTH-SIGNATURE-FIX-001"]["signed_subject_ref"] = "VERDICT-FIX-001"
        with self.assertRaisesRegex(ValueError, "authorization signature misbinding"):
            validate_acceptance_bundle(verdict, claim, signature_misbinding_registry, self.origins)

        expired_grant_registry = copy.deepcopy(self.registry)
        expired_grant_verdict = copy.deepcopy(verdict)
        expired_grant_claim = copy.deepcopy(claim)
        grant = expired_grant_registry["GRANT-FIX-001"]
        grant["expires_at"] = "2026-07-11T11:59:59+00:00"
        grant["content_hash"] = canonical_object_hash(grant)
        authorization = expired_grant_registry["AUTH-FIX-001"]
        authorization["capability_grant_hashes"] = [grant["content_hash"]]
        authorization["content_hash"] = canonical_object_hash(authorization)
        expired_grant_verdict["approval_and_permission_snapshot_hashes"] = [authorization["content_hash"]]
        expired_grant_claim["approval_and_permission_snapshot_hashes"] = [authorization["content_hash"]]
        with self.assertRaisesRegex(ValueError, "capability grant expired"):
            validate_acceptance_bundle(
                expired_grant_verdict,
                expired_grant_claim,
                expired_grant_registry,
                self.origins,
            )

        wrong_rule_scope_registry = copy.deepcopy(self.registry)
        wrong_rule_scope_verdict = copy.deepcopy(verdict)
        wrong_rule_scope_claim = copy.deepcopy(claim)
        rule_set = wrong_rule_scope_registry["RULE-SET-FIX-001"]
        rule_set["scope"] = "production"
        rule_set["content_hash"] = canonical_object_hash(rule_set)
        review = wrong_rule_scope_registry["AI-REVIEW-FIX-001"]
        review["rule_set_hash"] = rule_set["content_hash"]
        review["content_hash"] = canonical_object_hash(review)
        wrong_rule_scope_verdict["ai_review_verdict_hashes"] = [review["content_hash"]]
        wrong_rule_scope_claim["ai_review_verdict_hashes"] = [review["content_hash"]]
        with self.assertRaisesRegex(ValueError, "rule scope mismatch"):
            validate_acceptance_bundle(
                wrong_rule_scope_verdict,
                wrong_rule_scope_claim,
                wrong_rule_scope_registry,
                self.origins,
            )

    def test_coherent_control_principal_rule_and_claim_tampering_fails_closed(self) -> None:
        verdict = self.registry["VERDICT-FIX-001"]
        claim = self.registry["CLAIM-FIX-001"]

        with self.subTest(tamper="missing required control category"):
            registry = copy.deepcopy(self.registry)
            tampered_verdict = copy.deepcopy(verdict)
            tampered_claim = copy.deepcopy(claim)
            control = registry["CONTROL-FIX-001"]
            control["base_control_refs_by_category"].pop("typed_traceability")
            control["content_hash"] = canonical_object_hash(control)
            registry["ROUTE-FIX-001"]["control_set_hash"] = control["content_hash"]
            overlay = registry["OVERLAY-FIX-001"]
            overlay["control_set_hash"] = control["content_hash"]
            overlay["content_hash"] = canonical_object_hash(overlay)
            authorization = registry["AUTH-FIX-001"]
            authorization["control_set_hash"] = control["content_hash"]
            authorization["content_hash"] = canonical_object_hash(authorization)
            tampered_verdict["control_set_hash"] = control["content_hash"]
            tampered_claim["control_set_hash"] = control["content_hash"]
            tampered_verdict["overlay_status_snapshot_hash"] = overlay["content_hash"]
            tampered_claim["overlay_status_snapshot_hash"] = overlay["content_hash"]
            tampered_verdict["approval_and_permission_snapshot_hashes"] = [authorization["content_hash"]]
            tampered_claim["approval_and_permission_snapshot_hashes"] = [authorization["content_hash"]]
            with self.assertRaisesRegex(ValueError, "control categories must exactly match"):
                validate_acceptance_bundle(tampered_verdict, tampered_claim, registry, self.origins)

        with self.subTest(tamper="principal unverified"):
            registry = copy.deepcopy(self.registry)
            registry["PRINCIPAL-FIX-001"]["principal_status"] = "unverified_fixture"
            with self.assertRaisesRegex(ValueError, "principal is not verified"):
                validate_acceptance_bundle(verdict, claim, registry, self.origins)

        with self.subTest(tamper="uncovered blocking rule"):
            registry = copy.deepcopy(self.registry)
            tampered_verdict = copy.deepcopy(verdict)
            tampered_claim = copy.deepcopy(claim)
            rule_set = registry["RULE-SET-FIX-001"]
            rule_set["rules"].append(
                {
                    "rule_id": "RULE-FIX-UNREVIEWED-002",
                    "severity": "blocking",
                    "statement": "新增适用阻断规则必须被审核。",
                }
            )
            rule_set["content_hash"] = canonical_object_hash(rule_set)
            review = registry["AI-REVIEW-FIX-001"]
            review["rule_set_hash"] = rule_set["content_hash"]
            review["content_hash"] = canonical_object_hash(review)
            tampered_verdict["ai_review_verdict_hashes"] = [review["content_hash"]]
            tampered_claim["ai_review_verdict_hashes"] = [review["content_hash"]]
            with self.assertRaisesRegex(ValueError, "blocking rules must be exactly covered"):
                validate_acceptance_bundle(tampered_verdict, tampered_claim, registry, self.origins)

        with self.subTest(tamper="claim evidence pair expansion"):
            registry = copy.deepcopy(self.registry)
            origins = dict(self.origins)
            tampered_claim = copy.deepcopy(claim)
            extra_ref = "EVIDENCE-FIX-EXTRA-001"
            registry[extra_ref] = copy.deepcopy(registry["EVIDENCE-FIX-SUCCESS-001"])
            registry[extra_ref]["evidence_id"] = extra_ref
            origins[extra_ref] = origins["EVIDENCE-FIX-SUCCESS-001"]
            tampered_claim["evidence_refs"].append(extra_ref)
            tampered_claim["evidence_hashes"].append(bound_object_hash(extra_ref, registry, origins))
            with self.assertRaisesRegex(ValueError, "claim evidence pairs expand verdict"):
                validate_acceptance_bundle(verdict, tampered_claim, registry, origins)

        with self.subTest(tamper="required overlay unknown"):
            registry = copy.deepcopy(self.registry)
            registry["ROUTE-FIX-001"]["overlays"]["production"]["required"] = "unknown"
            with self.assertRaisesRegex(ValueError, "required overlay is unknown"):
                validate_acceptance_bundle(verdict, claim, registry, self.origins)

    def test_overlay_proof_time_and_rewrite_tampering_fails_closed(self) -> None:
        verdict = self.registry["VERDICT-FIX-001"]
        claim = self.registry["CLAIM-FIX-001"]

        with self.subTest(tamper="derived overlay requirement mismatch"):
            registry = copy.deepcopy(self.registry)
            registry["ROUTE-FIX-001"]["route_inputs"]["execution_topology"] = "multi_agent"
            with self.assertRaisesRegex(ValueError, "derived overlay requirement mismatch"):
                validate_acceptance_bundle(verdict, claim, registry, self.origins)

        with self.subTest(tamper="enabled overlay incomplete"):
            registry = copy.deepcopy(self.registry)
            registry["ROUTE-FIX-001"]["overlays"]["multi_agent"]["enabled"] = True
            with self.assertRaisesRegex(ValueError, "enabled overlay invariant"):
                validate_acceptance_bundle(verdict, claim, registry, self.origins)

        with self.subTest(tamper="critical evidence proof downgrade"):
            registry = copy.deepcopy(self.registry)
            tampered_verdict = copy.deepcopy(verdict)
            tampered_claim = copy.deepcopy(claim)
            control_evidence = registry["EVIDENCE-FIX-CONTROL-001"]
            control_evidence["proof_level"] = "control_package"
            with self.assertRaisesRegex(ValueError, "claim proof exceeds critical path ceiling"):
                validate_acceptance_bundle(tampered_verdict, tampered_claim, registry, self.origins)

        with self.subTest(tamper="all acceptance bindings expired"):
            registry = copy.deepcopy(self.registry)
            tampered_verdict = copy.deepcopy(verdict)
            tampered_claim = copy.deepcopy(claim)
            tampered_verdict["expires_at"] = "2026-07-11T13:00:00+00:00"
            tampered_claim["expires_at"] = "2026-07-11T12:59:00+00:00"
            grant = registry["GRANT-FIX-001"]
            grant["expires_at"] = "2026-07-11T13:00:00+00:00"
            grant["content_hash"] = canonical_object_hash(grant)
            authorization = registry["AUTH-FIX-001"]
            authorization["expires_at"] = "2026-07-11T13:00:00+00:00"
            authorization["capability_grant_hashes"] = [grant["content_hash"]]
            authorization["content_hash"] = canonical_object_hash(authorization)
            tampered_verdict["approval_and_permission_snapshot_hashes"] = [authorization["content_hash"]]
            tampered_claim["approval_and_permission_snapshot_hashes"] = [authorization["content_hash"]]
            with self.assertRaisesRegex(ValueError, "expired at validation time"):
                validate_acceptance_bundle(tampered_verdict, tampered_claim, registry, self.origins)

        with self.subTest(tamper="AI rewrite attempt exceeds maximum"):
            registry = copy.deepcopy(self.registry)
            tampered_verdict = copy.deepcopy(verdict)
            tampered_claim = copy.deepcopy(claim)
            review = registry["AI-REVIEW-FIX-001"]
            review["rewrite_attempt"] = review["max_rewrite_attempts"] + 1
            review["content_hash"] = canonical_object_hash(review)
            tampered_verdict["ai_review_verdict_hashes"] = [review["content_hash"]]
            tampered_claim["ai_review_verdict_hashes"] = [review["content_hash"]]
            with self.assertRaisesRegex(ValueError, "AI rewrite attempt is out of bounds"):
                validate_acceptance_bundle(tampered_verdict, tampered_claim, registry, self.origins)

    def test_rewrite_limit_and_control_evidence_tampering_fails_closed(self) -> None:
        verdict = self.registry["VERDICT-FIX-001"]
        claim = self.registry["CLAIM-FIX-001"]

        with self.subTest(tamper="non-blocked AI review reaches rewrite limit"):
            registry = copy.deepcopy(self.registry)
            tampered_verdict = copy.deepcopy(verdict)
            tampered_claim = copy.deepcopy(claim)
            review = registry["AI-REVIEW-FIX-001"]
            review["rewrite_attempt"] = review["max_rewrite_attempts"]
            review["content_hash"] = canonical_object_hash(review)
            tampered_verdict["ai_review_verdict_hashes"] = [review["content_hash"]]
            tampered_claim["ai_review_verdict_hashes"] = [review["content_hash"]]
            with self.assertRaisesRegex(ValueError, "rewrite limit requires blocked decision"):
                validate_acceptance_bundle(tampered_verdict, tampered_claim, registry, self.origins)

        with self.subTest(tamper="control implementation evidence invalidated"):
            registry = copy.deepcopy(self.registry)
            registry["EVIDENCE-FIX-CONTROL-001"]["stale_status"] = "invalidated"
            with self.assertRaisesRegex(ValueError, "control implementation evidence must be verified and fresh"):
                validate_acceptance_bundle(verdict, claim, registry, self.origins)

        with self.subTest(tamper="control implementation evidence subject hash misbound"):
            registry = copy.deepcopy(self.registry)
            registry["EVIDENCE-FIX-CONTROL-001"]["subject_hash"] = "0" * 64
            with self.assertRaisesRegex(ValueError, "control implementation evidence subject hash mismatch"):
                validate_acceptance_bundle(verdict, claim, registry, self.origins)

    def test_runs_and_evidence_follow_dynamic_contract_and_fail_closed(self) -> None:
        contract_path = ROOT / "contracts" / "governance" / "run-evidence-contract.yaml"
        self.assertTrue(contract_path.is_file(), "missing Run/Evidence machine contract")
        contract = load_yaml(contract_path)
        validate_run_evidence_contracts(self.registry, self.origins, contract)

        for run_id in (
            "RUN-FIX-SUCCESS-001",
            "RUN-FIX-FAILED-001",
            "RUN-FIX-RESUMED-001",
            "RUN-FIX-REVIEW-001",
            "RUN-FIX-CONTROL-VERIFY-001",
        ):
            with self.subTest(run=run_id):
                self.assertEqual(
                    set(),
                    set(contract["run"]["required_fields"]) - set(self.registry[run_id]),
                )

        for evidence_id in (
            "EVIDENCE-FIX-SUCCESS-001",
            "EVIDENCE-FIX-RESUMED-001",
            "EVIDENCE-FIX-CONTROL-001",
        ):
            with self.subTest(evidence=evidence_id):
                evidence = self.registry[evidence_id]
                self.assertEqual(
                    set(),
                    set(contract["evidence"]["required_fields"]) - set(evidence),
                )
                self.assertNotIn("status", evidence)

        with self.subTest(tamper="required fingerprint missing"):
            registry = copy.deepcopy(self.registry)
            registry["RUN-FIX-SUCCESS-001"].pop("code_fingerprint")
            with self.assertRaisesRegex(ValueError, "missing required Run fields"):
                validate_run_evidence_contracts(registry, self.origins, contract)

        with self.subTest(tamper="attempt manifest incomplete"):
            registry = copy.deepcopy(self.registry)
            registry["RUN-FIX-SUCCESS-001"]["attempt_manifest"][0].pop("output_status")
            with self.assertRaisesRegex(ValueError, "attempt manifest entry is incomplete"):
                validate_run_evidence_contracts(registry, self.origins, contract)

        for field, bad_value, expected in (
            ("verification_status", "captured", "Evidence verification_status must be verified"),
            ("stale_status", "stale", "Evidence stale_status must be fresh"),
        ):
            with self.subTest(tamper=field):
                registry = copy.deepcopy(self.registry)
                registry["EVIDENCE-FIX-SUCCESS-001"][field] = bad_value
                with self.assertRaisesRegex(ValueError, expected):
                    validate_run_evidence_contracts(registry, self.origins, contract)

        with self.subTest(tamper="Evidence points to wrong Run"):
            registry = copy.deepcopy(self.registry)
            registry["EVIDENCE-FIX-SUCCESS-001"]["run_ref"] = "RUN-FIX-REVIEW-001"
            with self.assertRaisesRegex(ValueError, "Evidence subject or Run binding mismatch"):
                validate_run_evidence_contracts(registry, self.origins, contract)

        with self.subTest(tamper="failed Run rewritten as success"):
            registry = copy.deepcopy(self.registry)
            failed = registry["RUN-FIX-FAILED-001"]
            failed["status"] = "succeeded"
            failed["execution_outcome"] = "success"
            failed["semantic_result"] = "passed"
            with self.assertRaisesRegex(ValueError, "failed Run history is inconsistent"):
                validate_run_evidence_contracts(registry, self.origins, contract)

    def test_control_verification_run_and_critical_evidence_fail_closed(self) -> None:
        contract = load_yaml(ROOT / "contracts" / "governance" / "run-evidence-contract.yaml")
        self.assertIn(
            "verified_critical_path_evidence_requires_non_empty_criterion_results",
            contract["evidence"]["invariants"],
        )
        self.assertIn("CONTROL-CRITERION-FIX-001", self.registry)
        self.assertIn("RUN-FIX-CONTROL-VERIFY-001", self.registry)
        self.assertIn("ATTEMPT-FIX-CONTROL-VERIFY-001", self.registry)

        control_run = self.registry["RUN-FIX-CONTROL-VERIFY-001"]
        control_evidence = self.registry["EVIDENCE-FIX-CONTROL-001"]
        workflow = self.registry["WF-FIX-001"]
        self.assertEqual("control_set_verification", control_run["run_kind"])
        self.assertIn(control_run["run_id"], workflow["run_refs"])
        self.assertEqual("WF-FIX-001", control_run["workflow_ref"])
        self.assertEqual("RUN-FIX-CONTROL-VERIFY-001", control_evidence["run_ref"])
        self.assertEqual(
            ["ATTEMPT-FIX-CONTROL-VERIFY-001"],
            control_evidence["included_attempt_refs"],
        )
        self.assertEqual(
            ["ATTEMPT-FIX-CONTROL-VERIFY-001"],
            control_evidence["artifact_refs"],
        )
        self.assertTrue(control_evidence["criterion_results"])
        self.assertEqual(
            ["ATTEMPT-FIX-CONTROL-VERIFY-001"],
            control_evidence["criterion_results"][0]["raw_evidence_refs"],
        )
        validate_run_evidence_contracts(self.registry, self.origins, contract)

        with self.subTest(tamper="critical control Evidence has no criterion result"):
            registry = copy.deepcopy(self.registry)
            registry["EVIDENCE-FIX-CONTROL-001"]["criterion_results"] = []
            with self.assertRaisesRegex(ValueError, "critical Evidence requires non-empty criterion results"):
                validate_run_evidence_contracts(registry, self.origins, contract)

        with self.subTest(tamper="control Evidence reuses non-control attempt"):
            registry = copy.deepcopy(self.registry)
            evidence = registry["EVIDENCE-FIX-CONTROL-001"]
            evidence["included_attempt_refs"] = ["ATTEMPT-FIX-SUCCESS-001"]
            evidence["artifact_refs"] = ["ATTEMPT-FIX-SUCCESS-001"]
            evidence["criterion_results"][0]["raw_evidence_refs"] = ["ATTEMPT-FIX-SUCCESS-001"]
            with self.assertRaisesRegex(ValueError, "control Evidence must use control verification attempt"):
                validate_run_evidence_contracts(registry, self.origins, contract)

    def test_missing_reopen_target_fails_closed(self) -> None:
        recovery = load_yaml(NEGATIVE / "missing-reopen-target" / "recovery.yaml")
        with self.assertRaisesRegex(ValueError, "reopen_target"):
            validate_recovery(recovery, self.registry)


class OperationalSpineRepositoryStateTests(unittest.TestCase):
    def test_snapshot_hash_inventory_exactly_matches_fixture_tree(self) -> None:
        snapshot = load_yaml(SNAPSHOT)
        paths = fixture_content_paths()
        expected = {path.relative_to(ROOT).as_posix(): sha256(path) for path in paths}
        self.assertEqual(expected, snapshot["content_integrity"]["files"])
        self.assertEqual(
            fixture_tree_manifest_sha256(paths),
            snapshot["content_integrity"]["fixture_tree_manifest_sha256"],
        )

    def test_project_state_and_evidence_snapshot_are_fixture_scoped(self) -> None:
        project = load_yaml(ROOT / "project-os.yaml")
        self.assertTrue(SNAPSHOT.is_file(), f"missing evidence snapshot: {SNAPSHOT}")
        snapshot = load_yaml(SNAPSHOT)

        self.assertEqual("approved", project["maturity"]["design_status"])
        self.assertEqual("partial", project["maturity"]["implementation_status"])
        self.assertEqual("unverified", project["maturity"]["verification_status"])
        self.assertEqual("fixture_runtime_proven", project["score_summary"]["fixture_proof"])
        self.assertEqual("operational_spine_fixture_only", project["score_summary"]["fixture_proof_scope"])
        self.assertEqual("not_evaluated", project["score_summary"]["current_overall_score"])
        self.assertEqual("fixture_runtime_proven", project["claim_limits"]["ceiling"])
        self.assertEqual("operational_spine_fixture_only", project["claim_limits"]["scope"])
        self.assertEqual([], project["claim_limits"]["current_claims"])
        self.assertIn(str(SNAPSHOT.relative_to(ROOT)), project["proof_evidence"])

        self.assertEqual("a7378fe", snapshot["baseline_revision"])
        captured_at = datetime.fromisoformat(snapshot["captured_at"])
        self.assertIsNotNone(captured_at.tzinfo)
        self.assertEqual(
            f"EVIDENCE-OPERATIONAL-SPINE-FIXTURE-{captured_at.strftime('%Y%m%d')}",
            snapshot["evidence_id"],
        )
        self.assertLessEqual(captured_at.astimezone(timezone.utc), datetime.now(timezone.utc) + timedelta(minutes=5))
        self.assertEqual("not_evaluated", snapshot["current_overall_score"])
        self.assertEqual("fixture_runtime_proven", snapshot["proof_level_ceiling"])
        self.assertEqual("anonymous_operational_spine_fixture_only", snapshot["proof_scope"])
        self.assertEqual("internal_separate_agent_not_external", snapshot["reviewer_independence"])
        self.assertEqual("unmet", snapshot["hard_gates"]["cross_project_isolation"])
        self.assertEqual("unmet", snapshot["hard_gates"]["second_heterogeneous_l2"])
        self.assertEqual("unmet", snapshot["hard_gates"]["independent_adversarial_94_gate"])
        self.assertFalse(snapshot["claims_allowed"]["production_ready"])
        self.assertFalse(snapshot["claims_allowed"]["general_95_plus"])


if __name__ == "__main__":
    unittest.main()
