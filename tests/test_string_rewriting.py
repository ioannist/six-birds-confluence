import json
from pathlib import Path

import pytest
import yaml

from rewriteflat.example_io import (
    load_string_rewrite_example,
    load_string_rewrite_system,
    string_rewrite_example_from_mapping,
)
from rewriteflat.string_rewriting import (
    SUPPORTED_EXPECTED_LABELS,
    StringRewriteSystem,
    analyze_string_exploration,
    evaluate_supported_expected_label,
)


ROOT = Path(__file__).resolve().parents[1]
EXAMPLE_IDS = [
    "E005_string_sort_confluent",
    "E006_string_overlap_nonconfluent",
    "E007_completion_before",
    "E008_completion_after",
]


def _catalog_expected_labels() -> dict[str, list[str]]:
    payload = yaml.safe_load((ROOT / "project" / "example_catalog.yaml").read_text(encoding="utf-8"))
    return {item["id"]: item["expected_labels"] for item in payload["examples"] if isinstance(item, dict)}


def _run_example(example_id: str) -> dict:
    example, system = load_string_rewrite_system(ROOT / "data" / "examples" / f"{example_id}.yaml")
    bounds = example["bounds"]
    exploration = system.explore_bounded(
        start_strings=example["start_strings"],
        max_depth=bounds["max_depth"],
        max_states=bounds["max_states"],
        max_word_length=bounds["max_word_length"],
    )
    analysis = analyze_string_exploration(exploration)
    return {"example": example, "exploration": exploration, "analysis": analysis}


def test_one_step_rewriting_includes_overlapping_positions():
    system = StringRewriteSystem(rules=[("aa", "a")])
    steps = system.one_step_matches("aaaa")
    positions = [step["position"] for step in steps]
    assert len(steps) == 3
    assert positions == [0, 1, 2]
    assert system.successors("aaaa") == ["aaa"]


def test_length_one_lhs_matches_inside_longer_word():
    system = StringRewriteSystem(rules=[("a", "b")])
    steps = system.one_step_matches("ab")
    assert [step["position"] for step in steps] == [0]
    assert system.successors("ab") == ["bb"]


def test_e005_sorting_example_properties():
    run = _run_example("E005_string_sort_confluent")
    analysis = run["analysis"]
    assert run["exploration"]["exploration_complete"] is True
    assert analysis["state_count"] == 6
    assert analysis["edge_count"] == 6
    assert analysis["peak_count"] == 1
    assert analysis["terminating"] is True
    assert analysis["locally_confluent"] is True
    assert analysis["confluent"] is True
    assert analysis["unique_reachable_normal_forms"] is True
    assert analysis["normal_forms"] == ["abc"]


def test_e006_overlap_nonconfluent_properties():
    run = _run_example("E006_string_overlap_nonconfluent")
    analysis = run["analysis"]
    assert run["exploration"]["exploration_complete"] is True
    assert analysis["state_count"] == 4
    assert analysis["edge_count"] == 3
    assert analysis["peak_count"] == 1
    assert analysis["terminating"] is True
    assert analysis["locally_confluent"] is False
    assert analysis["confluent"] is False
    assert analysis["unique_reachable_normal_forms"] is False
    assert analysis["normal_forms"] == ["a", "aa"]
    assert analysis["defect_counts"]["nonjoinability_defect"] > 0
    assert analysis["defect_counts"]["nf_outcome_mismatch"] > 0


def test_completion_before_after_contrast():
    before = _run_example("E007_completion_before")["analysis"]
    after = _run_example("E008_completion_after")["analysis"]

    assert before["state_count"] == 3
    assert before["edge_count"] == 2
    assert before["confluent"] is False
    assert before["defect_counts"]["nonjoinability_defect"] > 0
    assert before["normal_forms"] == ["x", "y"]

    assert after["state_count"] == 3
    assert after["edge_count"] == 3
    assert after["confluent"] is True
    assert after["defect_counts"]["nonjoinability_defect"] == 0
    assert after["defect_counts"]["nf_outcome_mismatch"] == 0
    assert after["normal_forms"] == ["y"]


def test_supported_expected_label_matching_for_curated_examples():
    expected = _catalog_expected_labels()
    for example_id in EXAMPLE_IDS:
        run = _run_example(example_id)
        analysis = run["analysis"]
        supported = [label for label in expected[example_id] if label in SUPPORTED_EXPECTED_LABELS]
        assert all(evaluate_supported_expected_label(label, analysis) for label in supported)


def test_invalid_loader_input_rejected():
    with pytest.raises(ValueError, match="rule lhs must be non-empty"):
        string_rewrite_example_from_mapping(
            {
                "kind": "string_rewrite_system",
                "id": "BAD",
                "label": "bad",
                "rules": [["", "a"]],
                "start_strings": ["a"],
                "bounds": {"max_depth": 2, "max_states": 3},
            }
        )


def test_artifact_serializability():
    run = _run_example("E005_string_sort_confluent")
    summary = {
        "example_id": "E005_string_sort_confluent",
        "state_count": run["analysis"]["state_count"],
        "edge_count": run["analysis"]["edge_count"],
        "normal_forms": run["analysis"]["normal_forms"],
    }
    json.dumps(run["analysis"], sort_keys=True)
    json.dumps(summary, sort_keys=True)


def test_load_string_rewrite_example_smoke():
    example = load_string_rewrite_example(ROOT / "data" / "examples" / "E007_completion_before.yaml")
    assert example["id"] == "E007_completion_before"
    assert example["bounds"]["max_depth"] == 3
