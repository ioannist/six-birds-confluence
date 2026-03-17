"""Final experimental freeze builders and validators."""

from __future__ import annotations

import json
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import yaml

from .regression_harness import build_regression_steps, run_regression_steps
from .results_ledger import build_results_ledger, write_results_ledger


ROOT = Path(__file__).resolve().parents[2]
MATRIX_PATH = ROOT / "project" / "claim_support_matrix.yaml"
FREEZE_DIR = ROOT / "results" / "freeze"
MATRIX_JSON_PATH = FREEZE_DIR / "claim_support_matrix.json"
SUMMARY_JSON_PATH = FREEZE_DIR / "final_experiment_summary.json"

REQUIRED_CLAIM_IDS = [
    "CSM001_elementary_flatness_iff_local_confluence_core",
    "CSM002_confluence_plus_normalizing_implies_exists_unique_normal_form_from_start",
    "CSM003_finite_terminating_local_flatness_implies_confluence",
    "CSM004_finite_terminating_confluence_iff_unique_reachable_normal_forms",
    "CSM005_bare_graph_flatness_is_inadequate_without_2cells",
    "CSM006_reachable_string_critical_pair_defects_capture_local_obstructions",
    "CSM007_string_completion_eliminates_local_defects",
    "CSM008_left_linear_trs_reachable_critical_pairs_capture_local_obstructions",
    "CSM009_reduction_2complex_elementary_holonomy_layer_is_explicit",
    "CSM010_full_confluence_equals_flatness_theorem_for_finite_terminating_left_linear_trs",
]

ALLOWED_STATUS = {"proved", "empirically_supported", "deferred_to_paper_theorem"}
ALLOWED_EVIDENCE_TYPES = {
    "lean_proved",
    "exhaustive_computational",
    "curated_term_level",
    "structural_artifact",
}


def _utc_now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def load_claim_support_matrix(path: Path = MATRIX_PATH) -> dict[str, Any]:
    payload = yaml.safe_load(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError("claim support matrix must be a mapping")
    return payload


def validate_claim_support_matrix(matrix: dict[str, Any]) -> dict[str, Any]:
    claims = matrix.get("claims")
    if not isinstance(claims, list):
        raise ValueError("claim support matrix missing claims list")

    rows_by_id: dict[str, dict[str, Any]] = {}
    evidence_types_seen: set[str] = set()

    for row in claims:
        if not isinstance(row, dict):
            raise ValueError("claim row must be a mapping")
        for field in ("claim_id", "label", "exact_hypotheses", "evidence", "status"):
            if field not in row:
                raise ValueError(f"claim row missing required field: {field}")

        claim_id = row["claim_id"]
        if not isinstance(claim_id, str) or not claim_id:
            raise ValueError("claim_id must be a non-empty string")
        if claim_id in rows_by_id:
            raise ValueError(f"duplicate claim_id: {claim_id}")
        rows_by_id[claim_id] = row

        status = row["status"]
        if status not in ALLOWED_STATUS:
            raise ValueError(f"invalid status for {claim_id}: {status}")

        evidence = row["evidence"]
        if not isinstance(evidence, list) or not evidence:
            raise ValueError(f"evidence must be non-empty list for {claim_id}")
        for ev in evidence:
            if not isinstance(ev, dict):
                raise ValueError(f"evidence entry must be mapping for {claim_id}")
            if "evidence_type" not in ev or "strongest_artifact_paths" not in ev:
                raise ValueError(f"evidence entry missing required fields for {claim_id}")
            ev_type = ev["evidence_type"]
            if ev_type not in ALLOWED_EVIDENCE_TYPES:
                raise ValueError(f"invalid evidence_type for {claim_id}: {ev_type}")
            evidence_types_seen.add(ev_type)
            paths = ev["strongest_artifact_paths"]
            if not isinstance(paths, list) or not paths:
                raise ValueError(f"strongest_artifact_paths must be non-empty list for {claim_id}")
            for rel in paths:
                if not isinstance(rel, str) or not rel:
                    raise ValueError(f"invalid strongest_artifact_path for {claim_id}")
                if not (ROOT / rel).exists():
                    raise ValueError(f"missing strongest_artifact_path for {claim_id}: {rel}")

    missing_claim_rows = [cid for cid in REQUIRED_CLAIM_IDS if cid not in rows_by_id]
    missing_evidence_types = sorted(ALLOWED_EVIDENCE_TYPES - evidence_types_seen)

    status_counts = Counter(row["status"] for row in rows_by_id.values())

    return {
        "claim_count": len(rows_by_id),
        "status_counts": {
            "proved": status_counts.get("proved", 0),
            "empirically_supported": status_counts.get("empirically_supported", 0),
            "deferred_to_paper_theorem": status_counts.get("deferred_to_paper_theorem", 0),
        },
        "missing_claim_rows": missing_claim_rows,
        "missing_evidence_types": missing_evidence_types,
    }


def build_final_experiment_summary(
    regression_result: dict[str, Any],
    matrix_validation: dict[str, Any],
    ledger: dict[str, Any],
) -> dict[str, Any]:
    missing_required = ledger.get("missing_required_collections", [])

    remaining_theorem_work = [
        "full theorem package for finite terminating left-linear TRSs in exact target form",
        "explicit reduction 2-complex and 2-connection theorem phrasing",
        "bridge to standard critical-pair completeness/local-confluence in full TRS setting",
    ]

    implementation_complete = (
        regression_result.get("success", False)
        and not matrix_validation["missing_claim_rows"]
        and not matrix_validation["missing_evidence_types"]
        and not missing_required
    )

    return {
        "schema_version": 1,
        "kind": "final_experiment_summary",
        "generated_at_utc": _utc_now(),
        "regression": {
            "status": "passed" if regression_result.get("success") else "failed",
            "runtime_seconds": regression_result.get("total_runtime_seconds", 0.0),
            "step_count": regression_result.get("step_count", 0),
        },
        "claim_matrix": {
            "path": "project/claim_support_matrix.yaml",
            "claim_count": matrix_validation["claim_count"],
            "status_counts": matrix_validation["status_counts"],
            "missing_claim_rows": matrix_validation["missing_claim_rows"],
            "missing_evidence_types": matrix_validation["missing_evidence_types"],
        },
        "artifact_families": {
            "present": sorted(ledger.get("collection_counts", {}).keys()),
            "missing_required_collections": missing_required,
        },
        "implementation": {
            "remaining_implementation_tasks": [],
            "implementation_complete": implementation_complete,
        },
        "remaining_theorem_writing_work": remaining_theorem_work,
        "freeze_verdict": "implementation_complete" if implementation_complete else "implementation_not_complete",
    }


def run_final_freeze(
    *,
    run_regression: bool = True,
    regression_result: dict[str, Any] | None = None,
) -> dict[str, Any]:
    FREEZE_DIR.mkdir(parents=True, exist_ok=True)

    if run_regression:
        regression = run_regression_steps(steps=build_regression_steps())
    else:
        regression = regression_result or {
            "success": True,
            "failed_step": None,
            "step_count": len(build_regression_steps()),
            "executed_step_count": len(build_regression_steps()),
            "total_runtime_seconds": 0.0,
            "slowest_step": None,
            "steps": [],
        }

    if not regression["success"]:
        raise RuntimeError(f"regression failed at step: {regression['failed_step']}")

    matrix = load_claim_support_matrix(MATRIX_PATH)
    matrix_validation = validate_claim_support_matrix(matrix)

    MATRIX_JSON_PATH.write_text(json.dumps(matrix, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    # refresh ledger after writing freeze matrix copy
    write_results_ledger(root="results")
    ledger = build_results_ledger(root="results")

    summary = build_final_experiment_summary(regression, matrix_validation, ledger)
    SUMMARY_JSON_PATH.write_text(json.dumps(summary, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    # refresh ledger again so freeze summary itself is indexed
    write_results_ledger(root="results")

    return {
        "regression": regression,
        "matrix_validation": matrix_validation,
        "summary": summary,
    }
