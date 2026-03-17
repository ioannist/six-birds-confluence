#!/usr/bin/env python
"""Generate deterministic peak-analysis JSON artifacts for toy finite ARS examples."""

from __future__ import annotations

import json
from pathlib import Path

from rewriteflat.example_io import load_finite_ars
from rewriteflat.peak_analysis import build_peak_artifact


ROOT = Path(__file__).resolve().parents[1]
EXAMPLE_PATHS = [
    ROOT / "data" / "examples" / "E001_diamond_flat.yaml",
    ROOT / "data" / "examples" / "E002_fork_curved.yaml",
]
OUT_DIR = ROOT / "results" / "peaks"


def write_json(path: Path, payload: dict) -> None:
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def main() -> int:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    summary: list[dict[str, object]] = []

    for example_path in EXAMPLE_PATHS:
        example_id = example_path.stem
        ars = load_finite_ars(example_path)
        artifact = build_peak_artifact(example_id, ars)
        out_path = OUT_DIR / f"{example_id}.json"
        write_json(out_path, artifact)

        summary_row = {
            "example_id": example_id,
            "terminating": artifact["terminating"],
            "peak_count": artifact["peak_count"],
            "nonjoinability_defect_count": artifact["defect_counts"]["nonjoinability_defect"],
            "nf_outcome_mismatch_count": artifact["defect_counts"]["nf_outcome_mismatch"],
        }
        summary.append(summary_row)
        print(
            f"{example_id} peaks={summary_row['peak_count']} "
            f"nonjoinability={summary_row['nonjoinability_defect_count']} "
            f"nf_mismatch={summary_row['nf_outcome_mismatch_count']}"
        )

    summary_payload = {"schema_version": 1, "kind": "finite_ars_peak_summary", "examples": summary}
    write_json(OUT_DIR / "summary.json", summary_payload)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
