import json
from pathlib import Path

from rewriteflat.example_io import load_finite_ars
from rewriteflat.finite_ars import FiniteARS
from rewriteflat.naive_graph_audit import (
    build_naive_graph_audit,
    build_naive_graph_audit_row,
    has_directed_cycle,
    naive_directed_loop_flat,
)


ROOT = Path(__file__).resolve().parents[1]


def _load_curated() -> dict[str, FiniteARS]:
    return {
        "E001_diamond_flat": load_finite_ars(ROOT / "data" / "examples" / "E001_diamond_flat.yaml"),
        "E002_fork_curved": load_finite_ars(ROOT / "data" / "examples" / "E002_fork_curved.yaml"),
        "E003_delayed_join_flat": load_finite_ars(ROOT / "data" / "examples" / "E003_delayed_join_flat.yaml"),
        "E004_bare_graph_counterexample_target": load_finite_ars(
            ROOT / "data" / "examples" / "E004_bare_graph_counterexample_target.yaml"
        ),
    }


def test_curated_terminating_examples_are_naively_flat():
    examples = _load_curated()
    for ars in examples.values():
        assert has_directed_cycle(ars) is False
        assert naive_directed_loop_flat(ars) is True


def test_fork_and_bare_graph_target_nonconfluent_despite_naive_flatness():
    examples = _load_curated()
    for example_id in ("E002_fork_curved", "E004_bare_graph_counterexample_target"):
        row = build_naive_graph_audit_row(example_id, examples[example_id])
        assert row["naive_directed_loop_flat"] is True
        assert row["confluent"] is False
        assert row["nonjoinability_defect_count"] > 0


def test_bare_graph_target_zero_undirected_cycle_rank():
    row = build_naive_graph_audit_row(
        "E004_bare_graph_counterexample_target",
        load_finite_ars(ROOT / "data" / "examples" / "E004_bare_graph_counterexample_target.yaml"),
    )
    assert row["undirected_cycle_rank"] == 0
    assert row["confluent"] is False


def test_confluent_example_can_have_positive_undirected_cycle_rank():
    row = build_naive_graph_audit_row(
        "E001_diamond_flat", load_finite_ars(ROOT / "data" / "examples" / "E001_diamond_flat.yaml")
    )
    assert row["undirected_cycle_rank"] > 0
    assert row["confluent"] is True


def test_inline_nonterminating_cycle_case():
    ars = FiniteARS(states=["A", "B"], edges=[("A", "B"), ("B", "A")])
    assert has_directed_cycle(ars) is True
    assert naive_directed_loop_flat(ars) is False


def test_top_level_artifact_structure_and_serializability():
    examples = _load_curated()
    artifact = build_naive_graph_audit(examples.items())

    assert artifact["schema_version"] == 1
    assert artifact["kind"] == "naive_bare_graph_flatness_audit"
    assert "examples" in artifact
    assert "findings" in artifact
    json.dumps(artifact, sort_keys=True)
