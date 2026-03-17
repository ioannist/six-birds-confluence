"""Reduction 2-complex / elementary holonomy artifacts for selected examples."""

from __future__ import annotations

import csv
import json
from collections import deque
from pathlib import Path
from typing import Any

from .critical_pairs import build_critical_pair_artifact
from .example_io import load_finite_ars, load_string_rewrite_system
from .peak_analysis import analyze_peak
from .term_rewriting import (
    TermRewriteSystem,
    build_term_rewrite_artifact,
    load_term_rewrite_example,
)


ROOT = Path(__file__).resolve().parents[2]
OUT_DIR = ROOT / "results" / "two_complex"

SELECTED_EXAMPLES = [
    "E001_diamond_flat",
    "E002_fork_curved",
    "E007_completion_before",
    "E008_completion_after",
    "TRS003_nested_overlap_nonconfluent",
    "TRS004_nested_overlap_joinable",
]


def _cp_signature(source: str, left: str, right: str) -> tuple[str, tuple[str, str]]:
    b1, b2 = sorted([left, right])
    return (source, (b1, b2))


def _distance_map(adjacency: dict[str, list[str]], start: str) -> dict[str, int]:
    distances = {start: 0}
    q: deque[str] = deque([start])
    while q:
        cur = q.popleft()
        base = distances[cur]
        for nxt in adjacency.get(cur, []):
            if nxt in distances:
                continue
            distances[nxt] = base + 1
            q.append(nxt)
    return distances


def _shortest_path(adjacency: dict[str, list[str]], start: str, target: str) -> list[str]:
    if start == target:
        return [start]
    parents: dict[str, str | None] = {start: None}
    q: deque[str] = deque([start])
    while q:
        cur = q.popleft()
        for nxt in adjacency.get(cur, []):
            if nxt in parents:
                continue
            parents[nxt] = cur
            if nxt == target:
                q.clear()
                break
            q.append(nxt)
    if target not in parents:
        raise ValueError(f"no path from {start} to {target}")
    path = [target]
    cur = target
    while parents[cur] is not None:
        cur = parents[cur]  # type: ignore[index]
        path.append(cur)
    path.reverse()
    return path


def _choose_join_witness(states: list[str], edges: list[tuple[str, str]], left: str, right: str) -> str | None:
    adjacency: dict[str, list[str]] = {s: [] for s in states}
    for src, dst in sorted(edges):
        adjacency[src].append(dst)
    for key in adjacency:
        adjacency[key] = sorted(adjacency[key])

    left_dist = _distance_map(adjacency, left)
    right_dist = _distance_map(adjacency, right)
    common = sorted(set(left_dist) & set(right_dist))
    if not common:
        return None
    best = min(left_dist[w] + right_dist[w] for w in common)
    candidates = [w for w in common if left_dist[w] + right_dist[w] == best]
    return sorted(candidates)[0]


def _filler_paths(states: list[str], edges: list[tuple[str, str]], left: str, right: str, witness: str | None) -> tuple[list[str], list[str]]:
    if witness is None:
        return [], []
    adjacency: dict[str, list[str]] = {s: [] for s in states}
    for src, dst in sorted(edges):
        adjacency[src].append(dst)
    for key in adjacency:
        adjacency[key] = sorted(adjacency[key])
    return _shortest_path(adjacency, left, witness), _shortest_path(adjacency, right, witness)


def _holonomy_status(joinable: bool, nf_mismatch: bool) -> tuple[str, str | None]:
    if joinable and not nf_mismatch:
        return "trivial", None
    if not joinable:
        return "nontrivial", "nonjoinable"
    return "nontrivial", "nf_outcome_mismatch"


def _build_finite_ars_artifact(example_id: str) -> dict[str, Any]:
    ars = load_finite_ars(ROOT / "data" / "examples" / f"{example_id}.yaml")
    states = sorted(ars.states)
    edges = sorted(ars.edges)

    one_cells = [
        {
            "one_cell_id": f"C1_{idx:04d}",
            "source": src,
            "target": dst,
        }
        for idx, (src, dst) in enumerate(edges, start=1)
    ]

    peaks = sorted(ars.local_peaks(), key=lambda x: (x[0], x[1], x[2]))
    two_cells = []
    for idx, (source, left, right) in enumerate(peaks, start=1):
        metrics = analyze_peak(ars, source, left, right)
        joinable = bool(metrics["joinable"])
        nf_mismatch = metrics["nf_outcome_mismatch"] is True
        witness = _choose_join_witness(states, edges, left, right) if joinable else None
        lf, rf = _filler_paths(states, edges, left, right, witness)
        status, defect_kind = _holonomy_status(joinable, nf_mismatch)
        two_cells.append(
            {
                "two_cell_id": f"C2_{idx:04d}",
                "generator_kind": "local_peak",
                "source_0cell": source,
                "left_branch_0cell": left,
                "right_branch_0cell": right,
                "boundary": {
                    "left_edge_path_states": [source, left],
                    "right_edge_path_states": [source, right],
                    "left_filler_path_states": lf,
                    "right_filler_path_states": rf,
                },
                "join_witness": witness,
                "elementary_holonomy_status": status,
                "holonomy_defect_kind": defect_kind,
                "nonjoinability_defect": bool(metrics["nonjoinability_defect"]),
                "nf_outcome_mismatch": nf_mismatch,
            }
        )

    return _finalize_artifact(example_id, "finite_ars", states, one_cells, two_cells)


def _build_string_artifact(example_id: str) -> dict[str, Any]:
    example, system = load_string_rewrite_system(ROOT / "data" / "examples" / f"{example_id}.yaml")
    bounds = example["bounds"]
    exploration = system.explore_bounded(
        start_strings=example["start_strings"],
        max_depth=bounds["max_depth"],
        max_states=bounds["max_states"],
        max_word_length=bounds.get("max_word_length"),
    )
    states = list(exploration["states"])
    edges = [tuple(edge) for edge in exploration["edges"]]

    one_cells = [
        {
            "one_cell_id": f"C1_{idx:04d}",
            "source": src,
            "target": dst,
        }
        for idx, (src, dst) in enumerate(sorted(edges), start=1)
    ]

    cp_art = build_critical_pair_artifact(example_id, example, system)
    reachable = [cp for cp in cp_art["critical_pairs"] if cp["source_reachable_from_example_starts"]]
    reachable.sort(key=lambda cp: (cp["source_word"], cp["left_branch_term"], cp["right_branch_term"], cp["critical_pair_id"]))

    two_cells = []
    for idx, cp in enumerate(reachable, start=1):
        source = cp["source_word"]
        left = cp["left_branch_term"]
        right = cp["right_branch_term"]
        joinable = bool(cp["joinable"])
        nf_mismatch = cp.get("nf_outcome_mismatch") is True
        witness = _choose_join_witness(states, edges, left, right) if joinable else None
        lf, rf = _filler_paths(states, edges, left, right, witness)
        status, defect_kind = _holonomy_status(joinable, nf_mismatch)
        two_cells.append(
            {
                "two_cell_id": f"C2_{idx:04d}",
                "generator_kind": "reachable_critical_pair",
                "source_0cell": source,
                "left_branch_0cell": left,
                "right_branch_0cell": right,
                "boundary": {
                    "left_edge_path_states": [source, left],
                    "right_edge_path_states": [source, right],
                    "left_filler_path_states": lf,
                    "right_filler_path_states": rf,
                },
                "join_witness": witness,
                "elementary_holonomy_status": status,
                "holonomy_defect_kind": defect_kind,
                "nonjoinability_defect": bool(cp["nonjoinability_defect"]),
                "nf_outcome_mismatch": nf_mismatch,
            }
        )

    return _finalize_artifact(example_id, "string_rewrite", sorted(states), one_cells, two_cells)


def _build_term_artifact(example_id: str) -> dict[str, Any]:
    example = load_term_rewrite_example(ROOT / "data" / "examples" / "term_rewrite" / f"{example_id}.yaml")
    system = TermRewriteSystem(example["rules"])
    bounds = example["bounds"]
    exploration = system.explore_bounded(
        start_terms=example["start_terms"],
        max_depth=bounds["max_depth"],
        max_states=bounds["max_states"],
        max_term_nodes=bounds.get("max_term_nodes"),
    )
    states = list(exploration["states"])
    edges = [tuple(edge) for edge in exploration["edges"]]

    one_cells = [
        {
            "one_cell_id": f"C1_{idx:04d}",
            "source": src,
            "target": dst,
        }
        for idx, (src, dst) in enumerate(sorted(edges), start=1)
    ]

    cp_art = build_term_rewrite_artifact(example_id, example)
    reachable = [cp for cp in cp_art["critical_pairs"] if cp["source_reachable_from_starts"]]
    reachable.sort(key=lambda cp: (cp["source_term"], cp["left_branch_term"], cp["right_branch_term"], cp["cp_id"]))

    two_cells = []
    for idx, cp in enumerate(reachable, start=1):
        source = cp["source_term"]
        left = cp["left_branch_term"]
        right = cp["right_branch_term"]
        joinable = bool(cp["joinable"])
        nf_mismatch = cp.get("nf_outcome_mismatch") is True
        witness = _choose_join_witness(states, edges, left, right) if joinable else None
        lf, rf = _filler_paths(states, edges, left, right, witness)
        status, defect_kind = _holonomy_status(joinable, nf_mismatch)
        two_cells.append(
            {
                "two_cell_id": f"C2_{idx:04d}",
                "generator_kind": "reachable_critical_pair",
                "source_0cell": source,
                "left_branch_0cell": left,
                "right_branch_0cell": right,
                "boundary": {
                    "left_edge_path_states": [source, left],
                    "right_edge_path_states": [source, right],
                    "left_filler_path_states": lf,
                    "right_filler_path_states": rf,
                },
                "join_witness": witness,
                "elementary_holonomy_status": status,
                "holonomy_defect_kind": defect_kind,
                "nonjoinability_defect": bool(cp["nonjoinability_defect"]),
                "nf_outcome_mismatch": nf_mismatch,
            }
        )

    return _finalize_artifact(example_id, "term_rewrite", sorted(states), one_cells, two_cells)


def _finalize_artifact(example_id: str, domain: str, zero_cells: list[str], one_cells: list[dict[str, Any]], two_cells: list[dict[str, Any]]) -> dict[str, Any]:
    holonomy_counts = {
        "trivial": sum(1 for c in two_cells if c["elementary_holonomy_status"] == "trivial"),
        "nontrivial": sum(1 for c in two_cells if c["elementary_holonomy_status"] == "nontrivial"),
        "nonjoinable": sum(1 for c in two_cells if c["nonjoinability_defect"]),
        "nf_outcome_mismatch": sum(1 for c in two_cells if c["nf_outcome_mismatch"]),
    }
    return {
        "schema_version": 1,
        "kind": "reduction_two_complex",
        "example_id": example_id,
        "domain": domain,
        "zero_cells": sorted(zero_cells),
        "one_cells": one_cells,
        "two_cell_count": len(two_cells),
        "two_cells": two_cells,
        "holonomy_counts": holonomy_counts,
    }


def build_two_complex_artifact(example_id: str) -> dict[str, Any]:
    if example_id in {"E001_diamond_flat", "E002_fork_curved"}:
        return _build_finite_ars_artifact(example_id)
    if example_id in {"E007_completion_before", "E008_completion_after"}:
        return _build_string_artifact(example_id)
    if example_id in {"TRS003_nested_overlap_nonconfluent", "TRS004_nested_overlap_joinable"}:
        return _build_term_artifact(example_id)
    raise ValueError(f"unsupported selected example: {example_id}")


def build_selected_two_complex_artifacts(example_ids: list[str] | None = None) -> dict[str, Any]:
    selected = SELECTED_EXAMPLES if example_ids is None else list(example_ids)
    artifacts = [build_two_complex_artifact(eid) for eid in selected]

    examples_summary = [
        {
            "example_id": a["example_id"],
            "domain": a["domain"],
            "two_cell_count": a["two_cell_count"],
            "trivial_count": a["holonomy_counts"]["trivial"],
            "nontrivial_count": a["holonomy_counts"]["nontrivial"],
            "nonjoinable_count": a["holonomy_counts"]["nonjoinable"],
            "nf_outcome_mismatch_count": a["holonomy_counts"]["nf_outcome_mismatch"],
        }
        for a in artifacts
    ]

    by_id = {a["example_id"]: a for a in artifacts}

    string_before = by_id["E007_completion_before"]
    string_after = by_id["E008_completion_after"]
    trs_before = by_id["TRS003_nested_overlap_nonconfluent"]
    trs_after = by_id["TRS004_nested_overlap_joinable"]

    pair_deltas = [
        {
            "pair_id": "string_completion_pair",
            "before_example_id": "E007_completion_before",
            "after_example_id": "E008_completion_after",
            "before_nontrivial_count": string_before["holonomy_counts"]["nontrivial"],
            "after_nontrivial_count": string_after["holonomy_counts"]["nontrivial"],
            "holonomy_elimination_observed": string_before["holonomy_counts"]["nontrivial"] > 0
            and string_after["holonomy_counts"]["nontrivial"] == 0,
        },
        {
            "pair_id": "trs_nested_overlap_pair",
            "before_example_id": "TRS003_nested_overlap_nonconfluent",
            "after_example_id": "TRS004_nested_overlap_joinable",
            "before_nontrivial_count": trs_before["holonomy_counts"]["nontrivial"],
            "after_nontrivial_count": trs_after["holonomy_counts"]["nontrivial"],
            "holonomy_elimination_observed": trs_before["holonomy_counts"]["nontrivial"] > 0
            and trs_after["holonomy_counts"]["nontrivial"] == 0,
        },
    ]

    findings = {
        "all_selected_examples_generated": set(selected) == set(SELECTED_EXAMPLES),
        "all_joinable_two_cells_trivial": all(
            (cell["join_witness"] is None) or (cell["elementary_holonomy_status"] == "trivial")
            for art in artifacts
            for cell in art["two_cells"]
        ),
        "all_defective_two_cells_nontrivial": all(
            (not cell["nonjoinability_defect"] and not cell["nf_outcome_mismatch"])
            or (cell["elementary_holonomy_status"] == "nontrivial")
            for art in artifacts
            for cell in art["two_cells"]
        ),
        "string_pair_holonomy_elimination_observed": pair_deltas[0]["holonomy_elimination_observed"],
        "trs_pair_holonomy_elimination_observed": pair_deltas[1]["holonomy_elimination_observed"],
    }

    summary = {
        "schema_version": 1,
        "kind": "reduction_two_complex_summary",
        "examples": examples_summary,
        "pair_deltas": pair_deltas,
        "findings": findings,
    }

    return {
        "artifacts": artifacts,
        "summary": summary,
    }


def write_two_complex_artifacts(example_ids: list[str] | None = None) -> dict[str, Any]:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    built = build_selected_two_complex_artifacts(example_ids=example_ids)

    artifact_paths: list[str] = []
    for artifact in built["artifacts"]:
        path = OUT_DIR / f"{artifact['example_id']}.json"
        path.write_text(json.dumps(artifact, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        artifact_paths.append(path.as_posix())

    summary_json_path = OUT_DIR / "summary.json"
    summary_csv_path = OUT_DIR / "summary.csv"

    summary = built["summary"]
    summary_json_path.write_text(json.dumps(summary, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    fields = [
        "example_id",
        "domain",
        "two_cell_count",
        "trivial_count",
        "nontrivial_count",
        "nonjoinable_count",
        "nf_outcome_mismatch_count",
    ]
    with summary_csv_path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        for row in summary["examples"]:
            writer.writerow({f: row[f] for f in fields})

    return {
        "artifact_paths": artifact_paths,
        "summary_json_path": summary_json_path.as_posix(),
        "summary_csv_path": summary_csv_path.as_posix(),
        "summary": summary,
    }
