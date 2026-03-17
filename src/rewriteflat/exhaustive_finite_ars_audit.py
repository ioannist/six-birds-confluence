"""Exhaustive audit utilities for small labeled finite ARSs."""

from __future__ import annotations

import time
from typing import Any

from .finite_ars import FiniteARS
from .peak_analysis import analyze_all_peaks


DISCREPANCY_KEYS = {
    "local_flatness_vs_local_confluence": "local_flatness_vs_local_confluence",
    "terminating_local_flatness_not_confluent": "terminating_local_flatness_not_confluent",
    "terminating_confluent_not_unique_reachable_normal_forms": "terminating_confluent_not_unique_reachable_normal_forms",
    "terminating_unique_reachable_normal_forms_not_confluent": "terminating_unique_reachable_normal_forms_not_confluent",
}


def enumerate_labeled_finite_ars(n_states: int):
    if n_states <= 0:
        raise ValueError("n_states must be positive")

    states = [f"s{i}" for i in range(n_states)]
    candidates = [(src, dst) for src in states for dst in states]
    total_masks = 1 << (n_states * n_states)
    width = len(str(total_masks - 1))

    for mask in range(total_masks):
        edges = [candidates[i] for i in range(len(candidates)) if (mask >> i) & 1]
        system_id = f"N{n_states:02d}_M{mask:0{width}d}"
        yield system_id, FiniteARS(states=states, edges=edges)


def build_terminating_audit_row(system_id: str, ars: FiniteARS) -> dict[str, Any]:
    peaks = analyze_all_peaks(ars)
    nonjoinability_defect_count = sum(1 for peak in peaks if peak["nonjoinability_defect"])
    nf_outcome_mismatch_count = sum(1 for peak in peaks if peak["nf_outcome_mismatch"] is True)
    local_flatness = nonjoinability_defect_count == 0
    locally_confluent = ars.is_locally_confluent()
    confluent = ars.is_confluent()
    unique_rnf = ars.has_unique_reachable_normal_forms()

    return {
        "system_id": system_id,
        "n_states": len(ars.states),
        "edge_count": len(ars.edges),
        "peak_count": len(peaks),
        "nonjoinability_defect_count": nonjoinability_defect_count,
        "nf_outcome_mismatch_count": nf_outcome_mismatch_count,
        "local_flatness": local_flatness,
        "locally_confluent": locally_confluent,
        "confluent": confluent,
        "unique_reachable_normal_forms": unique_rnf,
    }


def run_exhaustive_audit(max_states: int = 4) -> dict[str, Any]:
    if max_states <= 0:
        raise ValueError("max_states must be positive")

    start = time.perf_counter()
    rows: list[dict[str, Any]] = []
    per_n: list[dict[str, Any]] = []

    counterexamples: dict[str, list[dict[str, Any]]] = {
        DISCREPANCY_KEYS["local_flatness_vs_local_confluence"]: [],
        DISCREPANCY_KEYS["terminating_local_flatness_not_confluent"]: [],
        DISCREPANCY_KEYS["terminating_confluent_not_unique_reachable_normal_forms"]: [],
        DISCREPANCY_KEYS["terminating_unique_reachable_normal_forms_not_confluent"]: [],
    }

    total_systems_checked = 0
    total_terminating_systems_checked = 0

    for n_states in range(1, max_states + 1):
        n_total = 0
        n_terminating = 0
        n_local_flatness = 0
        n_locally_confluent = 0
        n_confluent = 0
        n_unique_rnf = 0

        for system_id, ars in enumerate_labeled_finite_ars(n_states):
            n_total += 1
            total_systems_checked += 1

            if not ars.is_terminating():
                continue

            n_terminating += 1
            total_terminating_systems_checked += 1
            row = build_terminating_audit_row(system_id, ars)
            rows.append(row)

            if row["local_flatness"]:
                n_local_flatness += 1
            if row["locally_confluent"]:
                n_locally_confluent += 1
            if row["confluent"]:
                n_confluent += 1
            if row["unique_reachable_normal_forms"]:
                n_unique_rnf += 1

            edge_rows = [[src, dst] for src, dst in ars.edges]
            details = {
                "system_id": system_id,
                "n_states": n_states,
                "states": list(ars.states),
                "edges": edge_rows,
                "metrics": row,
            }

            if row["local_flatness"] != row["locally_confluent"]:
                counterexamples[DISCREPANCY_KEYS["local_flatness_vs_local_confluence"]].append(details)
            if row["local_flatness"] and not row["confluent"]:
                counterexamples[DISCREPANCY_KEYS["terminating_local_flatness_not_confluent"]].append(details)
            if row["confluent"] and not row["unique_reachable_normal_forms"]:
                counterexamples[
                    DISCREPANCY_KEYS["terminating_confluent_not_unique_reachable_normal_forms"]
                ].append(details)
            if row["unique_reachable_normal_forms"] and not row["confluent"]:
                counterexamples[
                    DISCREPANCY_KEYS["terminating_unique_reachable_normal_forms_not_confluent"]
                ].append(details)

        per_n.append(
            {
                "n_states": n_states,
                "total_systems_checked": n_total,
                "total_terminating_systems_checked": n_terminating,
                "local_flatness_count": n_local_flatness,
                "locally_confluent_count": n_locally_confluent,
                "confluent_count": n_confluent,
                "unique_reachable_normal_forms_count": n_unique_rnf,
            }
        )

    discrepancy_counts = {key: len(value) for key, value in counterexamples.items()}
    findings = {
        "local_flatness_eq_local_confluence_holds": discrepancy_counts[
            DISCREPANCY_KEYS["local_flatness_vs_local_confluence"]
        ]
        == 0,
        "terminating_local_flatness_implies_confluence_holds": discrepancy_counts[
            DISCREPANCY_KEYS["terminating_local_flatness_not_confluent"]
        ]
        == 0,
        "terminating_confluence_implies_unique_reachable_normal_forms_holds": discrepancy_counts[
            DISCREPANCY_KEYS["terminating_confluent_not_unique_reachable_normal_forms"]
        ]
        == 0,
        "terminating_unique_reachable_normal_forms_implies_confluence_holds": discrepancy_counts[
            DISCREPANCY_KEYS["terminating_unique_reachable_normal_forms_not_confluent"]
        ]
        == 0,
    }

    runtime_seconds = time.perf_counter() - start

    summary_artifact = {
        "schema_version": 1,
        "kind": "exhaustive_finite_ars_audit",
        "search_space": {
            "max_states": max_states,
            "include_self_loops": True,
            "state_naming": "s0..s{n-1}",
            "total_systems_checked": total_systems_checked,
            "total_terminating_systems_checked": total_terminating_systems_checked,
        },
        "per_n": per_n,
        "discrepancy_counts": discrepancy_counts,
        "findings": findings,
        "runtime_seconds": runtime_seconds,
    }

    counterexample_artifact = {
        "schema_version": 1,
        "kind": "exhaustive_finite_ars_counterexamples",
        "search_space": {
            "max_states": max_states,
            "include_self_loops": True,
            "state_naming": "s0..s{n-1}",
        },
        "counterexamples": counterexamples,
    }

    return {
        "summary": summary_artifact,
        "rows": rows,
        "counterexamples": counterexample_artifact,
    }
