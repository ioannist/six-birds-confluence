import json

from rewriteflat.completion_case_study import (
    DEFAULT_CASE_ID,
    build_completion_case_study_artifact,
    load_completion_case_study,
)


def _stages_by_id(artifact: dict) -> dict[str, dict]:
    return {stage["stage_id"]: stage for stage in artifact["stages"]}


def test_case_study_spec_loads_and_stage_ordering():
    artifact = build_completion_case_study_artifact(DEFAULT_CASE_ID)
    spec = load_completion_case_study(
        "project/case_studies/CS001_manual_completion_ab_to_xy.yaml"
    )
    assert spec["case_id"] == "CS001_manual_completion_ab_to_xy"
    assert len(spec["stages"]) == 2
    assert [stage["stage_id"] for stage in spec["stages"]] == ["S0_before", "S1_after"]
    assert [stage["stage_id"] for stage in artifact["stages"]] == ["S0_before", "S1_after"]


def test_rule_addition_is_explicit_in_case_spec_and_artifact():
    artifact = build_completion_case_study_artifact(DEFAULT_CASE_ID)
    stages = _stages_by_id(artifact)
    assert stages["S0_before"]["added_rules_from_previous_stage"] == []
    assert stages["S1_after"]["added_rules_from_previous_stage"] == [["x", "y"]]


def test_before_after_stage_metrics_match_expected_behavior():
    stages = _stages_by_id(build_completion_case_study_artifact(DEFAULT_CASE_ID))

    s0 = stages["S0_before"]
    assert s0["example_id"] == "E007_completion_before"
    assert s0["rule_count"] == 2
    assert s0["confluent"] is False
    assert s0["local_peak_nonjoinability_defect_count"] == 1
    assert s0["local_peak_nf_outcome_mismatch_count"] == 1
    assert s0["system_critical_pair_count"] == 1
    assert s0["reachable_critical_pair_count"] == 1
    assert s0["system_defective_critical_pair_count"] == 1
    assert s0["reachable_defective_critical_pair_count"] == 1
    assert s0["normal_forms"] == ["x", "y"]

    s1 = stages["S1_after"]
    assert s1["example_id"] == "E008_completion_after"
    assert s1["rule_count"] == 3
    assert s1["confluent"] is True
    assert s1["local_peak_nonjoinability_defect_count"] == 0
    assert s1["local_peak_nf_outcome_mismatch_count"] == 0
    assert s1["system_critical_pair_count"] == 1
    assert s1["reachable_critical_pair_count"] == 1
    assert s1["system_defective_critical_pair_count"] == 0
    assert s1["reachable_defective_critical_pair_count"] == 0
    assert s1["normal_forms"] == ["y"]


def test_findings_capture_defect_elimination_and_confluence_flip():
    findings = build_completion_case_study_artifact(DEFAULT_CASE_ID)["findings"]
    assert findings["final_stage_zero_reachable_defects"] is True
    assert findings["final_stage_zero_system_defects"] is True
    assert findings["final_stage_confluent"] is True
    assert findings["confluence_flips_false_to_true"] is True
    assert findings["defect_elimination_observed"] is True
    assert findings["curvature_elimination_story_worked_cleanly"] is True


def test_artifact_serializable_and_has_required_keys():
    artifact = build_completion_case_study_artifact(DEFAULT_CASE_ID)
    assert artifact["schema_version"] == 1
    assert artifact["kind"] == "manual_completion_case_study"
    assert artifact["case_id"] == "CS001_manual_completion_ab_to_xy"
    assert "stages" in artifact
    assert "stage_deltas" in artifact
    assert "findings" in artifact
    json.dumps(artifact, sort_keys=True)
