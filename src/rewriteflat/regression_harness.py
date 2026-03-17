"""Fail-fast regression harness for routine CI-style checks."""

from __future__ import annotations

import os
import subprocess
import sys
import time
from pathlib import Path
from typing import Any, Callable

from .exhaustive_finite_ars_audit import run_exhaustive_audit


ROOT = Path(__file__).resolve().parents[2]


def _small_exhaustive_audit_n3() -> dict[str, Any]:
    result = run_exhaustive_audit(max_states=3)
    summary = result["summary"]
    return {
        "max_states": 3,
        "total_systems_checked": summary["search_space"]["total_systems_checked"],
        "total_terminating_systems_checked": summary["search_space"][
            "total_terminating_systems_checked"
        ],
        "discrepancy_counts": summary["discrepancy_counts"],
    }


def build_regression_steps() -> list[dict[str, Any]]:
    py = sys.executable
    return [
        {
            "name": "unit_tests",
            "kind": "subprocess",
            "command": [py, "-m", "pytest", "-q"],
        },
        {
            "name": "finite_ars_smoke",
            "kind": "subprocess",
            "command": [py, "scripts/finite_ars_smoke_check.py"],
        },
        {
            "name": "peak_artifacts",
            "kind": "subprocess",
            "command": [py, "scripts/generate_peak_artifacts.py"],
        },
        {
            "name": "plaquette_artifacts",
            "kind": "subprocess",
            "command": [py, "scripts/generate_plaquette_artifacts.py"],
        },
        {
            "name": "naive_graph_audit",
            "kind": "subprocess",
            "command": [py, "scripts/run_naive_graph_flatness_audit.py"],
        },
        {
            "name": "string_examples",
            "kind": "subprocess",
            "command": [py, "scripts/run_string_rewrite_examples.py"],
        },
        {
            "name": "critical_pair_analysis",
            "kind": "subprocess",
            "command": [py, "scripts/run_critical_pair_analysis.py"],
        },
        {
            "name": "critical_pair_curvature_audit",
            "kind": "subprocess",
            "command": [py, "scripts/run_critical_pair_curvature_audit.py"],
        },
        {
            "name": "completion_case_study",
            "kind": "subprocess",
            "command": [py, "scripts/run_completion_case_study.py"],
        },
        {
            "name": "diagram_assets",
            "kind": "subprocess",
            "command": [py, "scripts/generate_diagram_assets.py"],
        },
        {
            "name": "term_rewrite_prototype",
            "kind": "subprocess",
            "command": [py, "scripts/run_term_rewrite_prototype.py"],
        },
        {
            "name": "two_complex_generation",
            "kind": "subprocess",
            "command": [py, "scripts/run_two_complex_generation.py"],
        },
        {
            "name": "small_exhaustive_audit_n3",
            "kind": "callable",
            "callable": _small_exhaustive_audit_n3,
            "max_states": 3,
            "writes_artifacts": False,
        },
        {
            "name": "results_ledger",
            "kind": "subprocess",
            "command": [py, "scripts/build_results_ledger.py"],
        },
    ]


def run_regression_steps(
    steps: list[dict[str, Any]] | None = None,
    *,
    env: dict[str, str] | None = None,
    cwd: Path | None = None,
) -> dict[str, Any]:
    step_list = steps if steps is not None else build_regression_steps()
    runtime_start = time.perf_counter()

    effective_cwd = cwd or ROOT
    effective_env = dict(os.environ)
    if env:
        effective_env.update(env)
    src_path = str((ROOT / "src").resolve())
    existing_pythonpath = effective_env.get("PYTHONPATH", "")
    if src_path not in existing_pythonpath.split(os.pathsep):
        effective_env["PYTHONPATH"] = (
            src_path if not existing_pythonpath else src_path + os.pathsep + existing_pythonpath
        )

    step_results: list[dict[str, Any]] = []
    overall_success = True
    failed_step: str | None = None

    for step in step_list:
        step_start = time.perf_counter()
        name = step["name"]
        kind = step["kind"]

        if kind == "subprocess":
            command = step["command"]
            proc = subprocess.run(command, cwd=effective_cwd, env=effective_env, check=False)
            elapsed = time.perf_counter() - step_start
            success = proc.returncode == 0
            result = {
                "name": name,
                "kind": kind,
                "success": success,
                "elapsed_seconds": elapsed,
                "command": command,
                "exit_code": proc.returncode,
            }
        elif kind == "callable":
            fn: Callable[[], Any] = step["callable"]
            try:
                details = fn()
                success = True
                error = None
            except Exception as exc:  # pragma: no cover - defensive
                details = None
                success = False
                error = repr(exc)
            elapsed = time.perf_counter() - step_start
            result = {
                "name": name,
                "kind": kind,
                "success": success,
                "elapsed_seconds": elapsed,
                "callable": getattr(fn, "__name__", "callable"),
                "details": details,
                "error": error,
                "max_states": step.get("max_states"),
                "writes_artifacts": step.get("writes_artifacts"),
            }
        else:
            raise ValueError(f"unsupported step kind: {kind}")

        step_results.append(result)

        if not result["success"]:
            overall_success = False
            failed_step = name
            break

    total_runtime = time.perf_counter() - runtime_start
    slowest = max(step_results, key=lambda r: r["elapsed_seconds"]) if step_results else None

    return {
        "success": overall_success,
        "failed_step": failed_step,
        "step_count": len(step_list),
        "executed_step_count": len(step_results),
        "total_runtime_seconds": total_runtime,
        "slowest_step": {
            "name": slowest["name"],
            "elapsed_seconds": slowest["elapsed_seconds"],
        }
        if slowest
        else None,
        "steps": step_results,
    }
