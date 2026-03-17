"""Naive bare-graph flatness audit for finite ARS examples."""

from __future__ import annotations

from collections import deque
from typing import Any, Iterable

from .finite_ars import FiniteARS
from .peak_analysis import analyze_all_peaks


def has_directed_cycle(ars: FiniteARS) -> bool:
    return not ars.is_terminating()


def naive_directed_loop_flat(ars: FiniteARS) -> bool:
    return not has_directed_cycle(ars)


def undirected_cycle_rank(ars: FiniteARS) -> int:
    states = list(ars.states)
    state_set = set(states)

    neighbors: dict[str, set[str]] = {state: set() for state in states}
    undirected_edges: set[tuple[str, str]] = set()
    for src, dst in ars.edges:
        if src == dst:
            continue
        left, right = (src, dst) if src < dst else (dst, src)
        undirected_edges.add((left, right))
        neighbors[src].add(dst)
        neighbors[dst].add(src)

    visited: set[str] = set()
    components = 0
    for start in states:
        if start in visited:
            continue
        components += 1
        queue: deque[str] = deque([start])
        visited.add(start)
        while queue:
            current = queue.popleft()
            for nxt in sorted(neighbors[current]):
                if nxt in visited or nxt not in state_set:
                    continue
                visited.add(nxt)
                queue.append(nxt)

    return len(undirected_edges) - len(states) + components


def build_naive_graph_audit_row(example_id: str, ars: FiniteARS) -> dict[str, Any]:
    peaks = analyze_all_peaks(ars)
    nonjoinability_defect_count = sum(1 for peak in peaks if peak["nonjoinability_defect"])
    nf_outcome_mismatch_count = sum(1 for peak in peaks if peak["nf_outcome_mismatch"] is True)

    directed_cycle = has_directed_cycle(ars)
    return {
        "example_id": example_id,
        "terminating": ars.is_terminating(),
        "has_directed_cycle": directed_cycle,
        "naive_directed_loop_flat": not directed_cycle,
        "undirected_cycle_rank": undirected_cycle_rank(ars),
        "peak_count": len(peaks),
        "nonjoinability_defect_count": nonjoinability_defect_count,
        "nf_outcome_mismatch_count": nf_outcome_mismatch_count,
        "locally_confluent": ars.is_locally_confluent(),
        "confluent": ars.is_confluent(),
    }


def build_naive_graph_audit(example_specs: Iterable[tuple[str, FiniteARS]]) -> dict[str, Any]:
    rows = [build_naive_graph_audit_row(example_id, ars) for example_id, ars in example_specs]
    rows.sort(key=lambda row: row["example_id"])

    findings = {
        "all_curated_examples_terminating": all(row["terminating"] for row in rows),
        "all_curated_examples_naively_flat": all(row["naive_directed_loop_flat"] for row in rows),
        "nonconfluent_but_naively_flat_example_ids": [
            row["example_id"]
            for row in rows
            if row["naive_directed_loop_flat"] and not row["confluent"]
        ],
        "zero_undirected_cycle_rank_but_nonconfluent_example_ids": [
            row["example_id"]
            for row in rows
            if row["undirected_cycle_rank"] == 0 and not row["confluent"]
        ],
        "positive_undirected_cycle_rank_and_confluent_example_ids": [
            row["example_id"]
            for row in rows
            if row["undirected_cycle_rank"] > 0 and row["confluent"]
        ],
    }

    return {
        "schema_version": 1,
        "kind": "naive_bare_graph_flatness_audit",
        "examples": rows,
        "findings": findings,
    }
