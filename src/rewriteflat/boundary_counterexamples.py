"""Boundary counterexample search beyond safe finite-ARS hypotheses."""

from __future__ import annotations

import time
from collections import deque
from itertools import combinations
from typing import Any

from .exhaustive_finite_ars_audit import enumerate_labeled_finite_ars
from .finite_ars import FiniteARS
from .naive_graph_audit import has_directed_cycle, naive_directed_loop_flat, undirected_cycle_rank
from .peak_analysis import analyze_all_peaks


OVERCLAIM_IDS = [
    "O001_local_flatness_implies_confluence_without_termination",
    "O002_confluence_implies_normalizing",
    "O003_unique_reachable_normal_forms_implies_confluence_without_termination",
    "O004_naive_nf_peak_flatness_implies_local_flatness_without_termination",
    "O005_naive_graph_flatness_false_positive",
    "O006_naive_graph_flatness_false_negative",
]


def _shortest_paths_from(ars: FiniteARS, source: str) -> tuple[dict[str, int], dict[str, list[str]]]:
    dist = {source: 0}
    path = {source: [source]}
    queue: deque[str] = deque([source])

    while queue:
        node = queue.popleft()
        for nxt in sorted(ars.successors(node)):
            if nxt in dist:
                continue
            dist[nxt] = dist[node] + 1
            path[nxt] = path[node] + [nxt]
            queue.append(nxt)

    return dist, path


def _shortest_path(ars: FiniteARS, source: str, target: str) -> list[str] | None:
    if source == target:
        return [source]
    _, paths = _shortest_paths_from(ars, source)
    return paths.get(target)


def is_normalizing(ars: FiniteARS) -> bool:
    return all(len(ars.reachable_normal_forms(state)) > 0 for state in ars.states)


def naive_nf_peak_flatness(ars: FiniteARS) -> bool:
    for source, left, right in sorted(ars.local_peaks(), key=lambda item: (item[0], item[1], item[2])):
        left_nf = ars.reachable_normal_forms(left)
        right_nf = ars.reachable_normal_forms(right)
        if left_nf != right_nf:
            return False
    return True


def find_minimal_nonconfluence_witness(ars: FiniteARS) -> dict[str, Any] | None:
    best: tuple[tuple[int, str, str, str], dict[str, Any]] | None = None
    for source in sorted(ars.states):
        dist, paths = _shortest_paths_from(ars, source)
        reachable = sorted(dist.keys())
        for left, right in combinations(reachable, 2):
            if ars.joinable(left, right):
                continue
            key = (dist[left] + dist[right], source, left, right)
            record = {
                "source_state": source,
                "left_state": left,
                "right_state": right,
                "left_path_states": paths[left],
                "right_path_states": paths[right],
            }
            if best is None or key < best[0]:
                best = (key, record)
    return None if best is None else best[1]


def find_minimal_defective_peak(ars: FiniteARS) -> dict[str, Any] | None:
    for peak in analyze_all_peaks(ars):
        if peak["nonjoinability_defect"]:
            return {
                "source": peak["source"],
                "left": peak["left"],
                "right": peak["right"],
                "left_reachable_normal_forms": peak["left_reachable_normal_forms"],
                "right_reachable_normal_forms": peak["right_reachable_normal_forms"],
            }
    return None


def find_minimal_directed_cycle(ars: FiniteARS) -> dict[str, Any] | None:
    best: tuple[tuple[int, tuple[str, ...]], dict[str, Any]] | None = None
    for start in sorted(ars.states):
        if start in ars.successors(start):
            cycle_path = [start, start]
            key = (1, tuple(cycle_path))
            record = {"cycle_path_states": cycle_path, "cycle_length": 1}
            if best is None or key < best[0]:
                best = (key, record)
        for nxt in sorted(ars.successors(start)):
            if nxt == start:
                continue
            tail = _shortest_path(ars, nxt, start)
            if tail is None:
                continue
            cycle_path = [start] + tail
            length = len(cycle_path) - 1
            key = (length, tuple(cycle_path))
            record = {"cycle_path_states": cycle_path, "cycle_length": length}
            if best is None or key < best[0]:
                best = (key, record)
    return None if best is None else best[1]


def _state_without_reachable_normal_forms(ars: FiniteARS) -> str | None:
    for state in sorted(ars.states):
        if len(ars.reachable_normal_forms(state)) == 0:
            return state
    return None


def _build_metrics(ars: FiniteARS) -> dict[str, Any]:
    peaks = analyze_all_peaks(ars)
    nonjoinability_defect_count = sum(1 for peak in peaks if peak["nonjoinability_defect"])
    nf_outcome_mismatch_count = sum(1 for peak in peaks if peak["nf_outcome_mismatch"] is True)
    local_flatness = nonjoinability_defect_count == 0
    cycle = has_directed_cycle(ars)

    return {
        "terminating": ars.is_terminating(),
        "normalizing": is_normalizing(ars),
        "peak_count": len(peaks),
        "nonjoinability_defect_count": nonjoinability_defect_count,
        "nf_outcome_mismatch_count": nf_outcome_mismatch_count,
        "local_flatness": local_flatness,
        "locally_confluent": ars.is_locally_confluent(),
        "confluent": ars.is_confluent(),
        "unique_reachable_normal_forms": ars.has_unique_reachable_normal_forms(),
        "naive_nf_peak_flatness": naive_nf_peak_flatness(ars),
        "has_directed_cycle": cycle,
        "naive_directed_loop_flat": not cycle,
        "undirected_cycle_rank": undirected_cycle_rank(ars),
    }


def _overclaim_predicates(metrics: dict[str, Any]) -> dict[str, bool]:
    return {
        OVERCLAIM_IDS[0]: (
            (not metrics["terminating"])
            and metrics["local_flatness"]
            and metrics["locally_confluent"]
            and (not metrics["confluent"])
        ),
        OVERCLAIM_IDS[1]: metrics["confluent"] and (not metrics["normalizing"]),
        OVERCLAIM_IDS[2]: (
            (not metrics["terminating"])
            and metrics["unique_reachable_normal_forms"]
            and (not metrics["confluent"])
        ),
        OVERCLAIM_IDS[3]: (
            (not metrics["terminating"])
            and metrics["naive_nf_peak_flatness"]
            and (not metrics["local_flatness"])
        ),
        OVERCLAIM_IDS[4]: metrics["naive_directed_loop_flat"] and (not metrics["confluent"]),
        OVERCLAIM_IDS[5]: (not metrics["naive_directed_loop_flat"]) and metrics["confluent"],
    }


def _build_witness(
    witness_id: str, overclaim_id: str, system_id: str, ars: FiniteARS, metrics: dict[str, Any]
) -> dict[str, Any]:
    return {
        "witness_id": witness_id,
        "overclaim_id": overclaim_id,
        "status": "found",
        "system_id": system_id,
        "n_states": len(ars.states),
        "states": list(ars.states),
        "edges": [[src, dst] for src, dst in ars.edges],
        "metrics": metrics,
        "summary": {
            "nonconfluence_witness": find_minimal_nonconfluence_witness(ars),
            "defective_peak": find_minimal_defective_peak(ars),
            "directed_cycle_witness": find_minimal_directed_cycle(ars),
            "state_without_reachable_normal_forms": _state_without_reachable_normal_forms(ars),
        },
    }


def build_boundary_counterexample_artifact(max_states: int = 4) -> dict[str, Any]:
    if max_states <= 0:
        raise ValueError("max_states must be positive")

    started = time.perf_counter()
    best_by_overclaim: dict[str, tuple[tuple[int, int, str], str, FiniteARS, dict[str, Any]]] = {}

    for n_states in range(1, max_states + 1):
        for system_id, ars in enumerate_labeled_finite_ars(n_states):
            metrics = _build_metrics(ars)
            predicates = _overclaim_predicates(metrics)
            for overclaim_id in OVERCLAIM_IDS:
                if not predicates[overclaim_id]:
                    continue
                key = (n_states, len(ars.edges), system_id)
                current = best_by_overclaim.get(overclaim_id)
                if current is None or key < current[0]:
                    best_by_overclaim[overclaim_id] = (key, system_id, ars, metrics)

    overclaims: list[dict[str, Any]] = []
    witness_counter = 1
    for overclaim_id in OVERCLAIM_IDS:
        chosen = best_by_overclaim.get(overclaim_id)
        if chosen is None:
            overclaims.append({"overclaim_id": overclaim_id, "status": "none", "witness": None})
            continue

        _, system_id, ars, metrics = chosen
        witness_id = f"W{witness_counter:03d}"
        witness_counter += 1
        witness = _build_witness(witness_id, overclaim_id, system_id, ars, metrics)
        overclaims.append({"overclaim_id": overclaim_id, "status": "found", "witness": witness})

    return {
        "schema_version": 1,
        "kind": "boundary_counterexample_search",
        "search_space": {
            "max_states": max_states,
            "include_self_loops": True,
            "state_naming": "s0..s{n-1}",
        },
        "runtime_seconds": time.perf_counter() - started,
        "overclaims": overclaims,
    }
