"""Curvature-generator audit comparing local peaks and critical-pair defects."""

from __future__ import annotations

from typing import Any

from .critical_pairs import build_critical_pair_artifact
from .example_io import load_string_rewrite_system
from .peak_analysis import analyze_all_peaks
from .string_rewriting import analyze_string_exploration, finite_ars_from_exploration


CURATED_STRING_EXAMPLE_IDS = [
    "E005_string_sort_confluent",
    "E006_string_overlap_nonconfluent",
    "E007_completion_before",
    "E008_completion_after",
]


def _signature(source_word: str, left: str, right: str) -> tuple[str, tuple[str, str]]:
    return (source_word, tuple(sorted((left, right))))


def _signature_rows(signatures: set[tuple[str, tuple[str, str]]]) -> list[dict[str, Any]]:
    return [
        {"source_word": source, "branches": [branches[0], branches[1]]}
        for source, branches in sorted(signatures, key=lambda item: (item[0], item[1][0], item[1][1]))
    ]


def build_example_curvature_audit_row(example_id: str) -> dict[str, Any]:
    from pathlib import Path

    root = Path(__file__).resolve().parents[2]
    example_path = root / "data" / "examples" / f"{example_id}.yaml"
    example, system = load_string_rewrite_system(example_path)
    bounds = example["bounds"]
    max_depth = bounds.get("max_depth")
    max_states = bounds.get("max_states")
    max_word_length = bounds.get("max_word_length")
    if max_depth is None or max_states is None:
        raise ValueError(f"example {example_id} bounds must include max_depth and max_states")

    exploration = system.explore_bounded(
        start_strings=example["start_strings"],
        max_depth=max_depth,
        max_states=max_states,
        max_word_length=max_word_length,
    )
    string_analysis = analyze_string_exploration(exploration)
    ars = finite_ars_from_exploration(exploration)
    peaks = analyze_all_peaks(ars)

    local_nonjoin = sum(1 for peak in peaks if peak["nonjoinability_defect"])
    local_nf_mismatch = sum(1 for peak in peaks if peak["nf_outcome_mismatch"] is True)
    local_peak_has_obstruction = (local_nonjoin > 0) or (local_nf_mismatch > 0)

    peak_signatures = {_signature(peak["source"], peak["left"], peak["right"]) for peak in peaks}
    peak_nonjoin_signatures = {
        _signature(peak["source"], peak["left"], peak["right"])
        for peak in peaks
        if peak["nonjoinability_defect"]
    }
    peak_nf_mismatch_signatures = {
        _signature(peak["source"], peak["left"], peak["right"])
        for peak in peaks
        if peak["nf_outcome_mismatch"] is True
    }

    cp_artifact = build_critical_pair_artifact(example_id, example, system)
    cps = cp_artifact["critical_pairs"]

    system_nonjoin = sum(1 for cp in cps if cp["nonjoinability_defect"])
    system_nf_mismatch = sum(1 for cp in cps if cp["nf_outcome_mismatch"] is True)
    reachable_cps = [cp for cp in cps if cp["source_reachable_from_example_starts"]]
    reachable_nonjoin = sum(1 for cp in reachable_cps if cp["nonjoinability_defect"])
    reachable_nf_mismatch = sum(1 for cp in reachable_cps if cp["nf_outcome_mismatch"] is True)
    reachable_has_obstruction = (reachable_nonjoin > 0) or (reachable_nf_mismatch > 0)

    reachable_signatures = {
        _signature(cp["source_word"], cp["left_branch_term"], cp["right_branch_term"]) for cp in reachable_cps
    }
    reachable_nonjoin_signatures = {
        _signature(cp["source_word"], cp["left_branch_term"], cp["right_branch_term"])
        for cp in reachable_cps
        if cp["nonjoinability_defect"]
    }
    reachable_nf_mismatch_signatures = {
        _signature(cp["source_word"], cp["left_branch_term"], cp["right_branch_term"])
        for cp in reachable_cps
        if cp["nf_outcome_mismatch"] is True
    }

    reachable_missing_from_graph = cp_artifact["cross_check"][
        "reachable_critical_pairs_missing_from_graph_peaks"
    ]
    graph_missing_from_reachable = cp_artifact["cross_check"][
        "graph_peaks_missing_from_reachable_critical_pairs"
    ]
    reachable_cross_check_match = cp_artifact["cross_check"]["reachable_cross_check_match"]

    nonjoin_cp_missing = _signature_rows(reachable_nonjoin_signatures - peak_nonjoin_signatures)
    nonjoin_graph_missing = _signature_rows(peak_nonjoin_signatures - reachable_nonjoin_signatures)
    nonjoinability_match = not nonjoin_cp_missing and not nonjoin_graph_missing

    nf_cp_missing = _signature_rows(reachable_nf_mismatch_signatures - peak_nf_mismatch_signatures)
    nf_graph_missing = _signature_rows(peak_nf_mismatch_signatures - reachable_nf_mismatch_signatures)
    nf_mismatch_match = not nf_cp_missing and not nf_graph_missing

    confluent = bool(string_analysis["confluent"])
    global_vs_local_peak_alignment = confluent == (not local_peak_has_obstruction)
    global_vs_reachable_cp_alignment = confluent == (not reachable_has_obstruction)

    curvature_supported = (
        reachable_cross_check_match
        and nonjoinability_match
        and nf_mismatch_match
        and global_vs_local_peak_alignment
        and global_vs_reachable_cp_alignment
    )

    return {
        "example_id": example_id,
        "global": {
            "terminating": bool(string_analysis["terminating"]),
            "exploration_complete": bool(exploration["exploration_complete"]),
            "confluent": confluent,
            "unique_reachable_normal_forms": bool(string_analysis["unique_reachable_normal_forms"]),
            "normal_forms": list(string_analysis["normal_forms"]),
        },
        "local_peaks": {
            "local_peak_count": len(peaks),
            "local_peak_nonjoinability_defect_count": local_nonjoin,
            "local_peak_nf_outcome_mismatch_count": local_nf_mismatch,
            "local_peak_has_obstruction": local_peak_has_obstruction,
        },
        "critical_pairs": {
            "system_critical_pair_count": cp_artifact["system_critical_pair_count"],
            "reachable_critical_pair_count": cp_artifact["reachable_critical_pair_count"],
            "system_critical_pair_nonjoinability_defect_count": system_nonjoin,
            "system_critical_pair_nf_outcome_mismatch_count": system_nf_mismatch,
            "reachable_critical_pair_nonjoinability_defect_count": reachable_nonjoin,
            "reachable_critical_pair_nf_outcome_mismatch_count": reachable_nf_mismatch,
            "reachable_critical_pair_has_obstruction": reachable_has_obstruction,
        },
        "alignment": {
            "reachable_cross_check_match": reachable_cross_check_match,
            "reachable_critical_pairs_missing_from_graph_peaks": reachable_missing_from_graph,
            "graph_peaks_missing_from_reachable_critical_pairs": graph_missing_from_reachable,
            "nonjoinability_defect_signature_match": nonjoinability_match,
            "nonjoinability_defect_reachable_cp_missing_from_graph": nonjoin_cp_missing,
            "nonjoinability_defect_graph_missing_from_reachable_cp": nonjoin_graph_missing,
            "nf_outcome_mismatch_signature_match": nf_mismatch_match,
            "nf_outcome_mismatch_reachable_cp_missing_from_graph": nf_cp_missing,
            "nf_outcome_mismatch_graph_missing_from_reachable_cp": nf_graph_missing,
            "global_vs_local_peak_alignment": global_vs_local_peak_alignment,
            "global_vs_reachable_critical_pair_alignment": global_vs_reachable_cp_alignment,
        },
        "curvature_generator_story_supported": curvature_supported,
    }


def _completion_pair_delta(rows_by_id: dict[str, dict[str, Any]]) -> dict[str, Any]:
    before_id = "E007_completion_before"
    after_id = "E008_completion_after"
    before = rows_by_id[before_id]
    after = rows_by_id[after_id]

    before_local_nonjoin = before["local_peaks"]["local_peak_nonjoinability_defect_count"]
    after_local_nonjoin = after["local_peaks"]["local_peak_nonjoinability_defect_count"]
    before_local_nf = before["local_peaks"]["local_peak_nf_outcome_mismatch_count"]
    after_local_nf = after["local_peaks"]["local_peak_nf_outcome_mismatch_count"]
    before_cp_nonjoin = before["critical_pairs"][
        "reachable_critical_pair_nonjoinability_defect_count"
    ]
    after_cp_nonjoin = after["critical_pairs"][
        "reachable_critical_pair_nonjoinability_defect_count"
    ]
    before_cp_nf = before["critical_pairs"]["reachable_critical_pair_nf_outcome_mismatch_count"]
    after_cp_nf = after["critical_pairs"]["reachable_critical_pair_nf_outcome_mismatch_count"]

    defect_elimination_observed = (
        (before["global"]["confluent"] is False)
        and (after["global"]["confluent"] is True)
        and before_local_nonjoin > 0
        and before_local_nf > 0
        and before_cp_nonjoin > 0
        and before_cp_nf > 0
        and after_local_nonjoin == 0
        and after_local_nf == 0
        and after_cp_nonjoin == 0
        and after_cp_nf == 0
    )

    return {
        "before_example_id": before_id,
        "after_example_id": after_id,
        "before_confluent": before["global"]["confluent"],
        "after_confluent": after["global"]["confluent"],
        "before_local_peak_nonjoinability_defect_count": before_local_nonjoin,
        "after_local_peak_nonjoinability_defect_count": after_local_nonjoin,
        "before_local_peak_nf_outcome_mismatch_count": before_local_nf,
        "after_local_peak_nf_outcome_mismatch_count": after_local_nf,
        "before_reachable_critical_pair_nonjoinability_defect_count": before_cp_nonjoin,
        "after_reachable_critical_pair_nonjoinability_defect_count": after_cp_nonjoin,
        "before_reachable_critical_pair_nf_outcome_mismatch_count": before_cp_nf,
        "after_reachable_critical_pair_nf_outcome_mismatch_count": after_cp_nf,
        "defect_elimination_observed": defect_elimination_observed,
    }


def build_critical_pair_curvature_audit(example_ids: list[str] | None = None) -> dict[str, Any]:
    ids = CURATED_STRING_EXAMPLE_IDS if example_ids is None else list(example_ids)
    rows = [build_example_curvature_audit_row(example_id) for example_id in ids]
    rows.sort(key=lambda row: row["example_id"])
    rows_by_id = {row["example_id"]: row for row in rows}

    confluent_ids = [row["example_id"] for row in rows if row["global"]["confluent"]]
    nonconfluent_ids = [row["example_id"] for row in rows if not row["global"]["confluent"]]
    reachable_obstructions = [
        row["example_id"]
        for row in rows
        if row["critical_pairs"]["reachable_critical_pair_has_obstruction"]
    ]
    local_obstructions = [
        row["example_id"] for row in rows if row["local_peaks"]["local_peak_has_obstruction"]
    ]

    findings = {
        "all_examples_terminating": all(row["global"]["terminating"] for row in rows),
        "all_examples_exploration_complete": all(
            row["global"]["exploration_complete"] for row in rows
        ),
        "all_examples_reachable_cross_check_match": all(
            row["alignment"]["reachable_cross_check_match"] for row in rows
        ),
        "all_examples_support_curvature_generator_story": all(
            row["curvature_generator_story_supported"] for row in rows
        ),
        "confluent_example_ids": confluent_ids,
        "nonconfluent_example_ids": nonconfluent_ids,
        "examples_with_reachable_critical_pair_obstructions": reachable_obstructions,
        "examples_with_local_peak_obstructions": local_obstructions,
    }

    return {
        "schema_version": 1,
        "kind": "critical_pair_curvature_audit",
        "examples": rows,
        "completion_pair_delta": _completion_pair_delta(rows_by_id),
        "findings": findings,
    }
