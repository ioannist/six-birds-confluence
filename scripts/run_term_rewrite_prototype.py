#!/usr/bin/env python
"""Run first-order term rewriting prototype examples."""

from __future__ import annotations

import json
from pathlib import Path

from rewriteflat.term_rewriting import build_term_rewrite_artifact, load_term_rewrite_example


ROOT = Path(__file__).resolve().parents[1]
EXAMPLE_DIR = ROOT / "data" / "examples" / "term_rewrite"
OUT_DIR = ROOT / "results" / "term_rewrite"
EXAMPLE_IDS = [
    "TRS001_add_peano",
    "TRS002_left_linear_overlap",
    "TRS003_nested_overlap_nonconfluent",
    "TRS004_nested_overlap_joinable",
]


def main() -> int:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    artifacts = []
    for example_id in EXAMPLE_IDS:
        example = load_term_rewrite_example(EXAMPLE_DIR / f"{example_id}.yaml")
        artifact = build_term_rewrite_artifact(example_id, example)
        artifacts.append(artifact)
        out_path = OUT_DIR / f"{example_id}.json"
        out_path.write_text(json.dumps(artifact, indent=2, sort_keys=True) + "\n", encoding="utf-8")

        print(
            f"{example_id} complete={artifact['exploration_complete']} "
            f"states={artifact['state_count']} cps={artifact['critical_pair_count']} "
            f"reachable_cps={artifact['reachable_critical_pair_count']} "
            f"reachable_defects={artifact['reachable_defective_critical_pair_count']} "
            f"cross_check={artifact['reachable_cross_check_match']}"
        )

    summary = {
        "schema_version": 1,
        "kind": "term_rewrite_prototype_summary",
        "critical_pair_scope": "left_linear_nonvariable_overlaps",
        "example_count": len(artifacts),
        "examples": [
            {
                "example_id": a["example_id"],
                "exploration_complete": a["exploration_complete"],
                "state_count": a["state_count"],
                "edge_count": a["edge_count"],
                "normal_forms": a["normal_forms"],
                "critical_pair_count": a["critical_pair_count"],
                "reachable_critical_pair_count": a["reachable_critical_pair_count"],
                "reachable_defective_critical_pair_count": a[
                    "reachable_defective_critical_pair_count"
                ],
                "graph_peak_count": a["graph_peak_count"],
                "reachable_cross_check_match": a["reachable_cross_check_match"],
            }
            for a in artifacts
        ],
    }
    (OUT_DIR / "summary.json").write_text(
        json.dumps(summary, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
