#!/usr/bin/env python
"""Run final experimental freeze workflow."""

from __future__ import annotations

from rewriteflat.freeze_summary import run_final_freeze


def main() -> int:
    out = run_final_freeze()
    reg = out["regression"]
    matrix = out["matrix_validation"]
    summary = out["summary"]

    print(f"regression_status={'passed' if reg['success'] else 'failed'}")
    print(f"regression_runtime_seconds={reg['total_runtime_seconds']:.3f}")
    print(f"claim_count={matrix['claim_count']}")
    print(f"missing_claim_rows={matrix['missing_claim_rows']}")
    print(f"missing_evidence_types={matrix['missing_evidence_types']}")
    print(f"freeze_verdict={summary['freeze_verdict']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
