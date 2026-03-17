#!/usr/bin/env python
"""Run fail-fast regression harness."""

from __future__ import annotations

import argparse

from rewriteflat.regression_harness import build_regression_steps, run_regression_steps


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--list-steps", action="store_true")
    args = parser.parse_args()

    steps = build_regression_steps()
    if args.list_steps:
        for step in steps:
            print(step["name"])
        return 0

    result = run_regression_steps(steps=steps)

    for step in result["steps"]:
        if step["success"]:
            print(f"OK step={step['name']} elapsed_seconds={step['elapsed_seconds']:.3f}")
        else:
            if step["kind"] == "subprocess":
                print(
                    "FAILED "
                    f"step={step['name']} exit_code={step['exit_code']} "
                    f"elapsed_seconds={step['elapsed_seconds']:.3f} "
                    f"command={' '.join(step['command'])}"
                )
            else:
                print(
                    "FAILED "
                    f"step={step['name']} elapsed_seconds={step['elapsed_seconds']:.3f} "
                    f"callable={step['callable']} error={step['error']}"
                )
            return 1

    slowest = result["slowest_step"]
    print(
        "PASS regression "
        f"steps={result['executed_step_count']}/{result['step_count']} "
        f"total_seconds={result['total_runtime_seconds']:.3f} "
        f"slowest_step={slowest['name']} "
        f"slowest_seconds={slowest['elapsed_seconds']:.3f}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
