#!/usr/bin/env python
"""Generate reduction two-complex / elementary holonomy artifacts."""

from __future__ import annotations

from rewriteflat.two_complex import write_two_complex_artifacts


def main() -> int:
    out = write_two_complex_artifacts()
    summary = out["summary"]

    print(f"example_count={len(summary['examples'])}")
    for row in summary["examples"]:
        print(
            f"{row['example_id']} trivial={row['trivial_count']} "
            f"nontrivial={row['nontrivial_count']}"
        )
    print(
        "string_holonomy_elimination="
        + str(summary["findings"]["string_pair_holonomy_elimination_observed"])
    )
    print(
        "trs_holonomy_elimination="
        + str(summary["findings"]["trs_pair_holonomy_elimination_observed"])
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
