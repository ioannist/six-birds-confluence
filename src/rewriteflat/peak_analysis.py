"""Peak-level defect analysis for finite ARS examples."""

from __future__ import annotations

from collections import deque
from typing import Any

from .finite_ars import FiniteARS


def _distance_map(ars: FiniteARS, start: str) -> dict[str, int]:
    distances: dict[str, int] = {start: 0}
    queue: deque[str] = deque([start])
    while queue:
        current = queue.popleft()
        base = distances[current]
        for nxt in ars.successors(current):
            if nxt in distances:
                continue
            distances[nxt] = base + 1
            queue.append(nxt)
    return distances


def analyze_peak(ars: FiniteARS, source: str, left: str, right: str) -> dict[str, Any]:
    terminating = ars.is_terminating()
    joinable = ars.joinable(left, right)
    left_nf = sorted(ars.reachable_normal_forms(left))
    right_nf = sorted(ars.reachable_normal_forms(right))
    left_nf_set = set(left_nf)
    right_nf_set = set(right_nf)

    if terminating:
        nf_outcome_mismatch: bool | None = left_nf_set != right_nf_set
        nf_sym_diff_size: int | None = len(left_nf_set.symmetric_difference(right_nf_set))
    else:
        nf_outcome_mismatch = None
        nf_sym_diff_size = None

    record: dict[str, Any] = {
        "source": source,
        "left": left,
        "right": right,
        "joinable": joinable,
        "nonjoinability_defect": not joinable,
        "left_reachable_normal_forms": left_nf,
        "right_reachable_normal_forms": right_nf,
        "nf_outcome_mismatch": nf_outcome_mismatch,
        "nf_symmetric_difference_size": nf_sym_diff_size,
    }

    if joinable:
        left_dist = _distance_map(ars, left)
        right_dist = _distance_map(ars, right)
        witnesses = sorted(set(left_dist) & set(right_dist))
        if witnesses:
            best = min(left_dist[w] + right_dist[w] for w in witnesses)
            best_witnesses = [w for w in witnesses if left_dist[w] + right_dist[w] == best]
            record["shortest_join_witness_total_distance"] = best
            record["shortest_join_witnesses"] = best_witnesses
        else:
            record["shortest_join_witness_total_distance"] = None
            record["shortest_join_witnesses"] = []
    else:
        record["shortest_join_witness_total_distance"] = None
        record["shortest_join_witnesses"] = []

    return record


def analyze_all_peaks(ars: FiniteARS) -> list[dict[str, Any]]:
    peaks = sorted(ars.local_peaks(), key=lambda item: (item[0], item[1], item[2]))
    return [analyze_peak(ars, source, left, right) for source, left, right in peaks]


def build_peak_artifact(example_id: str, ars: FiniteARS) -> dict[str, Any]:
    peaks = analyze_all_peaks(ars)

    nonjoinability_count = sum(1 for peak in peaks if peak["nonjoinability_defect"])
    nf_mismatch_count = sum(1 for peak in peaks if peak["nf_outcome_mismatch"] is True)

    return {
        "schema_version": 1,
        "kind": "finite_ars_peak_analysis",
        "example_id": example_id,
        "state_count": len(ars.states),
        "edge_count": len(ars.edges),
        "terminating": ars.is_terminating(),
        "peak_count": len(peaks),
        "defect_counts": {
            "nonjoinability_defect": nonjoinability_count,
            "nf_outcome_mismatch": nf_mismatch_count,
        },
        "peaks": peaks,
    }
