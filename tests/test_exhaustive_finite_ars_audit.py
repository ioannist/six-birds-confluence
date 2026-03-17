import json

from rewriteflat.exhaustive_finite_ars_audit import (
    enumerate_labeled_finite_ars,
    run_exhaustive_audit,
)


def test_exact_small_enumeration_counts():
    assert sum(1 for _ in enumerate_labeled_finite_ars(1)) == 2
    assert sum(1 for _ in enumerate_labeled_finite_ars(2)) == 16


def test_exact_small_terminating_counts_up_to_two_states():
    result = run_exhaustive_audit(max_states=2)
    search = result["summary"]["search_space"]
    assert search["total_systems_checked"] == 18
    assert search["total_terminating_systems_checked"] == 4

    per_n = {item["n_states"]: item for item in result["summary"]["per_n"]}
    assert per_n[1]["total_terminating_systems_checked"] == 1
    assert per_n[2]["total_terminating_systems_checked"] == 3


def test_no_discrepancy_on_exhaustive_run_up_to_three_states():
    result = run_exhaustive_audit(max_states=3)
    counts = result["summary"]["discrepancy_counts"]
    assert counts["local_flatness_vs_local_confluence"] == 0
    assert counts["terminating_local_flatness_not_confluent"] == 0
    assert counts["terminating_confluent_not_unique_reachable_normal_forms"] == 0
    assert counts["terminating_unique_reachable_normal_forms_not_confluent"] == 0


def test_artifact_structure_and_serializability():
    result = run_exhaustive_audit(max_states=2)
    summary = result["summary"]
    counterexamples = result["counterexamples"]

    assert summary["schema_version"] == 1
    assert summary["kind"] == "exhaustive_finite_ars_audit"
    assert "search_space" in summary
    assert "per_n" in summary
    assert "discrepancy_counts" in summary
    assert "findings" in summary
    assert counterexamples["schema_version"] == 1
    assert counterexamples["kind"] == "exhaustive_finite_ars_counterexamples"
    json.dumps(summary, sort_keys=True)
    json.dumps(counterexamples, sort_keys=True)


def test_counterexample_keys_exist_when_empty():
    result = run_exhaustive_audit(max_states=2)
    buckets = result["counterexamples"]["counterexamples"]

    assert "local_flatness_vs_local_confluence" in buckets
    assert "terminating_local_flatness_not_confluent" in buckets
    assert "terminating_confluent_not_unique_reachable_normal_forms" in buckets
    assert "terminating_unique_reachable_normal_forms_not_confluent" in buckets
