import json
from pathlib import Path

from rewriteflat.example_io import load_finite_ars
from rewriteflat.finite_ars import FiniteARS
from rewriteflat.peak_analysis import analyze_all_peaks, build_peak_artifact


ROOT = Path(__file__).resolve().parents[1]


def test_diamond_peak_defects():
    ars = load_finite_ars(ROOT / "data" / "examples" / "E001_diamond_flat.yaml")
    peaks = analyze_all_peaks(ars)
    assert len(peaks) == 1

    peak = peaks[0]
    assert peak["nonjoinability_defect"] is False
    assert peak["nf_outcome_mismatch"] is False
    assert peak["nf_symmetric_difference_size"] == 0
    assert peak["left_reachable_normal_forms"] == ["D"]
    assert peak["right_reachable_normal_forms"] == ["D"]


def test_fork_peak_defects():
    ars = load_finite_ars(ROOT / "data" / "examples" / "E002_fork_curved.yaml")
    peaks = analyze_all_peaks(ars)
    assert len(peaks) == 1

    peak = peaks[0]
    assert peak["source"] == "A"
    assert peak["left"] == "B"
    assert peak["right"] == "C"
    assert peak["nonjoinability_defect"] is True
    assert peak["nf_outcome_mismatch"] is True
    assert peak["nf_symmetric_difference_size"] == 2
    assert peak["left_reachable_normal_forms"] == ["D"]
    assert peak["right_reachable_normal_forms"] == ["C"]


def test_nonterminating_guard_on_nf_mismatch():
    ars = FiniteARS(
        states=["A", "B", "C"],
        edges=[("A", "B"), ("A", "C"), ("B", "B"), ("C", "C")],
    )
    peaks = analyze_all_peaks(ars)
    assert len(peaks) == 1

    peak = peaks[0]
    assert peak["nonjoinability_defect"] is True
    assert peak["nf_outcome_mismatch"] is None
    assert peak["nf_symmetric_difference_size"] is None


def test_artifact_structure_is_json_serializable():
    ars = load_finite_ars(ROOT / "data" / "examples" / "E001_diamond_flat.yaml")
    artifact = build_peak_artifact("E001_diamond_flat", ars)

    assert artifact["schema_version"] == 1
    assert artifact["kind"] == "finite_ars_peak_analysis"
    assert artifact["peak_count"] == 1
    assert artifact["defect_counts"]["nonjoinability_defect"] == 0
    assert artifact["defect_counts"]["nf_outcome_mismatch"] == 0
    json.dumps(artifact, sort_keys=True)
