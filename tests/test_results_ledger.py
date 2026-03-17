import csv
import json
from pathlib import Path

from rewriteflat.results_ledger import build_results_ledger, write_results_ledger


REQUIRED_COLLECTIONS = {
    "exhaustive_ars_audits",
    "boundary_counterexamples",
    "string_examples",
    "critical_pair_audits",
    "completion_case_study",
    "figures",
    "term_rewrite_examples",
    "two_complex_artifacts",
}

KEY_PATHS = {
    "results/audits/exhaustive_finite_ars_n_le_4_summary.json",
    "results/audits/boundary_counterexample_search_n_le_4.json",
    "results/string_rewrite/summary.json",
    "results/audits/critical_pair_curvature_audit.json",
    "results/case_studies/CS001_manual_completion_ab_to_xy.json",
    "results/diagrams/index.json",
    "results/term_rewrite/summary.json",
    "results/two_complex/summary.json",
}


def _id_map(ledger: dict) -> dict[str, str]:
    return {a["relative_path"]: a["artifact_id"] for a in ledger["artifacts"]}


def test_ledger_structure_is_json_serializable():
    ledger = build_results_ledger()
    assert ledger["schema_version"] == 1
    assert ledger["kind"] == "results_ledger"
    assert "generated_at_utc" in ledger
    assert "run_id" in ledger
    assert "artifact_count" in ledger
    assert "collection_counts" in ledger
    assert "artifacts" in ledger
    json.dumps(ledger, sort_keys=True)


def test_required_collections_are_covered():
    ledger = build_results_ledger()
    assert set(ledger["required_collections"]) >= REQUIRED_COLLECTIONS
    assert ledger["missing_required_collections"] == []
    assert REQUIRED_COLLECTIONS.issubset(set(ledger["collection_counts"].keys()))


def test_key_artifact_paths_are_indexed():
    ledger = build_results_ledger()
    paths = {a["relative_path"] for a in ledger["artifacts"]}
    assert KEY_PATHS.issubset(paths)


def test_stable_artifact_ids_for_paths():
    a = build_results_ledger()
    b = build_results_ledger()

    ids_a = _id_map(a)
    ids_b = _id_map(b)

    assert set(ids_a.values()) == set(ids_b.values())
    assert set(ids_a.keys()) == set(ids_b.keys())
    for rel_path, artifact_id in ids_a.items():
        assert ids_b[rel_path] == artifact_id


def test_self_reference_paths_are_excluded_after_write():
    ledger = write_results_ledger()
    paths = {a["relative_path"] for a in ledger["artifacts"]}
    assert "results/index.json" not in paths
    assert "results/summary.csv" not in paths
    assert "results/.gitkeep" not in paths


def test_summary_csv_row_count_matches_json_artifact_count():
    ledger = write_results_ledger()
    summary_path = Path("results/summary.csv")
    with summary_path.open("r", encoding="utf-8", newline="") as handle:
        rows = list(csv.DictReader(handle))
    assert len(rows) == ledger["artifact_count"]


def test_freeze_artifacts_collection_indexed_when_present():
    ledger = build_results_ledger()
    if Path("results/freeze/final_experiment_summary.json").exists():
        assert ledger["collection_counts"].get("freeze_artifacts", 0) > 0
