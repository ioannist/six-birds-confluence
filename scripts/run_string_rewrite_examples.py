#!/usr/bin/env python
"""Run curated string rewriting examples and emit deterministic JSON artifacts."""

from __future__ import annotations

import json
from pathlib import Path

import yaml

from rewriteflat.example_io import load_string_rewrite_system
from rewriteflat.string_rewriting import (
    SUPPORTED_EXPECTED_LABELS,
    analyze_string_exploration,
    evaluate_supported_expected_label,
)


ROOT = Path(__file__).resolve().parents[1]
OUT_DIR = ROOT / "results" / "string_rewrite"
EXAMPLE_IDS = [
    "E005_string_sort_confluent",
    "E006_string_overlap_nonconfluent",
    "E007_completion_before",
    "E008_completion_after",
]


def _load_catalog_expected_labels() -> dict[str, list[str]]:
    path = ROOT / "project" / "example_catalog.yaml"
    payload = yaml.safe_load(path.read_text(encoding="utf-8"))
    examples = payload.get("examples", [])
    mapping: dict[str, list[str]] = {}
    for item in examples:
        if not isinstance(item, dict):
            continue
        example_id = item.get("id")
        expected_labels = item.get("expected_labels", [])
        if isinstance(example_id, str) and isinstance(expected_labels, list):
            mapping[example_id] = [label for label in expected_labels if isinstance(label, str)]
    return mapping


def _artifact_for_example(example_id: str, expected_labels: list[str]) -> dict:
    path = ROOT / "data" / "examples" / f"{example_id}.yaml"
    example, system = load_string_rewrite_system(path)
    bounds = example["bounds"]
    max_depth = bounds.get("max_depth")
    max_states = bounds.get("max_states")
    max_word_length = bounds.get("max_word_length")
    if max_depth is None or max_states is None:
        raise ValueError(f"example {example_id} must define max_depth and max_states bounds")

    exploration = system.explore_bounded(
        start_strings=example["start_strings"],
        max_depth=max_depth,
        max_states=max_states,
        max_word_length=max_word_length,
    )
    analysis = analyze_string_exploration(exploration)

    supported_expected = [label for label in expected_labels if label in SUPPORTED_EXPECTED_LABELS]
    unsupported_expected = [label for label in expected_labels if label not in SUPPORTED_EXPECTED_LABELS]
    supported_match = all(
        evaluate_supported_expected_label(label, analysis) for label in supported_expected
    )

    return {
        "schema_version": 1,
        "kind": "string_rewrite_exploration",
        "example_id": example_id,
        "bounds": exploration["bounds"],
        "start_strings": exploration["start_strings"],
        "exploration_complete": exploration["exploration_complete"],
        "state_count": analysis["state_count"],
        "edge_count": analysis["edge_count"],
        "step_count": len(exploration["step_records"]),
        "peak_count": analysis["peak_count"],
        "terminating": analysis["terminating"],
        "locally_confluent": analysis["locally_confluent"],
        "confluent": analysis["confluent"],
        "unique_reachable_normal_forms": analysis["unique_reachable_normal_forms"],
        "normal_forms": analysis["normal_forms"],
        "defect_counts": analysis["defect_counts"],
        "states": exploration["states"],
        "edges": [list(edge) for edge in exploration["edges"]],
        "supported_expected_labels": supported_expected,
        "unsupported_expected_labels": unsupported_expected,
        "supported_expected_labels_match": supported_match,
    }


def main() -> int:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    catalog = _load_catalog_expected_labels()
    artifacts = []
    for example_id in EXAMPLE_IDS:
        artifact = _artifact_for_example(example_id, catalog.get(example_id, []))
        artifacts.append(artifact)
        out_path = OUT_DIR / f"{example_id}.json"
        out_path.write_text(json.dumps(artifact, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        b = artifact["bounds"]
        print(
            f"{example_id} bounds=({b['max_depth']},{b['max_states']},{b['max_word_length']}) "
            f"states={artifact['state_count']} peaks={artifact['peak_count']} "
            f"terminating={artifact['terminating']} confluent={artifact['confluent']} "
            f"supported_labels_match={artifact['supported_expected_labels_match']}"
        )

    summary = {
        "schema_version": 1,
        "kind": "string_rewrite_summary",
        "examples": [
            {
                "example_id": artifact["example_id"],
                "state_count": artifact["state_count"],
                "edge_count": artifact["edge_count"],
                "peak_count": artifact["peak_count"],
                "terminating": artifact["terminating"],
                "confluent": artifact["confluent"],
                "normal_forms": artifact["normal_forms"],
                "supported_expected_labels_match": artifact["supported_expected_labels_match"],
            }
            for artifact in artifacts
        ],
    }
    (OUT_DIR / "summary.json").write_text(
        json.dumps(summary, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
