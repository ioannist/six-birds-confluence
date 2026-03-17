"""Plaquette artifact builders for finite ARS local peaks."""

from __future__ import annotations

from collections import deque
from typing import Any

from .finite_ars import FiniteARS
from .peak_analysis import analyze_all_peaks


def _distance_map(ars: FiniteARS, start: str) -> dict[str, int]:
    distances: dict[str, int] = {start: 0}
    queue: deque[str] = deque([start])
    while queue:
        current = queue.popleft()
        base = distances[current]
        for nxt in sorted(ars.successors(current)):
            if nxt in distances:
                continue
            distances[nxt] = base + 1
            queue.append(nxt)
    return distances


def _shortest_path_states(ars: FiniteARS, start: str, target: str) -> list[str]:
    if start == target:
        return [start]

    queue: deque[str] = deque([start])
    parents: dict[str, str | None] = {start: None}

    while queue:
        current = queue.popleft()
        for nxt in sorted(ars.successors(current)):
            if nxt in parents:
                continue
            parents[nxt] = current
            if nxt == target:
                queue.clear()
                break
            queue.append(nxt)

    if target not in parents:
        raise ValueError(f"no path from {start} to {target}")

    path_rev = [target]
    current = target
    while parents[current] is not None:
        current = parents[current]
        path_rev.append(current)
    return list(reversed(path_rev))


def _choose_join_witness(ars: FiniteARS, left: str, right: str) -> dict[str, Any] | None:
    left_dist = _distance_map(ars, left)
    right_dist = _distance_map(ars, right)
    common = sorted(set(left_dist) & set(right_dist))
    if not common:
        return None

    best_total = min(left_dist[state] + right_dist[state] for state in common)
    candidates = [state for state in common if left_dist[state] + right_dist[state] == best_total]
    witness = sorted(candidates)[0]

    left_path = _shortest_path_states(ars, left, witness)
    right_path = _shortest_path_states(ars, right, witness)
    return {
        "state": witness,
        "left_path_states": left_path,
        "right_path_states": right_path,
        "total_distance": best_total,
    }


def build_plaquette_record(ars: FiniteARS, peak_record: dict[str, Any], index: int) -> dict[str, Any]:
    source = peak_record["source"]
    left = peak_record["left"]
    right = peak_record["right"]
    witness = _choose_join_witness(ars, left, right)
    joinable = witness is not None

    return {
        "plaquette_id": f"P{index:04d}",
        "source": source,
        "left_branch_edge": [source, left],
        "right_branch_edge": [source, right],
        "status": "joinable" if joinable else "defective",
        "join_witness": witness,
        "defect_label": None if joinable else "nonjoinable_peak",
    }


def build_all_plaquettes(ars: FiniteARS) -> list[dict[str, Any]]:
    peaks = analyze_all_peaks(ars)
    return [build_plaquette_record(ars, peak, i) for i, peak in enumerate(peaks, start=1)]


def build_plaquette_artifact(example_id: str, ars: FiniteARS) -> dict[str, Any]:
    plaquettes = build_all_plaquettes(ars)
    joinable_count = sum(1 for p in plaquettes if p["status"] == "joinable")
    defective_count = sum(1 for p in plaquettes if p["status"] == "defective")

    return {
        "schema_version": 1,
        "kind": "finite_ars_plaquettes",
        "example_id": example_id,
        "state_count": len(ars.states),
        "edge_count": len(ars.edges),
        "terminating": ars.is_terminating(),
        "plaquette_count": len(plaquettes),
        "defect_counts": {"joinable": joinable_count, "defective": defective_count},
        "plaquettes": plaquettes,
    }
