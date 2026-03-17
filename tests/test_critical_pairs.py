import json
from pathlib import Path

from rewriteflat.critical_pairs import build_critical_pair_artifact, enumerate_critical_pairs
from rewriteflat.example_io import load_string_rewrite_system
from rewriteflat.string_rewriting import StringRewriteSystem


ROOT = Path(__file__).resolve().parents[1]


def _artifact(example_id: str) -> dict:
    example, system = load_string_rewrite_system(ROOT / "data" / "examples" / f"{example_id}.yaml")
    return build_critical_pair_artifact(example_id, example, system)


def test_exact_overlap_same_lhs_critical_pair():
    system = StringRewriteSystem(rules=[("ab", "x"), ("ab", "y")])
    pairs = enumerate_critical_pairs(system)
    assert len(pairs) == 1
    cp = pairs[0]
    assert cp["source_word"] == "ab"
    assert cp["left_branch_term"] == "x"
    assert cp["right_branch_term"] == "y"


def test_e006_system_vs_reachable_distinction():
    artifact = _artifact("E006_string_overlap_nonconfluent")
    assert artifact["system_critical_pair_count"] == 2
    assert artifact["reachable_critical_pair_count"] == 1
    assert artifact["graph_peak_count"] == 1
    assert artifact["cross_check"]["reachable_cross_check_match"] is True
    assert artifact["reachable_defective_critical_pair_count"] > 0


def test_e007_e008_after_correction():
    before = _artifact("E007_completion_before")
    after = _artifact("E008_completion_after")

    assert before["system_critical_pair_count"] == 1
    assert before["reachable_critical_pair_count"] == 1
    assert before["graph_peak_count"] == 1
    assert before["reachable_defective_critical_pair_count"] > 0
    assert before["cross_check"]["reachable_cross_check_match"] is True

    assert after["system_critical_pair_count"] == 1
    assert after["reachable_critical_pair_count"] == 1
    assert after["graph_peak_count"] == 1
    assert after["reachable_defective_critical_pair_count"] == 0
    assert after["cross_check"]["reachable_cross_check_match"] is True


def test_e005_reachable_cross_check():
    artifact = _artifact("E005_string_sort_confluent")
    assert artifact["reachable_critical_pair_count"] >= 1
    assert artifact["graph_peak_count"] == 1
    assert artifact["cross_check"]["reachable_cross_check_match"] is True
    assert artifact["reachable_defective_critical_pair_count"] == 0


def test_critical_pair_artifact_serializability():
    one = _artifact("E006_string_overlap_nonconfluent")
    summary = {
        "schema_version": 1,
        "kind": "string_critical_pair_summary",
        "examples": [
            {
                "example_id": one["example_id"],
                "system_critical_pair_count": one["system_critical_pair_count"],
                "reachable_critical_pair_count": one["reachable_critical_pair_count"],
            }
        ],
    }
    assert one["kind"] == "string_critical_pair_analysis"
    assert "critical_pairs" in one
    assert "cross_check" in one
    json.dumps(one, sort_keys=True)
    json.dumps(summary, sort_keys=True)
