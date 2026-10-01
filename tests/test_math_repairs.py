"""Counterexamples for the mathematical failures found during review."""

import pytest

from rewriteflat.critical_pairs import build_critical_pair_artifact
from rewriteflat.finite_ars import FiniteARS
from rewriteflat.peak_analysis import analyze_peak
from rewriteflat.string_rewriting import StringRewriteSystem, analyze_string_exploration
from rewriteflat.term_rewriting import (
    TermRewriteSystem, apply_substitution, build_term_rewrite_artifact,
    generate_left_linear_critical_pairs, match_pattern, parse_term, unify,
)
from rewriteflat.two_complex import _holonomy_status, build_selected_two_complex_artifacts


def trs(*rules):
    return TermRewriteSystem([(parse_term(a), parse_term(b)) for a, b in rules])


def term_example(system, start, **bounds):
    return {"rules": [(r.lhs, r.rhs) for r in system.rules],
            "start_terms": [parse_term(start)],
            "bounds": {"max_depth": 8, "max_states": 100, "max_term_nodes": 30, **bounds}}


def string_example(start, **bounds):
    return {"start_strings": [start],
            "bounds": {"max_depth": 8, "max_states": 100, "max_word_length": 30, **bounds}}


def test_joinable_peak_can_have_different_normal_form_outcome_sets():
    # B and C share D, while B additionally reaches E. This peak has a filler.
    ars = FiniteARS("ABCDE", [("A", "B"), ("A", "C"),
                              ("B", "D"), ("C", "D"), ("B", "E")])
    peak = analyze_peak(ars, "A", "B", "C")
    assert peak["joinable"] and peak["nf_outcome_mismatch"]
    assert _holonomy_status(True, True) == ("trivial", None)


def test_indirect_occurs_check_rejects_infinite_term():
    assert unify(parse_term("f(?x,?y)"), parse_term("f(g(?y),g(?x))")) is None
    assert unify(parse_term("?x"), parse_term("a"),
                 {"x": parse_term("?y"), "y": parse_term("?x")}) is None


def test_unifier_is_normalized_and_solves_original_equation():
    a, b = parse_term("f(?x,?y)"), parse_term("f(g(?y),a)")
    sigma = unify(a, b)
    assert sigma is not None
    assert apply_substitution(a, sigma) == apply_substitution(b, sigma)
    assert sigma["x"] == parse_term("g(a)")


def test_matching_substitution_is_simultaneous_on_open_terms():
    pattern, target = parse_term("f(?x,?y)"), parse_term("f(?y,a)")
    sigma = match_pattern(pattern, target)
    assert apply_substitution(pattern, sigma) == target
    assert trs(("f(?x)", "g(?x)")).one_step_matches(parse_term("f(?x)"))[0]["target"] == "g(?x)"


def test_proper_self_overlap_is_not_omitted():
    pairs = generate_left_linear_critical_pairs(trs(("f(f(?x))", "g(?x)")))
    assert len(pairs) == 1
    assert pairs[0]["overlap_position"] == [0]


def test_critical_pairs_are_deduplicated_modulo_alpha_renaming():
    pairs = generate_left_linear_critical_pairs(trs(("f(?x)", "g(?x)"), ("f(?y)", "h(?y)")))
    assert len(pairs) == 1


@pytest.mark.parametrize("rules,reason", [
    ([("?x", "a")], "lhs must not"),
    ([("f(?x)", "g(?y)")], "rhs variables"),
    ([("f(a)", "f")], "fixed arity"),
])
def test_invalid_trs_rules_rejected(rules, reason):
    with pytest.raises(ValueError, match=reason):
        trs(*rules)


def test_non_left_linear_rules_do_not_enter_left_linear_generator():
    with pytest.raises(ValueError, match="left-linear"):
        generate_left_linear_critical_pairs(trs(("f(?x,?x)", "a")))


def test_contextual_string_overlaps_are_reachable_instances():
    system = StringRewriteSystem([("ab", "x"), ("ab", "y")])
    artifact = build_critical_pair_artifact("context", string_example("zab"), system)
    assert artifact["system_critical_pair_count"] == 1
    assert artifact["reachable_critical_pair_count"] == 1
    assert artifact["reachable_critical_pairs"][0]["source_word"] == "zab"
    assert artifact["cross_check"]["reachable_cross_check_match"]


def test_ground_contextual_instances_of_schematic_term_overlaps():
    system = trs(("f(?x)", "g(?x)"), ("f(?y)", "h(?y)"))
    artifact = build_term_rewrite_artifact("ground", term_example(system, "k(f(a))"))
    assert artifact["reachable_critical_pair_count"] == 1
    assert artifact["reachable_critical_pairs"][0]["source_term"] == "k(f(a))"
    assert artifact["reachable_cross_check_match"]


def test_disjoint_string_peaks_are_not_critical_overlaps():
    system = StringRewriteSystem([("a", "b"), ("c", "d")])
    artifact = build_critical_pair_artifact("commute", string_example("ac"), system)
    assert artifact["graph_peak_count"] == 1
    assert artifact["reachable_critical_pair_count"] == 0
    assert not artifact["cross_check"]["reachable_cross_check_match"]


def test_variable_position_term_peaks_are_not_critical_overlaps():
    system = trs(("f(?x)", "g(?x)"), ("a", "b"))
    artifact = build_term_rewrite_artifact("variable", term_example(system, "f(a)"))
    assert artifact["graph_peak_count"] == 1
    assert artifact["reachable_critical_pair_count"] == 0
    assert artifact["confluent"]


def test_incomplete_string_search_cannot_certify_nonjoinability():
    system = StringRewriteSystem([("a", "b"), ("a", "c"), ("b", "d"), ("c", "d")])
    with pytest.raises(ValueError, match="inconclusive"):
        build_critical_pair_artifact("truncated", string_example("a", max_depth=1), system)
    exploration = system.explore_bounded(["a"], 1, 100)
    analysis = analyze_string_exploration(exploration)
    assert not analysis["reachable_closure_properties_certified"]
    assert analysis["analysis_scope"] == "explored finite graph"


def test_incomplete_term_search_cannot_certify_nonjoinability():
    system = trs(("a", "b"), ("a", "c"), ("b", "d"), ("c", "d"))
    with pytest.raises(ValueError, match="inconclusive"):
        build_term_rewrite_artifact("truncated", term_example(system, "a", max_depth=1))


def test_deletion_rules_can_reach_empty_word():
    system = StringRewriteSystem([("a", ""), ("a", "b"), ("b", "")])
    artifact = build_critical_pair_artifact("empty", string_example("a"), system)
    assert artifact["reachable_defective_critical_pair_count"] == 0


def test_termination_check_handles_long_chains():
    states = [str(i) for i in range(2000)]
    assert FiniteARS(states, zip(states, states[1:])).is_terminating()


def test_all_exported_fillers_are_paths_in_their_own_one_skeleton():
    for artifact in build_selected_two_complex_artifacts()["artifacts"]:
        edges = {(e["source"], e["target"]) for e in artifact["one_cells"]}
        states = set(artifact["zero_cells"])
        for cell in artifact["two_cells"]:
            boundary = cell["boundary"]
            for side in ("left", "right"):
                path = boundary[f"{side}_edge_path_states"]
                assert set(path) <= states and set(zip(path, path[1:])) <= edges
                if cell["join_witness"] is not None:
                    filler = boundary[f"{side}_filler_path_states"]
                    assert filler[0] == path[-1] and filler[-1] == cell["join_witness"]
                    assert set(zip(filler, filler[1:])) <= edges
            assert (cell["elementary_holonomy_status"] == "trivial") == (cell["join_witness"] is not None)
            loop = boundary["closed_boundary_walk"]
            if cell["join_witness"] is None:
                assert loop is None and cell["attachment_status"] == "unfilled_peak"
            else:
                forward, reverse = loop["forward_route_states"], loop["reverse_route_states"]
                assert forward[0] == reverse[-1] == cell["source_0cell"]
                assert forward[-1] == reverse[0] == cell["join_witness"]
                assert set(zip(forward, forward[1:])) <= edges
                assert set(zip(reverse[1:], reverse)) <= edges


def test_nonterminating_term_pairs_leave_normal_form_diagnostic_unset():
    system = trs(("a", "b"), ("a", "c"), ("b", "a"), ("c", "a"))
    artifact = build_term_rewrite_artifact("cycle", term_example(system, "a"))
    assert artifact["confluent"] and not artifact["terminating"]
    assert artifact["system_defective_critical_pair_count"] == 0
    assert artifact["critical_pairs"][0]["nf_outcome_mismatch"] is None


def test_skip_regression_does_not_invent_a_success_receipt():
    from rewriteflat.freeze_summary import run_final_freeze
    with pytest.raises(ValueError, match="explicit regression result"):
        run_final_freeze(run_regression=False)
