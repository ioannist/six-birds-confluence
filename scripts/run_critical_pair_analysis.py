#!/usr/bin/env python
"""Run critical-pair analysis for curated string rewrite examples."""

from __future__ import annotations

import json
from pathlib import Path

from rewriteflat.critical_pairs import build_critical_pair_artifact
from rewriteflat.example_io import load_string_rewrite_system


ROOT = Path(__file__).resolve().parents[1]
OUT_DIR = ROOT / "results" / "critical_pairs"
EXAMPLE_IDS = [
    "E005_string_sort_confluent",
    "E006_string_overlap_nonconfluent",
    "E007_completion_before",
    "E008_completion_after",
]


def main() -> int:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    artifacts = []

    for example_id in EXAMPLE_IDS:
        path = ROOT / "data" / "examples" / f"{example_id}.yaml"
        example, system = load_string_rewrite_system(path)
        artifact = build_critical_pair_artifact(example_id, example, system)
        artifacts.append(artifact)
        (OUT_DIR / f"{example_id}.json").write_text(
            json.dumps(artifact, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )

        print(
            f"{example_id} system_cp={artifact['system_critical_pair_count']} "
            f"reachable_cp={artifact['reachable_critical_pair_count']} "
            f"graph_peaks={artifact['graph_peak_count']} "
            f"reachable_defects={artifact['reachable_defective_critical_pair_count']} "
            f"cross_check_match={artifact['cross_check']['reachable_cross_check_match']}"
        )

    summary = {
        "schema_version": 1,
        "kind": "string_critical_pair_summary",
        "examples": [
            {
                "example_id": artifact["example_id"],
                "system_critical_pair_count": artifact["system_critical_pair_count"],
                "reachable_critical_pair_count": artifact["reachable_critical_pair_count"],
                "graph_peak_count": artifact["graph_peak_count"],
                "defective_critical_pair_count": artifact["defective_critical_pair_count"],
                "reachable_defective_critical_pair_count": artifact[
                    "reachable_defective_critical_pair_count"
                ],
                "reachable_cross_check_match": artifact["cross_check"][
                    "reachable_cross_check_match"
                ],
            }
            for artifact in artifacts
        ],
    }
    (OUT_DIR / "summary.json").write_text(
        json.dumps(summary, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
