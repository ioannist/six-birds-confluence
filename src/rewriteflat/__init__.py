"""Rewriteflat package."""

from .finite_ars import FiniteARS
from .example_io import (
    finite_ars_from_mapping,
    load_finite_ars,
    load_string_rewrite_example,
    load_string_rewrite_system,
    string_rewrite_example_from_mapping,
)
from .peak_analysis import analyze_peak, analyze_all_peaks, build_peak_artifact
from .plaquettes import build_all_plaquettes, build_plaquette_artifact, build_plaquette_record
from .naive_graph_audit import (
    build_naive_graph_audit,
    build_naive_graph_audit_row,
    has_directed_cycle,
    naive_directed_loop_flat,
    undirected_cycle_rank,
)
from .exhaustive_finite_ars_audit import (
    enumerate_labeled_finite_ars,
    build_terminating_audit_row,
    run_exhaustive_audit,
)
from .boundary_counterexamples import (
    is_normalizing,
    naive_nf_peak_flatness,
    find_minimal_nonconfluence_witness,
    find_minimal_defective_peak,
    find_minimal_directed_cycle,
    build_boundary_counterexample_artifact,
)
from .string_rewriting import (
    StringRewriteSystem,
    analyze_string_exploration,
    evaluate_supported_expected_label,
    finite_ars_from_exploration,
)
from .critical_pairs import (
    enumerate_overlap_instances,
    enumerate_critical_pairs,
    analyze_string_example_critical_pairs,
    build_critical_pair_artifact,
)
from .critical_pair_curvature_audit import (
    build_example_curvature_audit_row,
    build_critical_pair_curvature_audit,
)
from .completion_case_study import (
    DEFAULT_CASE_ID,
    load_completion_case_study,
    build_completion_case_stage_row,
    build_completion_case_study_artifact,
)

__all__ = [
    "__version__",
    "FiniteARS",
    "load_finite_ars",
    "finite_ars_from_mapping",
    "load_string_rewrite_example",
    "load_string_rewrite_system",
    "string_rewrite_example_from_mapping",
    "StringRewriteSystem",
    "finite_ars_from_exploration",
    "analyze_string_exploration",
    "evaluate_supported_expected_label",
    "enumerate_overlap_instances",
    "enumerate_critical_pairs",
    "analyze_string_example_critical_pairs",
    "build_critical_pair_artifact",
    "build_example_curvature_audit_row",
    "build_critical_pair_curvature_audit",
    "DEFAULT_CASE_ID",
    "load_completion_case_study",
    "build_completion_case_stage_row",
    "build_completion_case_study_artifact",
    "analyze_peak",
    "analyze_all_peaks",
    "build_peak_artifact",
    "build_plaquette_record",
    "build_all_plaquettes",
    "build_plaquette_artifact",
    "has_directed_cycle",
    "naive_directed_loop_flat",
    "undirected_cycle_rank",
    "build_naive_graph_audit_row",
    "build_naive_graph_audit",
    "enumerate_labeled_finite_ars",
    "build_terminating_audit_row",
    "run_exhaustive_audit",
    "is_normalizing",
    "naive_nf_peak_flatness",
    "find_minimal_nonconfluence_witness",
    "find_minimal_defective_peak",
    "find_minimal_directed_cycle",
    "build_boundary_counterexample_artifact",
]
__version__ = "0.1.0"
