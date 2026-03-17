#!/usr/bin/env python
"""Run naive bare-graph flatness audit for curated finite ARS examples."""

from __future__ import annotations

import csv
import json
from pathlib import Path

from rewriteflat.example_io import load_finite_ars
from rewriteflat.naive_graph_audit import build_naive_graph_audit


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
OUT_DIR = ROOT / "results" / "audits"
JSON_PATH = OUT_DIR / "naive_graph_flatness_audit.json"
CSV_PATH = OUT_DIR / "naive_graph_flatness_audit.csv"

CSV_FIELDS = [
    "example_id",
    "terminating",
    "has_directed_cycle",
    "naive_directed_loop_flat",
    "undirected_cycle_rank",
    "peak_count",
    "nonjoinability_defect_count",
    "nf_outcome_mismatch_count",
    "locally_confluent",
    "confluent",
]


def main() -> int:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    specs = [(example_id, load_finite_ars(path)) for example_id, path in EXAMPLES]
    artifact = build_naive_graph_audit(specs)

    JSON_PATH.write_text(json.dumps(artifact, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    with CSV_PATH.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=CSV_FIELDS)
        writer.writeheader()
        for row in artifact["examples"]:
            writer.writerow({key: row[key] for key in CSV_FIELDS})

    print(f"audited_examples={len(artifact['examples'])}")
    print(
        "nonconfluent_but_naively_flat="
        + ",".join(artifact["findings"]["nonconfluent_but_naively_flat_example_ids"])
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
