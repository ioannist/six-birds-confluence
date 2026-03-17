"""Bounded semi-Thue / string rewriting utilities."""

from __future__ import annotations

from collections import deque
from dataclasses import dataclass
from typing import Any

from .finite_ars import FiniteARS
from .peak_analysis import analyze_all_peaks

SUPPORTED_EXPECTED_LABELS = {
    "terminating",
    "locally_confluent",
    "confluent",
    "nonconfluent",
    "zero_defect",
    "nonzero_defect",
}


@dataclass(frozen=True)
class StringRewriteRule:
    lhs: str
    rhs: str


class StringRewriteSystem:
    def __init__(self, rules: list[tuple[str, str]]) -> None:
        if not isinstance(rules, list) or not rules:
            raise ValueError("rules must be a non-empty list")
        validated: list[StringRewriteRule] = []
        for item in rules:
            if not isinstance(item, tuple) or len(item) != 2:
                raise ValueError(f"invalid rule shape: {item!r}")
            lhs, rhs = item
            if not isinstance(lhs, str) or not isinstance(rhs, str):
                raise ValueError(f"rule entries must be strings: {item!r}")
            if lhs == "":
                raise ValueError("rule lhs must be non-empty")
            validated.append(StringRewriteRule(lhs=lhs, rhs=rhs))
        self._rules = tuple(validated)

    @property
    def rules(self) -> tuple[StringRewriteRule, ...]:
        return self._rules

    def one_step_matches(self, word: str) -> list[dict[str, Any]]:
        if not isinstance(word, str):
            raise ValueError("word must be a string")
        steps: list[dict[str, Any]] = []
        for rule_index, rule in enumerate(self._rules):
            lhs = rule.lhs
            rhs = rule.rhs
            width = len(lhs)
            for position in range(0, len(word) - width + 1):
                if word[position : position + width] != lhs:
                    continue
                target = word[:position] + rhs + word[position + width :]
                steps.append(
                    {
                        "source": word,
                        "target": target,
                        "rule_index": rule_index,
                        "lhs": lhs,
                        "rhs": rhs,
                        "position": position,
                    }
                )
        return steps

    def successors(self, word: str) -> list[str]:
        return sorted({step["target"] for step in self.one_step_matches(word)})

    def explore_bounded(
        self,
        start_strings: list[str],
        max_depth: int,
        max_states: int,
        max_word_length: int | None = None,
    ) -> dict[str, Any]:
        if not isinstance(start_strings, list) or not start_strings:
            raise ValueError("start_strings must be a non-empty list")
        if any(not isinstance(word, str) for word in start_strings):
            raise ValueError("start_strings entries must be strings")
        if not isinstance(max_depth, int) or max_depth <= 0:
            raise ValueError("max_depth must be a positive integer")
        if not isinstance(max_states, int) or max_states <= 0:
            raise ValueError("max_states must be a positive integer")
        if max_word_length is not None and (
            not isinstance(max_word_length, int) or max_word_length <= 0
        ):
            raise ValueError("max_word_length must be a positive integer when provided")

        starts = sorted(set(start_strings))
        depth_by_state: dict[str, int] = {word: 0 for word in starts}
        queue: deque[str] = deque(starts)
        explored_states: set[str] = set(starts)
        explored_edges: set[tuple[str, str]] = set()
        step_records: list[dict[str, Any]] = []

        suppressed_by_depth = False
        suppressed_by_states = False
        suppressed_by_word_length = False

        while queue:
            source = queue.popleft()
            source_depth = depth_by_state[source]
            steps = self.one_step_matches(source)

            for step in steps:
                target = step["target"]
                if max_word_length is not None and len(target) > max_word_length:
                    suppressed_by_word_length = True
                    continue

                if target in explored_states:
                    explored_edges.add((source, target))
                    step_records.append(step)
                    continue

                if source_depth >= max_depth:
                    suppressed_by_depth = True
                    continue

                if len(explored_states) >= max_states:
                    suppressed_by_states = True
                    continue

                explored_states.add(target)
                depth_by_state[target] = source_depth + 1
                queue.append(target)
                explored_edges.add((source, target))
                step_records.append(step)

        states_sorted = sorted(explored_states)
        edges_sorted = sorted(explored_edges)
        step_records_sorted = sorted(
            step_records,
            key=lambda step: (
                step["source"],
                step["rule_index"],
                step["position"],
                step["target"],
            ),
        )
        depth_sorted = {state: depth_by_state[state] for state in sorted(depth_by_state)}
        exploration_complete = not (
            suppressed_by_depth or suppressed_by_states or suppressed_by_word_length
        )

        return {
            "start_strings": starts,
            "states": states_sorted,
            "edges": edges_sorted,
            "step_records": step_records_sorted,
            "depth_by_state": depth_sorted,
            "bounds": {
                "max_depth": max_depth,
                "max_states": max_states,
                "max_word_length": max_word_length,
            },
            "exploration_complete": exploration_complete,
            "suppressed": {
                "max_depth": suppressed_by_depth,
                "max_states": suppressed_by_states,
                "max_word_length": suppressed_by_word_length,
            },
        }


def finite_ars_from_exploration(exploration: dict[str, Any]) -> FiniteARS:
    return FiniteARS(states=exploration["states"], edges=exploration["edges"])


def analyze_string_exploration(exploration: dict[str, Any]) -> dict[str, Any]:
    ars = finite_ars_from_exploration(exploration)
    peaks = analyze_all_peaks(ars)
    nonjoinability = sum(1 for peak in peaks if peak["nonjoinability_defect"])
    nf_mismatch = sum(1 for peak in peaks if peak["nf_outcome_mismatch"] is True)
    normal_forms = sorted(ars.normal_forms())

    reachable_normal_forms_by_state = {
        state: sorted(ars.reachable_normal_forms(state)) for state in sorted(ars.states)
    }

    return {
        "state_count": len(ars.states),
        "edge_count": len(ars.edges),
        "peak_count": len(peaks),
        "terminating": ars.is_terminating(),
        "locally_confluent": ars.is_locally_confluent(),
        "confluent": ars.is_confluent(),
        "unique_reachable_normal_forms": ars.has_unique_reachable_normal_forms(),
        "normal_forms": normal_forms,
        "defect_counts": {
            "nonjoinability_defect": nonjoinability,
            "nf_outcome_mismatch": nf_mismatch,
        },
        "reachable_normal_forms_by_state": reachable_normal_forms_by_state,
    }


def evaluate_supported_expected_label(label: str, analysis: dict[str, Any]) -> bool:
    defects = analysis["defect_counts"]
    if label == "terminating":
        return bool(analysis["terminating"])
    if label == "locally_confluent":
        return bool(analysis["locally_confluent"])
    if label == "confluent":
        return bool(analysis["confluent"])
    if label == "nonconfluent":
        return not bool(analysis["confluent"])
    if label == "zero_defect":
        return defects["nonjoinability_defect"] == 0 and defects["nf_outcome_mismatch"] == 0
    if label == "nonzero_defect":
        return defects["nonjoinability_defect"] > 0 or defects["nf_outcome_mismatch"] > 0
    raise ValueError(f"unsupported expected label: {label}")
