"""Critical-pair enumeration and bounded analysis for string rewrite systems."""

from __future__ import annotations

from collections import defaultdict
from typing import Any

from .peak_analysis import analyze_all_peaks, analyze_peak
from .string_rewriting import StringRewriteSystem, finite_ars_from_exploration


def _apply_at(word: str, start: int, lhs: str, rhs: str) -> str:
    end = start + len(lhs)
    if word[start:end] != lhs:
        raise ValueError("lhs does not match at given position")
    return word[:start] + rhs + word[end:]


def _build_overlap_instance(
    left_rule_index: int,
    right_rule_index: int,
    left_lhs: str,
    left_rhs: str,
    right_lhs: str,
    right_rhs: str,
    relative_offset: int,
) -> dict[str, Any] | None:
    placed: dict[int, str] = {}
    for idx, ch in enumerate(left_lhs):
        placed[idx] = ch
    for idx, ch in enumerate(right_lhs):
        pos = relative_offset + idx
        existing = placed.get(pos)
        if existing is not None and existing != ch:
            return None
        placed[pos] = ch

    min_pos = min(placed)
    max_pos = max(placed)
    source_word = "".join(placed[pos] for pos in range(min_pos, max_pos + 1))
    left_start = -min_pos
    right_start = relative_offset - min_pos
    left_branch_term = _apply_at(source_word, left_start, left_lhs, left_rhs)
    right_branch_term = _apply_at(source_word, right_start, right_lhs, right_rhs)

    return {
        "left_rule_index": left_rule_index,
        "right_rule_index": right_rule_index,
        "left_lhs": left_lhs,
        "right_lhs": right_lhs,
        "relative_offset": relative_offset,
        "source_word": source_word,
        "left_start": left_start,
        "right_start": right_start,
        "left_branch_term": left_branch_term,
        "right_branch_term": right_branch_term,
    }


def enumerate_overlap_instances(system: StringRewriteSystem) -> list[dict[str, Any]]:
    raw: list[dict[str, Any]] = []
    rules = list(system.rules)
    for left_idx, left_rule in enumerate(rules):
        for right_idx, right_rule in enumerate(rules):
            left_lhs = left_rule.lhs
            left_rhs = left_rule.rhs
            right_lhs = right_rule.lhs
            right_rhs = right_rule.rhs
            # Offsets that force interval overlap between lhs occurrences.
            for relative_offset in range(-(len(right_lhs) - 1), len(left_lhs)):
                inst = _build_overlap_instance(
                    left_idx,
                    right_idx,
                    left_lhs,
                    left_rhs,
                    right_lhs,
                    right_rhs,
                    relative_offset,
                )
                if inst is not None:
                    raw.append(inst)

    raw.sort(
        key=lambda item: (
            item["left_rule_index"],
            item["right_rule_index"],
            item["relative_offset"],
            item["source_word"],
            item["left_start"],
            item["right_start"],
            item["left_branch_term"],
            item["right_branch_term"],
        )
    )
    return raw


def enumerate_critical_pairs(system: StringRewriteSystem) -> list[dict[str, Any]]:
    grouped: dict[tuple[str, str, str], list[dict[str, Any]]] = defaultdict(list)
    for inst in enumerate_overlap_instances(system):
        left = inst["left_branch_term"]
        right = inst["right_branch_term"]
        if left == right:
            continue
        branch_left, branch_right = sorted([left, right])
        grouped[(inst["source_word"], branch_left, branch_right)].append(inst)

    records: list[dict[str, Any]] = []
    for idx, signature in enumerate(sorted(grouped.keys()), start=1):
        source_word, branch_left, branch_right = signature
        overlap_instances = sorted(
            grouped[signature],
            key=lambda item: (
                item["left_rule_index"],
                item["right_rule_index"],
                item["relative_offset"],
                item["left_start"],
                item["right_start"],
            ),
        )
        records.append(
            {
                "critical_pair_id": f"CP{idx:04d}",
                "source_word": source_word,
                "left_branch_term": branch_left,
                "right_branch_term": branch_right,
                "overlap_instances": overlap_instances,
            }
        )
    return records


def _cp_signature(source_word: str, left_branch_term: str, right_branch_term: str) -> tuple[str, tuple[str, str]]:
    return (source_word, tuple(sorted((left_branch_term, right_branch_term))))


def analyze_string_example_critical_pairs(example: dict[str, Any], system: StringRewriteSystem) -> dict[str, Any]:
    bounds = example["bounds"]
    max_depth = bounds.get("max_depth")
    max_states = bounds.get("max_states")
    max_word_length = bounds.get("max_word_length")
    if max_depth is None or max_states is None:
        raise ValueError("example bounds must include max_depth and max_states")

    example_exploration = system.explore_bounded(
        start_strings=example["start_strings"],
        max_depth=max_depth,
        max_states=max_states,
        max_word_length=max_word_length,
    )
    example_ars = finite_ars_from_exploration(example_exploration)
    graph_peaks = analyze_all_peaks(example_ars)
    graph_peak_signatures = {
        _cp_signature(peak["source"], peak["left"], peak["right"]) for peak in graph_peaks
    }

    critical_pairs = []
    system_pairs = enumerate_critical_pairs(system)
    reachable_signatures = set()
    reachable_defective_count = 0
    defective_count = 0

    for cp in system_pairs:
        source_word = cp["source_word"]
        left = cp["left_branch_term"]
        right = cp["right_branch_term"]

        local_exploration = system.explore_bounded(
            start_strings=[source_word],
            max_depth=max_depth,
            max_states=max_states,
            max_word_length=max_word_length,
        )
        local_ars = finite_ars_from_exploration(local_exploration)
        peak_metrics = analyze_peak(local_ars, source_word, left, right)
        pair_signature = _cp_signature(source_word, left, right)
        source_reachable = source_word in set(example_exploration["states"])
        graph_peak_present = pair_signature in graph_peak_signatures

        if peak_metrics["nonjoinability_defect"]:
            defective_count += 1
            if source_reachable:
                reachable_defective_count += 1
        if source_reachable:
            reachable_signatures.add(pair_signature)

        cp_record = {
            **cp,
            "local_exploration_complete": local_exploration["exploration_complete"],
            "joinable": peak_metrics["joinable"],
            "nonjoinability_defect": peak_metrics["nonjoinability_defect"],
            "left_reachable_normal_forms": peak_metrics["left_reachable_normal_forms"],
            "right_reachable_normal_forms": peak_metrics["right_reachable_normal_forms"],
            "nf_outcome_mismatch": peak_metrics["nf_outcome_mismatch"],
            "nf_symmetric_difference_size": peak_metrics["nf_symmetric_difference_size"],
            "source_reachable_from_example_starts": source_reachable,
            "graph_peak_present_from_example_starts": graph_peak_present,
        }
        critical_pairs.append(cp_record)

    reachable_missing_from_graph = sorted(
        [
            {
                "source_word": sig[0],
                "branches": [sig[1][0], sig[1][1]],
            }
            for sig in (reachable_signatures - graph_peak_signatures)
        ],
        key=lambda item: (item["source_word"], item["branches"][0], item["branches"][1]),
    )
    graph_missing_from_reachable = sorted(
        [
            {
                "source_word": sig[0],
                "branches": [sig[1][0], sig[1][1]],
            }
            for sig in (graph_peak_signatures - reachable_signatures)
        ],
        key=lambda item: (item["source_word"], item["branches"][0], item["branches"][1]),
    )

    return {
        "critical_pairs": critical_pairs,
        "system_critical_pair_count": len(critical_pairs),
        "reachable_critical_pair_count": sum(
            1 for cp in critical_pairs if cp["source_reachable_from_example_starts"]
        ),
        "graph_peak_count": len(graph_peaks),
        "defective_critical_pair_count": defective_count,
        "reachable_defective_critical_pair_count": reachable_defective_count,
        "cross_check": {
            "reachable_critical_pairs_missing_from_graph_peaks": reachable_missing_from_graph,
            "graph_peaks_missing_from_reachable_critical_pairs": graph_missing_from_reachable,
            "reachable_cross_check_match": not reachable_missing_from_graph
            and not graph_missing_from_reachable,
        },
    }


def build_critical_pair_artifact(example_id: str, example: dict[str, Any], system: StringRewriteSystem) -> dict[str, Any]:
    analysis = analyze_string_example_critical_pairs(example, system)
    return {
        "schema_version": 1,
        "kind": "string_critical_pair_analysis",
        "example_id": example_id,
        "bounds": example["bounds"],
        "system_critical_pair_count": analysis["system_critical_pair_count"],
        "reachable_critical_pair_count": analysis["reachable_critical_pair_count"],
        "graph_peak_count": analysis["graph_peak_count"],
        "defective_critical_pair_count": analysis["defective_critical_pair_count"],
        "reachable_defective_critical_pair_count": analysis["reachable_defective_critical_pair_count"],
        "critical_pairs": analysis["critical_pairs"],
        "cross_check": analysis["cross_check"],
    }
