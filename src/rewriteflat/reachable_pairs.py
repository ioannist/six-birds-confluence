"""Concrete reachable overlap branchings, including contexts and instances.

Disjoint redexes and variable-position overlaps are not critical overlaps.
Consequently these signatures need not equal all graph-peak signatures.
"""

from itertools import combinations
from typing import Any

from .finite_ars import FiniteARS
from .peak_analysis import analyze_peak


def require_complete(exploration: dict[str, Any]) -> None:
    if not exploration["exploration_complete"]:
        raise ValueError("critical-pair certification requires complete exploration; "
                         "increase bounds (absence of a bounded witness is inconclusive)")


def reachable_overlap_pairs(system: Any, exploration: dict[str, Any], *,
                            terms: bool = False) -> list[dict[str, Any]]:
    require_complete(exploration)
    ars = FiniteARS(exploration["states"], exploration["edges"])
    signatures: dict[tuple[str, str, str], list[dict[str, Any]]] = {}
    for source in exploration["states"]:
        if terms:
            from .term_rewriting import Var, get_subterm, parse_term
            steps = system.one_step_matches(parse_term(source))
        else:
            steps = system.one_step_matches(source)
        for left, right in combinations(steps, 2):
            if left["target"] == right["target"]:
                continue
            if terms:
                outer, inner = left, right
                p, q = tuple(outer["position"]), tuple(inner["position"])
                if len(p) > len(q):
                    outer, inner, p, q = right, left, q, p
                if q[:len(p)] != p:
                    continue
                relative = q[len(p):]
                try:
                    pattern = get_subterm(system.rules[outer["rule_index"]].lhs, relative)
                except ValueError:
                    # The inner redex lies inside a substituted variable.
                    continue
                if isinstance(pattern, Var):
                    continue
            else:
                p, q = left["position"], right["position"]
                if max(p, q) >= min(p + len(left["lhs"]), q + len(right["lhs"])):
                    continue
            b, c = sorted([left["target"], right["target"]])
            signatures.setdefault((source, b, c), []).append({
                "left_rule_index": left["rule_index"],
                "right_rule_index": right["rule_index"],
                "left_position": left["position"], "right_position": right["position"],
            })
    records = []
    for index, ((source, b, c), instances) in enumerate(sorted(signatures.items()), 1):
        metrics = analyze_peak(ars, source, b, c)
        records.append({
            "cp_id" if terms else "critical_pair_id": f"RCP{index:04d}",
            "source_term" if terms else "source_word": source,
            "left_branch_term": b, "right_branch_term": c,
            "overlap_instances": instances,
            "source_reachable_from_starts" if terms else
                "source_reachable_from_example_starts": True,
            "graph_peak_present_from_starts" if terms else
                "graph_peak_present_from_example_starts": True,
            "local_exploration_complete": True,
            **{k: v for k, v in metrics.items() if k not in {"source", "left", "right"}},
        })
    return records
