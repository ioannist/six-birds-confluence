"""Manual completion case-study helpers."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml

from .critical_pairs import build_critical_pair_artifact
from .example_io import load_string_rewrite_system
from .string_rewriting import analyze_string_exploration


DEFAULT_CASE_ID = "CS001_manual_completion_ab_to_xy"


def load_completion_case_study(path: str | Path) -> dict[str, Any]:
    path_obj = Path(path)
    payload = yaml.safe_load(path_obj.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError("case-study payload must be a mapping")

    case_id = payload.get("case_id")
    stages = payload.get("stages")
    if not isinstance(case_id, str) or not case_id:
        raise ValueError("case-study must include non-empty case_id")
    if not isinstance(stages, list) or len(stages) < 2:
        raise ValueError("case-study must include at least 2 stages")

    stage_ids: set[str] = set()
    for idx, stage in enumerate(stages):
        if not isinstance(stage, dict):
            raise ValueError(f"stage[{idx}] must be a mapping")
        stage_id = stage.get("stage_id")
        example_id = stage.get("example_id")
        added_rules = stage.get("added_rules_from_previous_stage")
        if not isinstance(stage_id, str) or not stage_id:
            raise ValueError(f"stage[{idx}] missing non-empty stage_id")
        if stage_id in stage_ids:
            raise ValueError(f"duplicate stage_id: {stage_id}")
        stage_ids.add(stage_id)
        if not isinstance(example_id, str) or not example_id:
            raise ValueError(f"stage[{idx}] missing non-empty example_id")
        if not isinstance(added_rules, list):
            raise ValueError(f"stage[{idx}] must include added_rules_from_previous_stage list")
        if idx == 0 and len(added_rules) != 0:
            raise ValueError("first stage must not add rules from previous stage")
    return payload


def build_completion_case_stage_row(case_spec: dict[str, Any], stage_spec: dict[str, Any]) -> dict[str, Any]:
    root = Path(__file__).resolve().parents[2]
    example_id = stage_spec["example_id"]
    stage_id = stage_spec["stage_id"]
    example_path = root / "data" / "examples" / f"{example_id}.yaml"
    example, system = load_string_rewrite_system(example_path)

    bounds = example["bounds"]
    max_depth = bounds.get("max_depth")
    max_states = bounds.get("max_states")
    max_word_length = bounds.get("max_word_length")
    if max_depth is None or max_states is None:
        raise ValueError(f"example {example_id} must include max_depth and max_states")

    exploration = system.explore_bounded(
        start_strings=example["start_strings"],
        max_depth=max_depth,
        max_states=max_states,
        max_word_length=max_word_length,
    )
    string_analysis = analyze_string_exploration(exploration)
    cp_artifact = build_critical_pair_artifact(example_id, example, system)
    system_defective = sum(
        1
        for cp in cp_artifact["critical_pairs"]
        if cp["nonjoinability_defect"]
    )
    reachable_defective = sum(
        1
        for cp in cp_artifact["reachable_critical_pairs"]
        if cp["nonjoinability_defect"]
    )

    return {
        "case_id": case_spec["case_id"],
        "stage_id": stage_id,
        "example_id": example_id,
        "rule_count": len(system.rules),
        "rules": [[rule.lhs, rule.rhs] for rule in system.rules],
        "added_rules_from_previous_stage": stage_spec["added_rules_from_previous_stage"],
        "start_strings": example["start_strings"],
        "bounds": bounds,
        "exploration_complete": exploration["exploration_complete"],
        "terminating": string_analysis["terminating"],
        "confluent": string_analysis["confluent"],
        "unique_reachable_normal_forms": string_analysis["unique_reachable_normal_forms"],
        "normal_forms": string_analysis["normal_forms"],
        "local_peak_count": string_analysis["peak_count"],
        "local_peak_nonjoinability_defect_count": string_analysis["defect_counts"][
            "nonjoinability_defect"
        ],
        "local_peak_nf_outcome_mismatch_count": string_analysis["defect_counts"][
            "nf_outcome_mismatch"
        ],
        "system_critical_pair_count": cp_artifact["system_critical_pair_count"],
        "reachable_critical_pair_count": cp_artifact["reachable_critical_pair_count"],
        "system_defective_critical_pair_count": system_defective,
        "reachable_defective_critical_pair_count": reachable_defective,
    }


def _build_stage_deltas(stages: list[dict[str, Any]]) -> list[dict[str, Any]]:
    deltas = []
    for prev, curr in zip(stages, stages[1:]):
        deltas.append(
            {
                "from_stage_id": prev["stage_id"],
                "to_stage_id": curr["stage_id"],
                "added_rules": curr["added_rules_from_previous_stage"],
                "confluence_changed": prev["confluent"] != curr["confluent"],
                "local_peak_nonjoinability_defect_delta": curr[
                    "local_peak_nonjoinability_defect_count"
                ]
                - prev["local_peak_nonjoinability_defect_count"],
                "local_peak_nf_outcome_mismatch_delta": curr[
                    "local_peak_nf_outcome_mismatch_count"
                ]
                - prev["local_peak_nf_outcome_mismatch_count"],
                "reachable_defective_critical_pair_count_delta": curr[
                    "reachable_defective_critical_pair_count"
                ]
                - prev["reachable_defective_critical_pair_count"],
                "system_defective_critical_pair_count_delta": curr[
                    "system_defective_critical_pair_count"
                ]
                - prev["system_defective_critical_pair_count"],
            }
        )
    return deltas


def build_completion_case_study_artifact(case_id: str = DEFAULT_CASE_ID) -> dict[str, Any]:
    root = Path(__file__).resolve().parents[2]
    spec_path = root / "project" / "case_studies" / f"{case_id}.yaml"
    spec = load_completion_case_study(spec_path)

    stages = []
    for idx, stage_spec in enumerate(spec["stages"]):
        row = build_completion_case_stage_row(spec, stage_spec)
        if stages:
            previous_rules = {tuple(rule) for rule in stages[-1]["rules"]}
            current_rules = {tuple(rule) for rule in row["rules"]}
            added_rules = {tuple(rule) for rule in row["added_rules_from_previous_stage"]}
            if current_rules != previous_rules | added_rules:
                raise ValueError("completion stages must differ by exactly their declared rule additions")
            if row["start_strings"] != stages[-1]["start_strings"]:
                raise ValueError("completion stages must use the same start strings")
        row["stage_index"] = idx
        stages.append(row)

    stage_deltas = _build_stage_deltas(stages)
    first = stages[0]
    final = stages[-1]

    final_zero_reachable = final["reachable_defective_critical_pair_count"] == 0
    final_zero_system = final["system_defective_critical_pair_count"] == 0
    final_confluent = bool(final["confluent"])
    confluence_flip = (first["confluent"] is False) and (final["confluent"] is True)
    defect_elimination_observed = (
        first["local_peak_nonjoinability_defect_count"] > 0
        and first["local_peak_nf_outcome_mismatch_count"] > 0
        and first["reachable_defective_critical_pair_count"] > 0
        and final["local_peak_nonjoinability_defect_count"] == 0
        and final["local_peak_nf_outcome_mismatch_count"] == 0
        and final["reachable_defective_critical_pair_count"] == 0
    )
    story_clean = (
        final_zero_reachable
        and final_zero_system
        and final_confluent
        and confluence_flip
        and defect_elimination_observed
    )

    findings = {
        "final_stage_zero_reachable_defects": final_zero_reachable,
        "final_stage_zero_system_defects": final_zero_system,
        "final_stage_confluent": final_confluent,
        "confluence_flips_false_to_true": confluence_flip,
        "defect_elimination_observed": defect_elimination_observed,
        "curvature_elimination_story_worked_cleanly": story_clean,
    }

    return {
        "schema_version": 1,
        "kind": "manual_completion_case_study",
        "case_id": spec["case_id"],
        "stages": stages,
        "stage_deltas": stage_deltas,
        "findings": findings,
    }
