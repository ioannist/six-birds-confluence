import json

from rewriteflat.critical_pair_curvature_audit import build_critical_pair_curvature_audit


def _rows_by_id(artifact: dict) -> dict[str, dict]:
    return {row["example_id"]: row for row in artifact["examples"]}


def test_curated_audit_includes_four_examples_and_findings():
    artifact = build_critical_pair_curvature_audit()
    rows = _rows_by_id(artifact)
    assert set(rows.keys()) == {
        "E005_string_sort_confluent",
        "E006_string_overlap_nonconfluent",
        "E007_completion_before",
        "E008_completion_after",
    }
    assert artifact["findings"]["confluent_example_ids"] == [
        "E005_string_sort_confluent",
        "E008_completion_after",
    ]
    assert artifact["findings"]["nonconfluent_example_ids"] == [
        "E006_string_overlap_nonconfluent",
        "E007_completion_before",
    ]


def test_confluent_examples_have_zero_local_and_reachable_cp_defects():
    rows = _rows_by_id(build_critical_pair_curvature_audit())
    for example_id in ("E005_string_sort_confluent", "E008_completion_after"):
        row = rows[example_id]
        assert row["global"]["confluent"] is True
        assert row["local_peaks"]["local_peak_nonjoinability_defect_count"] == 0
        assert row["local_peaks"]["local_peak_nf_outcome_mismatch_count"] == 0
        assert row["critical_pairs"]["reachable_critical_pair_nonjoinability_defect_count"] == 0
        assert row["critical_pairs"]["reachable_critical_pair_nf_outcome_mismatch_count"] == 0
        assert row["curvature_generator_story_supported"] is True


def test_nonconfluent_examples_have_nonzero_local_and_reachable_cp_defects():
    rows = _rows_by_id(build_critical_pair_curvature_audit())
    for example_id in ("E006_string_overlap_nonconfluent", "E007_completion_before"):
        row = rows[example_id]
        assert row["global"]["confluent"] is False
        assert row["local_peaks"]["local_peak_nonjoinability_defect_count"] > 0
        assert row["critical_pairs"]["reachable_critical_pair_nonjoinability_defect_count"] > 0
        assert row["curvature_generator_story_supported"] is True


def test_e006_system_vs_reachable_distinction_preserved():
    row = _rows_by_id(build_critical_pair_curvature_audit())["E006_string_overlap_nonconfluent"]
    assert row["critical_pairs"]["system_critical_pair_count"] > row["critical_pairs"][
        "reachable_critical_pair_count"
    ]
    assert row["alignment"]["reachable_cross_check_match"] is True


def test_completion_pair_delta_captured():
    delta = build_critical_pair_curvature_audit()["completion_pair_delta"]
    assert delta["before_example_id"] == "E007_completion_before"
    assert delta["after_example_id"] == "E008_completion_after"
    assert delta["before_confluent"] is False
    assert delta["after_confluent"] is True
    assert delta["defect_elimination_observed"] is True


def test_artifact_serializable_and_has_required_keys():
    artifact = build_critical_pair_curvature_audit()
    assert artifact["schema_version"] == 1
    assert artifact["kind"] == "critical_pair_curvature_audit"
    assert "examples" in artifact
    assert "completion_pair_delta" in artifact
    assert "findings" in artifact
    json.dumps(artifact, sort_keys=True)
