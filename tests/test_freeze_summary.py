import json

from rewriteflat.freeze_summary import (
    REQUIRED_CLAIM_IDS,
    load_claim_support_matrix,
    run_final_freeze,
    validate_claim_support_matrix,
)


_DUMMY_REGRESSION = {
    "success": True,
    "failed_step": None,
    "step_count": 14,
    "executed_step_count": 14,
    "total_runtime_seconds": 1.0,
    "slowest_step": {"name": "unit_tests", "elapsed_seconds": 0.8},
    "steps": [],
}


def test_required_claim_rows_present():
    matrix = load_claim_support_matrix()
    found = {row["claim_id"] for row in matrix["claims"]}
    assert set(REQUIRED_CLAIM_IDS).issubset(found)


def test_evidence_type_coverage_complete():
    matrix = load_claim_support_matrix()
    validation = validate_claim_support_matrix(matrix)
    assert validation["missing_evidence_types"] == []


def test_all_strongest_artifact_paths_exist():
    matrix = load_claim_support_matrix()
    validate_claim_support_matrix(matrix)


def test_final_freeze_summary_structure():
    out = run_final_freeze(run_regression=False, regression_result=_DUMMY_REGRESSION)
    summary = out["summary"]
    assert summary["schema_version"] == 1
    assert summary["kind"] == "final_experiment_summary"
    assert "regression" in summary
    assert "claim_matrix" in summary
    assert "artifact_families" in summary
    assert "implementation" in summary
    assert "remaining_theorem_writing_work" in summary
    assert "freeze_verdict" in summary
    json.dumps(summary, sort_keys=True)


def test_implementation_complete_verdict():
    summary = run_final_freeze(run_regression=False, regression_result=_DUMMY_REGRESSION)["summary"]
    assert summary["freeze_verdict"] == "implementation_complete"
    assert summary["implementation"]["implementation_complete"] is True
    assert summary["implementation"]["remaining_implementation_tasks"] == []


def test_remaining_work_is_theorem_writing_not_implementation():
    summary = run_final_freeze(run_regression=False, regression_result=_DUMMY_REGRESSION)["summary"]
    items = summary["remaining_theorem_writing_work"]
    assert items
    text = "\n".join(items).lower()
    assert "finite terminating left-linear trs" in text
    assert "2-complex" in text or "2-connection" in text
    assert "critical-pair" in text or "local-confluence" in text
