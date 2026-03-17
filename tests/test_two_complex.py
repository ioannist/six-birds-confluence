import json

from rewriteflat.two_complex import (
    SELECTED_EXAMPLES,
    build_selected_two_complex_artifacts,
    build_two_complex_artifact,
)


def _artifacts_by_id(bundle: dict) -> dict[str, dict]:
    return {a["example_id"]: a for a in bundle["artifacts"]}


def test_all_selected_examples_generate_artifacts():
    bundle = build_selected_two_complex_artifacts()
    by_id = _artifacts_by_id(bundle)
    assert set(by_id.keys()) == set(SELECTED_EXAMPLES)


def test_finite_ars_trivial_vs_nontrivial_statuses():
    e1 = build_two_complex_artifact("E001_diamond_flat")
    e2 = build_two_complex_artifact("E002_fork_curved")

    assert e1["two_cell_count"] == 1
    assert e1["two_cells"][0]["elementary_holonomy_status"] == "trivial"
    assert e1["two_cells"][0]["join_witness"] == "D"

    assert e2["two_cell_count"] == 1
    assert e2["two_cells"][0]["elementary_holonomy_status"] == "nontrivial"
    assert e2["two_cells"][0]["holonomy_defect_kind"] == "nonjoinable"


def test_string_pair_holonomy_elimination_observed():
    bundle = build_selected_two_complex_artifacts()
    by_id = _artifacts_by_id(bundle)
    assert by_id["E007_completion_before"]["holonomy_counts"]["nontrivial"] == 1
    assert by_id["E008_completion_after"]["holonomy_counts"]["nontrivial"] == 0

    pd = {d["pair_id"]: d for d in bundle["summary"]["pair_deltas"]}
    assert pd["string_completion_pair"]["holonomy_elimination_observed"] is True


def test_trs_pair_holonomy_elimination_observed():
    bundle = build_selected_two_complex_artifacts()
    by_id = _artifacts_by_id(bundle)
    assert by_id["TRS003_nested_overlap_nonconfluent"]["holonomy_counts"]["nontrivial"] == 1
    assert by_id["TRS004_nested_overlap_joinable"]["holonomy_counts"]["nontrivial"] == 0

    pd = {d["pair_id"]: d for d in bundle["summary"]["pair_deltas"]}
    assert pd["trs_nested_overlap_pair"]["holonomy_elimination_observed"] is True


def test_canonical_witness_values():
    e8 = build_two_complex_artifact("E008_completion_after")
    t4 = build_two_complex_artifact("TRS004_nested_overlap_joinable")

    assert e8["two_cells"][0]["join_witness"] == "y"
    assert t4["two_cells"][0]["join_witness"] == "p(a)"


def test_artifact_and_summary_serializable():
    bundle = build_selected_two_complex_artifacts()
    for artifact in bundle["artifacts"]:
        assert "schema_version" in artifact
        assert "kind" in artifact
        assert "example_id" in artifact
        assert "zero_cells" in artifact
        assert "one_cells" in artifact
        assert "two_cells" in artifact
        json.dumps(artifact, sort_keys=True)
    summary = bundle["summary"]
    assert "schema_version" in summary
    assert "kind" in summary
    assert "examples" in summary
    assert "pair_deltas" in summary
    assert "findings" in summary
    json.dumps(summary, sort_keys=True)
