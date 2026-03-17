#!/usr/bin/env python
"""Generate deterministic plaquette JSON artifacts for curated finite ARS examples."""

from __future__ import annotations

import json
from pathlib import Path

from rewriteflat.example_io import load_finite_ars
from rewriteflat.plaquettes import build_plaquette_artifact


ROOT = Path(__file__).resolve().parents[1]
EXAMPLES = [
    ("E001_diamond_flat", ROOT / "data" / "examples" / "E001_diamond_flat.yaml"),
    ("E002_fork_curved", ROOT / "data" / "examples" / "E002_fork_curved.yaml"),
    ("E003_delayed_join_flat", ROOT / "data" / "examples" / "E003_delayed_join_flat.yaml"),
    (
        "E004_bare_graph_counterexample_target",
        ROOT / "data" / "examples" / "E004_bare_graph_counterexample_target.yaml",
    ),
]
OUT_DIR = ROOT / "results" / "plaquettes"


def write_json(path: Path, payload: dict) -> None:
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def main() -> int:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    summary: list[dict[str, object]] = []

    for example_id, example_path in EXAMPLES:
        ars = load_finite_ars(example_path)
        artifact = build_plaquette_artifact(example_id, ars)
        write_json(OUT_DIR / f"{example_id}.json", artifact)

        row = {
            "example_id": example_id,
            "terminating": artifact["terminating"],
            "plaquette_count": artifact["plaquette_count"],
            "joinable_count": artifact["defect_counts"]["joinable"],
            "defective_count": artifact["defect_counts"]["defective"],
        }
        summary.append(row)
        print(
            f"{example_id} plaquettes={row['plaquette_count']} "
            f"joinable={row['joinable_count']} defective={row['defective_count']}"
        )

    summary_payload = {"schema_version": 1, "kind": "finite_ars_plaquette_summary", "examples": summary}
    write_json(OUT_DIR / "summary.json", summary_payload)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
