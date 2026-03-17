#!/usr/bin/env python
"""Run the manual completion case study and emit JSON/CSV artifacts."""

from __future__ import annotations

import csv
import json
from pathlib import Path

from rewriteflat.completion_case_study import (
    DEFAULT_CASE_ID,
    build_completion_case_study_artifact,
)


ROOT = Path(__file__).resolve().parents[1]
OUT_DIR = ROOT / "results" / "case_studies"
JSON_PATH = OUT_DIR / f"{DEFAULT_CASE_ID}.json"
CSV_PATH = OUT_DIR / f"{DEFAULT_CASE_ID}.csv"

CSV_FIELDS = [
    "case_id",
    "stage_id",
    "stage_index",
    "example_id",
    "rule_count",
    "exploration_complete",
    "terminating",
    "confluent",
    "unique_reachable_normal_forms",
    "local_peak_count",
    "local_peak_nonjoinability_defect_count",
    "local_peak_nf_outcome_mismatch_count",
    "system_critical_pair_count",
    "reachable_critical_pair_count",
    "system_defective_critical_pair_count",
    "reachable_defective_critical_pair_count",
    "normal_forms",
]


def main() -> int:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    artifact = build_completion_case_study_artifact(DEFAULT_CASE_ID)
    JSON_PATH.write_text(json.dumps(artifact, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    with CSV_PATH.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=CSV_FIELDS)
        writer.writeheader()
        for stage in artifact["stages"]:
            row = {field: stage[field] for field in CSV_FIELDS}
            row["normal_forms"] = json.dumps(stage["normal_forms"])
            writer.writerow(row)

    print(f"case_id={artifact['case_id']}")
    print("stages=" + ",".join(stage["stage_id"] for stage in artifact["stages"]))
    for delta in artifact["stage_deltas"]:
        print(
            "delta="
            + delta["from_stage_id"]
            + "->"
            + delta["to_stage_id"]
            + " added_rules="
            + json.dumps(delta["added_rules"])
        )
    for stage in artifact["stages"]:
        print(
            f"{stage['stage_id']}: confluent={stage['confluent']} "
            f"reachable_defective_cp={stage['reachable_defective_critical_pair_count']}"
        )
    print(
        "curvature_elimination_story_worked_cleanly="
        + str(artifact["findings"]["curvature_elimination_story_worked_cleanly"])
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
