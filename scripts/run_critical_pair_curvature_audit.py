#!/usr/bin/env python
"""Run critical-pair curvature audit for curated string examples."""

from __future__ import annotations

import csv
import json
from pathlib import Path

from rewriteflat.critical_pair_curvature_audit import build_critical_pair_curvature_audit


ROOT = Path(__file__).resolve().parents[1]
OUT_DIR = ROOT / "results" / "audits"
JSON_PATH = OUT_DIR / "critical_pair_curvature_audit.json"
CSV_PATH = OUT_DIR / "critical_pair_curvature_audit.csv"

CSV_FIELDS = [
    "example_id",
    "terminating",
    "exploration_complete",
    "confluent",
    "unique_reachable_normal_forms",
    "local_peak_count",
    "local_peak_nonjoinability_defect_count",
    "local_peak_nf_outcome_mismatch_count",
    "system_critical_pair_count",
    "reachable_critical_pair_count",
    "system_critical_pair_nonjoinability_defect_count",
    "system_critical_pair_nf_outcome_mismatch_count",
    "reachable_critical_pair_nonjoinability_defect_count",
    "reachable_critical_pair_nf_outcome_mismatch_count",
    "reachable_cross_check_match",
    "nonjoinability_defect_signature_match",
    "nf_outcome_mismatch_signature_match",
    "global_vs_local_peak_alignment",
    "global_vs_reachable_critical_pair_alignment",
    "curvature_generator_story_supported",
]


def main() -> int:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    artifact = build_critical_pair_curvature_audit()
    JSON_PATH.write_text(json.dumps(artifact, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    rows = []
    for item in artifact["examples"]:
        global_part = item["global"]
        local_part = item["local_peaks"]
        cp_part = item["critical_pairs"]
        align = item["alignment"]
        rows.append(
            {
                "example_id": item["example_id"],
                "terminating": global_part["terminating"],
                "exploration_complete": global_part["exploration_complete"],
                "confluent": global_part["confluent"],
                "unique_reachable_normal_forms": global_part["unique_reachable_normal_forms"],
                "local_peak_count": local_part["local_peak_count"],
                "local_peak_nonjoinability_defect_count": local_part[
                    "local_peak_nonjoinability_defect_count"
                ],
                "local_peak_nf_outcome_mismatch_count": local_part[
                    "local_peak_nf_outcome_mismatch_count"
                ],
                "system_critical_pair_count": cp_part["system_critical_pair_count"],
                "reachable_critical_pair_count": cp_part["reachable_critical_pair_count"],
                "system_critical_pair_nonjoinability_defect_count": cp_part[
                    "system_critical_pair_nonjoinability_defect_count"
                ],
                "system_critical_pair_nf_outcome_mismatch_count": cp_part[
                    "system_critical_pair_nf_outcome_mismatch_count"
                ],
                "reachable_critical_pair_nonjoinability_defect_count": cp_part[
                    "reachable_critical_pair_nonjoinability_defect_count"
                ],
                "reachable_critical_pair_nf_outcome_mismatch_count": cp_part[
                    "reachable_critical_pair_nf_outcome_mismatch_count"
                ],
                "reachable_cross_check_match": align["reachable_cross_check_match"],
                "nonjoinability_defect_signature_match": align[
                    "nonjoinability_defect_signature_match"
                ],
                "nf_outcome_mismatch_signature_match": align[
                    "nf_outcome_mismatch_signature_match"
                ],
                "global_vs_local_peak_alignment": align["global_vs_local_peak_alignment"],
                "global_vs_reachable_critical_pair_alignment": align[
                    "global_vs_reachable_critical_pair_alignment"
                ],
                "curvature_generator_story_supported": item[
                    "curvature_generator_story_supported"
                ],
            }
        )

    with CSV_PATH.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=CSV_FIELDS)
        writer.writeheader()
        for row in rows:
            writer.writerow({field: row[field] for field in CSV_FIELDS})

    findings = artifact["findings"]
    print(f"example_count={len(artifact['examples'])}")
    print("confluent=" + ",".join(findings["confluent_example_ids"]))
    print("nonconfluent=" + ",".join(findings["nonconfluent_example_ids"]))
    print(
        "reachable_critical_pair_obstructions="
        + ",".join(findings["examples_with_reachable_critical_pair_obstructions"])
    )
    print(
        "all_examples_support_story="
        + str(findings["all_examples_support_curvature_generator_story"])
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
