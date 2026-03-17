import json
from pathlib import Path

from rewriteflat.example_io import load_finite_ars
from rewriteflat.plaquettes import build_plaquette_artifact


ROOT = Path(__file__).resolve().parents[1]


def test_diamond_plaquette():
    ars = load_finite_ars(ROOT / "data" / "examples" / "E001_diamond_flat.yaml")
    artifact = build_plaquette_artifact("E001_diamond_flat", ars)
    assert artifact["plaquette_count"] == 1

    plaquette = artifact["plaquettes"][0]
    assert plaquette["status"] == "joinable"
    assert plaquette["join_witness"]["state"] == "D"
    assert plaquette["left_branch_edge"] == ["A", "B"]
    assert plaquette["right_branch_edge"] == ["A", "C"]
    assert plaquette["defect_label"] is None


def test_fork_plaquette():
    ars = load_finite_ars(ROOT / "data" / "examples" / "E002_fork_curved.yaml")
    artifact = build_plaquette_artifact("E002_fork_curved", ars)
    assert artifact["plaquette_count"] == 1

    plaquette = artifact["plaquettes"][0]
    assert plaquette["status"] == "defective"
    assert plaquette["join_witness"] is None
    assert plaquette["defect_label"] == "nonjoinable_peak"


def test_delayed_join_plaquette():
    ars = load_finite_ars(ROOT / "data" / "examples" / "E003_delayed_join_flat.yaml")
    artifact = build_plaquette_artifact("E003_delayed_join_flat", ars)
    assert artifact["plaquette_count"] == 1

    plaquette = artifact["plaquettes"][0]
    assert plaquette["status"] == "joinable"
    assert plaquette["join_witness"]["state"] == "F"
    left_len = len(plaquette["join_witness"]["left_path_states"])
    right_len = len(plaquette["join_witness"]["right_path_states"])
    assert left_len != right_len


def test_bare_graph_target_plaquettes():
    ars = load_finite_ars(ROOT / "data" / "examples" / "E004_bare_graph_counterexample_target.yaml")
    artifact = build_plaquette_artifact("E004_bare_graph_counterexample_target", ars)
    assert artifact["plaquette_count"] >= 2
    assert all(p["status"] == "defective" for p in artifact["plaquettes"])
    assert artifact["defect_counts"]["defective"] == artifact["plaquette_count"]


def test_plaquette_artifact_is_json_serializable():
    ars = load_finite_ars(ROOT / "data" / "examples" / "E001_diamond_flat.yaml")
    artifact = build_plaquette_artifact("E001_diamond_flat", ars)
    json.dumps(artifact, sort_keys=True)
