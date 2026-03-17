import json

from rewriteflat.term_rewriting import (
    TermRewriteSystem,
    apply_substitution,
    build_term_rewrite_artifact,
    generate_left_linear_critical_pairs,
    load_term_rewrite_example,
    match_pattern,
    parse_term,
    term_to_string,
)


def test_parser_and_pretty_printer_canonical_forms():
    assert term_to_string(parse_term("?x")) == "?x"
    assert term_to_string(parse_term("z")) == "z"
    assert term_to_string(parse_term("s(?x)")) == "s(?x)"
    assert term_to_string(parse_term("add(s(z), ?y)")) == "add(s(z),?y)"


def test_pattern_matching_and_substitution_reconstructs_term():
    pattern = parse_term("add(s(?x),?y)")
    term = parse_term("add(s(z),s(z))")
    subst = match_pattern(pattern, term)
    assert subst is not None
    rebuilt = apply_substitution(pattern, subst)
    assert rebuilt == term


def test_nested_rewriting_on_peano_addition():
    example = load_term_rewrite_example("data/examples/term_rewrite/TRS001_add_peano.yaml")
    system = TermRewriteSystem(example["rules"])

    start = parse_term("add(s(z),s(z))")
    first_targets = [step["target"] for step in system.one_step_matches(start)]
    assert "s(add(z,s(z)))" in first_targets

    mid = parse_term("s(add(z,s(z)))")
    second_targets = [step["target"] for step in system.one_step_matches(mid)]
    assert "s(s(z))" in second_targets

    artifact = build_term_rewrite_artifact("TRS001_add_peano", example)
    assert artifact["normal_forms"] == ["s(s(z))"]
    assert artifact["critical_pair_count"] == 0


def test_root_overlap_critical_pair_on_overlap_example():
    example = load_term_rewrite_example("data/examples/term_rewrite/TRS002_left_linear_overlap.yaml")
    artifact = build_term_rewrite_artifact("TRS002_left_linear_overlap", example)

    assert artifact["critical_pair_count"] == 1
    cp = artifact["critical_pairs"][0]
    assert cp["source_term"] == "f(a,b)"
    assert sorted([cp["left_branch_term"], cp["right_branch_term"]]) == ["g(b)", "h(a)"]


def test_nonroot_overlap_generation_for_nested_example_rules():
    rules = [
        (parse_term("f(g(?x))"), parse_term("p(?x)")),
        (parse_term("g(a)"), parse_term("b")),
    ]
    system = TermRewriteSystem(rules)
    cps = generate_left_linear_critical_pairs(system)
    assert len(cps) == 1
    cp = cps[0]
    assert cp["source_term"] == "f(g(a))"
    assert sorted([cp["left_branch_term"], cp["right_branch_term"]]) == ["f(b)", "p(a)"]
    assert cp["overlap_position"] == [0]


def test_trs003_nested_overlap_nonconfluent_bridge_metrics():
    example = load_term_rewrite_example(
        "data/examples/term_rewrite/TRS003_nested_overlap_nonconfluent.yaml"
    )
    artifact = build_term_rewrite_artifact("TRS003_nested_overlap_nonconfluent", example)
    assert artifact["exploration_complete"] is True
    assert artifact["critical_pair_count"] == 1
    assert artifact["reachable_critical_pair_count"] == 1
    assert artifact["reachable_defective_critical_pair_count"] == 1
    assert artifact["graph_peak_count"] == 1
    assert artifact["reachable_cross_check_match"] is True
    assert artifact["confluent"] is False


def test_trs004_nested_overlap_joinable_bridge_metrics():
    example = load_term_rewrite_example(
        "data/examples/term_rewrite/TRS004_nested_overlap_joinable.yaml"
    )
    artifact = build_term_rewrite_artifact("TRS004_nested_overlap_joinable", example)
    assert artifact["exploration_complete"] is True
    assert artifact["critical_pair_count"] == 1
    assert artifact["reachable_critical_pair_count"] == 1
    assert artifact["reachable_defective_critical_pair_count"] == 0
    assert artifact["graph_peak_count"] == 1
    assert artifact["reachable_cross_check_match"] is True
    assert artifact["confluent"] is True


def test_artifact_and_summary_json_serializable():
    e2 = load_term_rewrite_example("data/examples/term_rewrite/TRS002_left_linear_overlap.yaml")
    a2 = build_term_rewrite_artifact("TRS002_left_linear_overlap", e2)
    assert "example_id" in a2
    assert "critical_pair_count" in a2
    assert "reachable_cross_check_match" in a2
    json.dumps(a2, sort_keys=True)
