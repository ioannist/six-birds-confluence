import json

from rewriteflat.boundary_counterexamples import (
    OVERCLAIM_IDS,
    build_boundary_counterexample_artifact,
    is_normalizing,
    naive_nf_peak_flatness,
)
from rewriteflat.finite_ars import FiniteARS
from rewriteflat.naive_graph_audit import naive_directed_loop_flat


def test_inline_witness_o001():
    ars = FiniteARS(
        states=["s0", "s1", "s2", "s3"],
        edges=[("s0", "s1"), ("s0", "s3"), ("s1", "s0"), ("s1", "s2")],
    )
    peak_count = len(ars.local_peaks())
    nonjoinability_defects = sum(
        1
        for source, left, right in ars.local_peaks()
        if not ars.joinable(left, right)
    )
    local_flatness = nonjoinability_defects == 0

    assert peak_count > 0
    assert local_flatness is True
    assert ars.is_locally_confluent() is True
    assert ars.is_confluent() is False
    assert ars.is_terminating() is False


def test_inline_witness_o002_and_o006():
    ars = FiniteARS(states=["s0"], edges=[("s0", "s0")])
    assert ars.is_confluent() is True
    assert is_normalizing(ars) is False
    assert naive_directed_loop_flat(ars) is False


def test_inline_witness_o003():
    ars = FiniteARS(
        states=["s0", "s1", "s2"],
        edges=[("s0", "s1"), ("s0", "s2"), ("s1", "s1"), ("s2", "s2")],
    )
    assert ars.is_terminating() is False
    assert ars.has_unique_reachable_normal_forms() is True
    assert ars.is_confluent() is False


def test_inline_witness_o004():
    ars = FiniteARS(
        states=["s0", "s1", "s2"],
        edges=[("s0", "s1"), ("s0", "s2"), ("s1", "s1"), ("s2", "s2")],
    )
    nonjoinability_defects = sum(
        1
        for source, left, right in ars.local_peaks()
        if not ars.joinable(left, right)
    )
    local_flatness = nonjoinability_defects == 0
    assert ars.is_terminating() is False
    assert naive_nf_peak_flatness(ars) is True
    assert local_flatness is False


def test_inline_witness_o005():
    ars = FiniteARS(
        states=["s0", "s1", "s2", "s3"],
        edges=[("s0", "s1"), ("s0", "s2"), ("s1", "s3")],
    )
    assert naive_directed_loop_flat(ars) is True
    assert ars.is_confluent() is False


def test_smaller_search_smoke():
    artifact = build_boundary_counterexample_artifact(max_states=3)
    assert len(artifact["overclaims"]) == 6
    by_id = {entry["overclaim_id"]: entry for entry in artifact["overclaims"]}
    for overclaim_id in OVERCLAIM_IDS:
        assert overclaim_id in by_id
        assert by_id[overclaim_id]["status"] in {"found", "none"}

    assert by_id["O002_confluence_implies_normalizing"]["status"] == "found"
    assert by_id["O004_naive_nf_peak_flatness_implies_local_flatness_without_termination"]["status"] == "found"
    assert by_id["O005_naive_graph_flatness_false_positive"]["status"] == "found"
    assert by_id["O006_naive_graph_flatness_false_negative"]["status"] == "found"


def test_artifact_structure_and_serializability():
    artifact = build_boundary_counterexample_artifact(max_states=3)
    assert artifact["schema_version"] == 1
    assert artifact["kind"] == "boundary_counterexample_search"
    assert "search_space" in artifact
    assert "overclaims" in artifact
    json.dumps(artifact, sort_keys=True)
