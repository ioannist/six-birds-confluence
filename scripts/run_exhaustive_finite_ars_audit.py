#!/usr/bin/env python
"""Run exhaustive finite-ARS audit and write summary/counterexample artifacts."""

from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path

from rewriteflat.exhaustive_finite_ars_audit import run_exhaustive_audit


ROOT = Path(__file__).resolve().parents[1]
OUT_DIR = ROOT / "results" / "audits"
SUMMARY_PATH = OUT_DIR / "exhaustive_finite_ars_n_le_4_summary.json"
ROWS_PATH = OUT_DIR / "exhaustive_finite_ars_n_le_4_rows.csv"
COUNTEREXAMPLE_PATH = OUT_DIR / "exhaustive_finite_ars_n_le_4_counterexamples.json"

ROW_FIELDS = [
    "system_id",
    "n_states",
    "edge_count",
    "peak_count",
    "nonjoinability_defect_count",
    "nf_outcome_mismatch_count",
    "local_flatness",
    "locally_confluent",
    "confluent",
    "unique_reachable_normal_forms",
]


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--max-states", type=int, default=4)
    args = parser.parse_args()

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    result = run_exhaustive_audit(max_states=args.max_states)
    summary = result["summary"]
    rows = result["rows"]
    counterexamples = result["counterexamples"]

    SUMMARY_PATH.write_text(json.dumps(summary, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    COUNTEREXAMPLE_PATH.write_text(
        json.dumps(counterexamples, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    with ROWS_PATH.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=ROW_FIELDS)
        writer.writeheader()
        for row in rows:
            writer.writerow({field: row[field] for field in ROW_FIELDS})

    print(f"total_systems_checked={summary['search_space']['total_systems_checked']}")
    print(f"total_terminating_systems_checked={summary['search_space']['total_terminating_systems_checked']}")
    print(f"discrepancy_counts={summary['discrepancy_counts']}")
    print(f"runtime_seconds={summary['runtime_seconds']:.6f}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
