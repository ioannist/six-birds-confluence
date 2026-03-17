#!/usr/bin/env python
"""Run boundary counterexample search and emit JSON/CSV artifacts."""

from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path

from rewriteflat.boundary_counterexamples import build_boundary_counterexample_artifact


ROOT = Path(__file__).resolve().parents[1]
OUT_DIR = ROOT / "results" / "audits"
JSON_PATH = OUT_DIR / "boundary_counterexample_search_n_le_4.json"
CSV_PATH = OUT_DIR / "boundary_counterexample_search_n_le_4_summary.csv"

CSV_FIELDS = [
    "overclaim_id",
    "status",
    "witness_id",
    "system_id",
    "n_states",
    "edge_count",
    "terminating",
    "normalizing",
    "local_flatness",
    "locally_confluent",
    "confluent",
    "unique_reachable_normal_forms",
    "naive_nf_peak_flatness",
    "naive_directed_loop_flat",
]


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--max-states", type=int, default=4)
    args = parser.parse_args()

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    artifact = build_boundary_counterexample_artifact(max_states=args.max_states)
    JSON_PATH.write_text(json.dumps(artifact, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    rows = []
    for entry in artifact["overclaims"]:
        row = {"overclaim_id": entry["overclaim_id"], "status": entry["status"]}
        if entry["status"] == "found":
            witness = entry["witness"]
            metrics = witness["metrics"]
            row.update(
                {
                    "witness_id": witness["witness_id"],
                    "system_id": witness["system_id"],
                    "n_states": witness["n_states"],
                    "edge_count": len(witness["edges"]),
                    "terminating": metrics["terminating"],
                    "normalizing": metrics["normalizing"],
                    "local_flatness": metrics["local_flatness"],
                    "locally_confluent": metrics["locally_confluent"],
                    "confluent": metrics["confluent"],
                    "unique_reachable_normal_forms": metrics["unique_reachable_normal_forms"],
                    "naive_nf_peak_flatness": metrics["naive_nf_peak_flatness"],
                    "naive_directed_loop_flat": metrics["naive_directed_loop_flat"],
                }
            )
        else:
            for key in CSV_FIELDS:
                row.setdefault(key, "")
        rows.append(row)

    with CSV_PATH.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=CSV_FIELDS)
        writer.writeheader()
        for row in rows:
            writer.writerow({field: row.get(field, "") for field in CSV_FIELDS})

    found = [entry for entry in artifact["overclaims"] if entry["status"] == "found"]
    print("found_overclaims=" + ",".join(entry["overclaim_id"] for entry in found))
    for entry in found:
        witness = entry["witness"]
        print(f"{entry['overclaim_id']} {witness['witness_id']} {witness['system_id']}")
    print(f"runtime_seconds={artifact['runtime_seconds']:.6f}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
