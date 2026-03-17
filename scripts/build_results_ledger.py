#!/usr/bin/env python
"""Build central results ledger JSON and CSV."""

from __future__ import annotations

import json

from rewriteflat.results_ledger import write_results_ledger


def main() -> int:
    ledger = write_results_ledger(root="results")
    print(f"artifact_count={ledger['artifact_count']}")
    print("collection_counts=" + json.dumps(ledger["collection_counts"], sort_keys=True))
    print("missing_required_collections=" + json.dumps(ledger["missing_required_collections"]))
    print(f"run_id={ledger['run_id']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
