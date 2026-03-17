#!/usr/bin/env python
"""Smoke-check finite ARS toy examples."""

from __future__ import annotations

import json
from pathlib import Path

from rewriteflat.example_io import load_finite_ars


ROOT = Path(__file__).resolve().parents[1]
EXAMPLES = [
    ROOT / "data" / "examples" / "E001_diamond_flat.yaml",
    ROOT / "data" / "examples" / "E002_fork_curved.yaml",
]


def summarize(path: Path) -> dict[str, object]:
    ars = load_finite_ars(path)
    return {
        "id": path.stem,
        "state_count": len(ars.states),
        "edge_count": len(ars.edges),
        "terminating": ars.is_terminating(),
        "local_peak_count": len(ars.local_peaks()),
        "locally_confluent": ars.is_locally_confluent(),
        "confluent": ars.is_confluent(),
        "unique_reachable_normal_forms": ars.has_unique_reachable_normal_forms(),
        "normal_forms": sorted(ars.normal_forms()),
    }


def main() -> int:
    for path in EXAMPLES:
        print(json.dumps(summarize(path), sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
