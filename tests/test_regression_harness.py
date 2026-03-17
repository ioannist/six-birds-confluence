import re
from pathlib import Path

from rewriteflat.regression_harness import build_regression_steps, run_regression_steps


REQUIRED_STEPS = {
    "unit_tests",
    "finite_ars_smoke",
    "peak_artifacts",
    "plaquette_artifacts",
    "naive_graph_audit",
    "string_examples",
    "critical_pair_analysis",
    "critical_pair_curvature_audit",
    "completion_case_study",
    "diagram_assets",
    "term_rewrite_prototype",
    "two_complex_generation",
    "small_exhaustive_audit_n3",
    "results_ledger",
}


def test_step_list_has_required_coverage():
    names = {step["name"] for step in build_regression_steps()}
    assert REQUIRED_STEPS.issubset(names)


def test_small_exhaustive_step_is_non_clobbering():
    step = next(step for step in build_regression_steps() if step["name"] == "small_exhaustive_audit_n3")
    assert step["kind"] == "callable"
    assert step["max_states"] == 3
    assert step["writes_artifacts"] is False


def test_makefile_has_regression_target():
    text = Path("Makefile").read_text(encoding="utf-8")
    assert re.search(r"(?m)^regression:\s*$", text)


def test_run_summary_structure_for_helper_steps():
    steps = [
        {
            "name": "ok_callable",
            "kind": "callable",
            "callable": lambda: {"ok": True},
            "writes_artifacts": False,
        }
    ]
    result = run_regression_steps(steps=steps)
    assert result["success"] is True
    assert "total_runtime_seconds" in result
    assert "steps" in result
    assert result["executed_step_count"] == 1
    assert result["slowest_step"]["name"] == "ok_callable"


def test_list_steps_order_stable_prefix():
    names = [step["name"] for step in build_regression_steps()]
    assert names[0] == "unit_tests"
    assert names[-1] == "results_ledger"
