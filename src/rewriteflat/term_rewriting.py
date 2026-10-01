"""Small first-order term rewriting prototype (isolated stretch module)."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml

from .finite_ars import FiniteARS
from .reachable_pairs import reachable_overlap_pairs, require_complete


@dataclass(frozen=True)
class Var:
    name: str


@dataclass(frozen=True)
class Fun:
    symbol: str
    args: tuple["Term", ...]


Term = Var | Fun
Subst = dict[str, Term]


def term_to_string(term: Term) -> str:
    if isinstance(term, Var):
        return f"?{term.name}"
    if not term.args:
        return term.symbol
    return f"{term.symbol}({','.join(term_to_string(arg) for arg in term.args)})"


class _TermParser:
    def __init__(self, text: str) -> None:
        self.text = text
        self.i = 0

    def parse(self) -> Term:
        term = self._parse_term()
        self._skip_ws()
        if self.i != len(self.text):
            raise ValueError(f"unexpected trailing input at index {self.i}")
        return term

    def _skip_ws(self) -> None:
        while self.i < len(self.text) and self.text[self.i].isspace():
            self.i += 1

    def _peek(self) -> str | None:
        self._skip_ws()
        if self.i >= len(self.text):
            return None
        return self.text[self.i]

    def _consume(self, expected: str) -> None:
        self._skip_ws()
        if self.i >= len(self.text) or self.text[self.i] != expected:
            raise ValueError(f"expected '{expected}' at index {self.i}")
        self.i += 1

    def _parse_ident(self) -> str:
        self._skip_ws()
        if self.i >= len(self.text):
            raise ValueError("expected identifier")
        c = self.text[self.i]
        if not (c.isalpha() or c == "_"):
            raise ValueError(f"invalid identifier start at index {self.i}")
        start = self.i
        self.i += 1
        while self.i < len(self.text):
            c = self.text[self.i]
            if c.isalnum() or c == "_":
                self.i += 1
                continue
            break
        return self.text[start:self.i]

    def _parse_term(self) -> Term:
        self._skip_ws()
        nxt = self._peek()
        if nxt is None:
            raise ValueError("unexpected end of input")
        if nxt == "?":
            self.i += 1
            return Var(self._parse_ident())

        sym = self._parse_ident()
        self._skip_ws()
        if self._peek() != "(":
            return Fun(sym, ())

        self._consume("(")
        args: list[Term] = []
        self._skip_ws()
        if self._peek() == ")":
            self._consume(")")
            return Fun(sym, ())

        while True:
            args.append(self._parse_term())
            self._skip_ws()
            nxt = self._peek()
            if nxt == ",":
                self._consume(",")
                continue
            if nxt == ")":
                self._consume(")")
                break
            raise ValueError(f"expected ',' or ')' at index {self.i}")

        return Fun(sym, tuple(args))


def parse_term(text: str) -> Term:
    if not isinstance(text, str) or not text.strip():
        raise ValueError("term must be a non-empty string")
    return _TermParser(text).parse()


def term_node_count(term: Term) -> int:
    if isinstance(term, Var):
        return 1
    return 1 + sum(term_node_count(arg) for arg in term.args)


def iter_positions(term: Term, prefix: tuple[int, ...] = ()):
    yield prefix
    if isinstance(term, Fun):
        for idx, arg in enumerate(term.args):
            yield from iter_positions(arg, prefix + (idx,))


def get_subterm(term: Term, position: tuple[int, ...]) -> Term:
    current = term
    for idx in position:
        if isinstance(current, Var):
            raise ValueError("position descends through variable")
        if idx < 0 or idx >= len(current.args):
            raise ValueError("position index out of range")
        current = current.args[idx]
    return current


def replace_subterm(term: Term, position: tuple[int, ...], replacement: Term) -> Term:
    if not position:
        return replacement
    if isinstance(term, Var):
        raise ValueError("position descends through variable")
    idx = position[0]
    if idx < 0 or idx >= len(term.args):
        raise ValueError("position index out of range")
    new_args = list(term.args)
    new_args[idx] = replace_subterm(new_args[idx], position[1:], replacement)
    return Fun(term.symbol, tuple(new_args))


def _occurs(name: str, term: Term) -> bool:
    if isinstance(term, Var):
        return term.name == name
    return any(_occurs(name, arg) for arg in term.args)


def apply_substitution(term: Term, subst: Subst) -> Term:
    """Simultaneous substitution; replacement terms are not substituted again."""
    if isinstance(term, Var):
        return subst.get(term.name, term)
    return Fun(term.symbol, tuple(apply_substitution(arg, subst) for arg in term.args))


def match_pattern(pattern: Term, term: Term, subst: Subst | None = None) -> Subst | None:
    out: Subst = {} if subst is None else dict(subst)

    def go(p: Term, t: Term) -> bool:
        if isinstance(p, Var):
            if p.name in out:
                return out[p.name] == t
            out[p.name] = t
            return True
        if isinstance(t, Var):
            return False
        if p.symbol != t.symbol or len(p.args) != len(t.args):
            return False
        return all(go(pa, ta) for pa, ta in zip(p.args, t.args))

    return out if go(pattern, term) else None


def unify(t1: Term, t2: Term, subst: Subst | None = None) -> Subst | None:
    out: Subst = {} if subst is None else dict(subst)

    def resolve(t: Term) -> Term:
        if isinstance(t, Var) and t.name in out:
            return resolve(out[t.name])
        if isinstance(t, Fun):
            return Fun(t.symbol, tuple(resolve(arg) for arg in t.args))
        return t

    def bind(name: str, value: Term) -> bool:
        value = resolve(value)
        if isinstance(value, Var) and value.name == name:
            return True
        if _occurs(name, value):
            return False
        out[name] = value
        return True

    def go(a: Term, b: Term) -> bool:
        a = resolve(a)
        b = resolve(b)
        if isinstance(a, Var):
            return bind(a.name, b)
        if isinstance(b, Var):
            return bind(b.name, a)
        if a.symbol != b.symbol or len(a.args) != len(b.args):
            return False
        return all(go(x, y) for x, y in zip(a.args, b.args))

    # Validate optional initial substitutions before recursive resolution.
    def acyclic(name: str, active: frozenset[str]) -> bool:
        if name in active:
            return False
        counts: dict[str, int] = {}
        _collect_var_counts(out[name], counts)
        return all(acyclic(v, active | {name}) for v in counts if v in out)

    for name in list(out):
        if out[name] == Var(name):
            del out[name]
    if not all(acyclic(name, frozenset()) for name in out):
        return None
    if not go(t1, t2):
        return None
    return {name: resolve(value) for name, value in out.items()}


def _collect_var_counts(term: Term, counts: dict[str, int]) -> None:
    if isinstance(term, Var):
        counts[term.name] = counts.get(term.name, 0) + 1
        return
    for arg in term.args:
        _collect_var_counts(arg, counts)


def is_left_linear(term: Term) -> bool:
    counts: dict[str, int] = {}
    _collect_var_counts(term, counts)
    return all(v <= 1 for v in counts.values())


@dataclass(frozen=True)
class Rule:
    lhs: Term
    rhs: Term


class TermRewriteSystem:
    def __init__(self, rules: list[tuple[Term, Term]]) -> None:
        if not isinstance(rules, list) or not rules:
            raise ValueError("rules must be a non-empty list")
        self.rules = tuple(Rule(lhs, rhs) for lhs, rhs in rules)
        for rule in self.rules:
            if isinstance(rule.lhs, Var):
                raise ValueError("rule lhs must not be a variable")
            lhs_vars: dict[str, int] = {}
            rhs_vars: dict[str, int] = {}
            _collect_var_counts(rule.lhs, lhs_vars)
            _collect_var_counts(rule.rhs, rhs_vars)
            if not rhs_vars.keys() <= lhs_vars.keys():
                raise ValueError("rule rhs variables must occur in lhs")
        arities: dict[str, int] = {}
        for rule in self.rules:
            for term in (rule.lhs, rule.rhs):
                for position in iter_positions(term):
                    subterm = get_subterm(term, position)
                    if isinstance(subterm, Fun):
                        arity = len(subterm.args)
                        if arities.setdefault(subterm.symbol, arity) != arity:
                            raise ValueError("function symbols must have a fixed arity")
        self._arities = arities

    def one_step_matches(self, term: Term) -> list[dict[str, Any]]:
        arities = dict(self._arities)
        for position in iter_positions(term):
            subterm = get_subterm(term, position)
            if isinstance(subterm, Fun):
                if arities.setdefault(subterm.symbol, len(subterm.args)) != len(subterm.args):
                    raise ValueError("function symbols must have a fixed arity")
        records: list[dict[str, Any]] = []
        positions = list(iter_positions(term))
        for rule_index, rule in enumerate(self.rules):
            for position in positions:
                subterm = get_subterm(term, position)
                subst = match_pattern(rule.lhs, subterm)
                if subst is None:
                    continue
                target_subterm = apply_substitution(rule.rhs, subst)
                target = replace_subterm(term, position, target_subterm)
                records.append(
                    {
                        "source": term_to_string(term),
                        "target": term_to_string(target),
                        "rule_index": rule_index,
                        "position": list(position),
                        "lhs": term_to_string(rule.lhs),
                        "rhs": term_to_string(rule.rhs),
                    }
                )
        records.sort(key=lambda r: (r["rule_index"], tuple(r["position"]), r["target"]))
        return records

    def successors(self, term: Term) -> list[Term]:
        seen: dict[str, Term] = {}
        for step in self.one_step_matches(term):
            seen[step["target"]] = parse_term(step["target"])
        return [seen[key] for key in sorted(seen.keys())]

    def explore_bounded(
        self,
        start_terms: list[Term],
        max_depth: int,
        max_states: int,
        max_term_nodes: int | None = None,
    ) -> dict[str, Any]:
        if not start_terms:
            raise ValueError("start_terms must be non-empty")
        if max_depth <= 0 or max_states <= 0:
            raise ValueError("max_depth and max_states must be positive")
        if max_term_nodes is not None and max_term_nodes <= 0:
            raise ValueError("max_term_nodes must be positive if provided")

        starts = sorted({term_to_string(t): t for t in start_terms}.items())
        start_terms_sorted = [t for _, t in starts]
        if len(starts) > max_states:
            raise ValueError("start terms exceed max_states")
        if max_term_nodes is not None and any(term_node_count(t) > max_term_nodes
                                              for t in start_terms_sorted):
            raise ValueError("start term exceeds max_term_nodes")

        depth_by: dict[Term, int] = {t: 0 for t in start_terms_sorted}
        queue: list[Term] = list(start_terms_sorted)
        head = 0
        states: set[Term] = set(start_terms_sorted)
        edges: set[tuple[str, str]] = set()
        step_records: list[dict[str, Any]] = []

        suppressed_depth = False
        suppressed_states = False
        suppressed_nodes = False

        while head < len(queue):
            source = queue[head]
            head += 1
            source_depth = depth_by[source]
            source_str = term_to_string(source)

            for step in self.one_step_matches(source):
                target = parse_term(step["target"])
                target_str = step["target"]
                if max_term_nodes is not None and term_node_count(target) > max_term_nodes:
                    suppressed_nodes = True
                    continue

                if target in states:
                    edges.add((source_str, target_str))
                    step_records.append(step)
                    continue

                if source_depth >= max_depth:
                    suppressed_depth = True
                    continue

                if len(states) >= max_states:
                    suppressed_states = True
                    continue

                states.add(target)
                depth_by[target] = source_depth + 1
                queue.append(target)
                edges.add((source_str, target_str))
                step_records.append(step)

        states_sorted = sorted(term_to_string(t) for t in states)
        edges_sorted = sorted(edges)
        step_records_sorted = sorted(
            step_records,
            key=lambda s: (s["source"], s["rule_index"], tuple(s["position"]), s["target"]),
        )
        exploration_complete = not (suppressed_depth or suppressed_states or suppressed_nodes)

        depth_by_state = {
            term_to_string(t): d
            for t, d in sorted(depth_by.items(), key=lambda kv: term_to_string(kv[0]))
        }

        return {
            "start_terms": [term_to_string(t) for t in start_terms_sorted],
            "states": states_sorted,
            "edges": [[s, t] for s, t in edges_sorted],
            "step_records": step_records_sorted,
            "depth_by_state": depth_by_state,
            "bounds": {
                "max_depth": max_depth,
                "max_states": max_states,
                "max_term_nodes": max_term_nodes,
            },
            "exploration_complete": exploration_complete,
            "suppressed": {
                "max_depth": suppressed_depth,
                "max_states": suppressed_states,
                "max_term_nodes": suppressed_nodes,
            },
        }


def _freshen_term(term: Term, suffix: str) -> Term:
    if isinstance(term, Var):
        return Var(f"{term.name}{suffix}")
    return Fun(term.symbol, tuple(_freshen_term(arg, suffix) for arg in term.args))


def _freshened_rule(rule: Rule, suffix: str) -> Rule:
    return Rule(lhs=_freshen_term(rule.lhs, suffix), rhs=_freshen_term(rule.rhs, suffix))


def _cp_signature(source_term: str, left_branch_term: str, right_branch_term: str) -> tuple[str, tuple[str, str]]:
    b1, b2 = sorted([left_branch_term, right_branch_term])
    return (source_term, (b1, b2))


def generate_left_linear_critical_pairs(system: TermRewriteSystem) -> list[dict[str, Any]]:
    if not all(is_left_linear(rule.lhs) for rule in system.rules):
        raise ValueError("critical-pair prototype requires left-linear rules")
    raw: list[dict[str, Any]] = []

    for i, base_rule in enumerate(system.rules):
        for j, overlap_rule in enumerate(system.rules):
            left = _freshened_rule(base_rule, f"_L{i}_{j}")
            right = _freshened_rule(overlap_rule, f"_R{i}_{j}")

            for position in iter_positions(left.lhs):
                subterm = get_subterm(left.lhs, position)
                if isinstance(subterm, Var):
                    continue
                sigma = unify(subterm, right.lhs)
                if sigma is None:
                    continue

                source = apply_substitution(left.lhs, sigma)
                left_branch = apply_substitution(left.rhs, sigma)
                right_source = replace_subterm(left.lhs, position, right.rhs)
                right_branch = apply_substitution(right_source, sigma)

                left_s = term_to_string(left_branch)
                right_s = term_to_string(right_branch)
                if left_s == right_s:
                    continue

                b1, b2 = sorted([left_s, right_s])
                raw.append(
                    {
                        "left_rule_index": i,
                        "right_rule_index": j,
                        "source_term": term_to_string(source),
                        "left_branch_term": b1,
                        "right_branch_term": b2,
                        "overlap_position": list(position),
                    }
                )

    raw.sort(
        key=lambda r: (
            r["source_term"],
            r["left_branch_term"],
            r["right_branch_term"],
            tuple(r["overlap_position"]),
            r["left_rule_index"],
            r["right_rule_index"],
        )
    )

    dedup: list[dict[str, Any]] = []
    seen: set[tuple[str, str, str]] = set()
    for rec in raw:
        # Quotient by renaming variables across the whole branching triple.
        names: dict[str, str] = {}

        def alpha(term: Term) -> Term:
            if isinstance(term, Var):
                return Var(names.setdefault(term.name, f"v{len(names)}"))
            return Fun(term.symbol, tuple(alpha(arg) for arg in term.args))

        source = term_to_string(alpha(parse_term(rec["source_term"])))
        branches = sorted(term_to_string(alpha(parse_term(rec[k])))
                          for k in ("left_branch_term", "right_branch_term"))
        sig = (source, branches[0], branches[1])
        if sig in seen:
            continue
        seen.add(sig)
        dedup.append(rec)

    out: list[dict[str, Any]] = []
    for idx, rec in enumerate(dedup, start=1):
        out.append({"cp_id": f"CP{idx:04d}", **rec})
    return out


def _load_mapping(path: str | Path) -> dict[str, Any]:
    path_obj = Path(path)
    suffix = path_obj.suffix.lower()
    raw = path_obj.read_text(encoding="utf-8")
    if suffix == ".json":
        data = json.loads(raw)
    elif suffix in (".yaml", ".yml"):
        data = yaml.safe_load(raw)
    else:
        raise ValueError(f"unsupported file format: {suffix}")
    if not isinstance(data, dict):
        raise ValueError("example payload must be a mapping")
    return data


def load_term_rewrite_example(path: str | Path) -> dict[str, Any]:
    data = _load_mapping(path)
    if data.get("kind") != "term_rewrite_system":
        raise ValueError("example kind must be 'term_rewrite_system'")

    rules = data.get("rules")
    starts = data.get("start_terms")
    bounds = data.get("bounds", {})
    if not isinstance(rules, list) or not rules:
        raise ValueError("rules must be a non-empty list")
    if not isinstance(starts, list) or not starts:
        raise ValueError("start_terms must be a non-empty list")
    if not isinstance(bounds, dict):
        raise ValueError("bounds must be a mapping")

    parsed_rules: list[tuple[Term, Term]] = []
    for rule in rules:
        if not isinstance(rule, list) or len(rule) != 2:
            raise ValueError(f"invalid rule shape: {rule!r}")
        lhs_text, rhs_text = rule
        if not isinstance(lhs_text, str) or not isinstance(rhs_text, str):
            raise ValueError("rule entries must be strings")
        parsed_rules.append((parse_term(lhs_text), parse_term(rhs_text)))

    parsed_starts: list[Term] = []
    for item in starts:
        if not isinstance(item, str):
            raise ValueError("start_terms entries must be strings")
        parsed_starts.append(parse_term(item))

    parsed_bounds: dict[str, int | None] = {}
    for key in ("max_depth", "max_states", "max_term_nodes"):
        value = bounds.get(key)
        if value is None:
            parsed_bounds[key] = None
            continue
        if not isinstance(value, int) or value <= 0:
            raise ValueError(f"bound '{key}' must be a positive integer")
        parsed_bounds[key] = value

    return {
        "id": data.get("id"),
        "label": data.get("label"),
        "rules": parsed_rules,
        "start_terms": parsed_starts,
        "bounds": parsed_bounds,
    }


def build_term_rewrite_artifact(example_id: str, example: dict[str, Any]) -> dict[str, Any]:
    system = TermRewriteSystem(rules=example["rules"])
    bounds = example["bounds"]
    if bounds["max_depth"] is None or bounds["max_states"] is None:
        raise ValueError("example bounds must include max_depth and max_states")

    exploration = system.explore_bounded(
        start_terms=example["start_terms"],
        max_depth=bounds["max_depth"],
        max_states=bounds["max_states"],
        max_term_nodes=bounds.get("max_term_nodes"),
    )

    states = exploration["states"]
    edges = [tuple(edge) for edge in exploration["edges"]]
    ars = FiniteARS(states=states, edges=edges)

    graph_peak_signatures = {
        _cp_signature(source, left, right)
        for source, left, right in sorted(ars.local_peaks(), key=lambda x: (x[0], x[1], x[2]))
    }

    critical_pairs = generate_left_linear_critical_pairs(system)
    require_complete(exploration)

    system_defective_count = 0
    main_state_set = set(states)

    enriched_cps: list[dict[str, Any]] = []
    for cp in critical_pairs:
        source_s = cp["source_term"]
        left_s = cp["left_branch_term"]
        right_s = cp["right_branch_term"]
        source_reachable = source_s in main_state_set

        local_exploration = system.explore_bounded(
            start_terms=[parse_term(source_s)],
            max_depth=bounds["max_depth"],
            max_states=bounds["max_states"],
            max_term_nodes=bounds.get("max_term_nodes"),
        )
        local_ars = FiniteARS(
            states=local_exploration["states"],
            edges=[tuple(e) for e in local_exploration["edges"]],
        )
        require_complete(local_exploration)
        joinable = local_ars.joinable(left_s, right_s)
        left_nfs = sorted(local_ars.reachable_normal_forms(left_s))
        right_nfs = sorted(local_ars.reachable_normal_forms(right_s))

        left_nf_set = set(left_nfs)
        right_nf_set = set(right_nfs)
        nf_outcome_mismatch = (left_nf_set != right_nf_set) if local_ars.is_terminating() else None
        cp_defective = not joinable

        if cp_defective:
            system_defective_count += 1

        sig = _cp_signature(source_s, left_s, right_s)

        enriched_cps.append(
            {
                **cp,
                "source_reachability_scope": "literal schematic overlap source",
                "source_reachable_from_starts": source_reachable,
                "local_exploration_complete": local_exploration["exploration_complete"],
                "graph_peak_present_from_starts": sig in graph_peak_signatures,
                "joinable": joinable,
                "nonjoinability_defect": not joinable,
                "left_reachable_normal_forms": left_nfs,
                "right_reachable_normal_forms": right_nfs,
                "nf_outcome_mismatch": nf_outcome_mismatch,
            }
        )

    reachable_pairs = reachable_overlap_pairs(system, exploration, terms=True)
    reachable_signatures = {
        _cp_signature(cp["source_term"], cp["left_branch_term"], cp["right_branch_term"])
        for cp in reachable_pairs
    }
    reachable_defective_count = sum(cp["nonjoinability_defect"] for cp in reachable_pairs)

    reachable_missing = sorted(
        [
            {"source_term": sig[0], "branches": [sig[1][0], sig[1][1]]}
            for sig in (reachable_signatures - graph_peak_signatures)
        ],
        key=lambda x: (x["source_term"], x["branches"][0], x["branches"][1]),
    )
    graph_missing = sorted(
        [
            {"source_term": sig[0], "branches": [sig[1][0], sig[1][1]]}
            for sig in (graph_peak_signatures - reachable_signatures)
        ],
        key=lambda x: (x["source_term"], x["branches"][0], x["branches"][1]),
    )

    return {
        "schema_version": 1,
        "kind": "term_rewrite_prototype",
        "example_id": example_id,
        "start_terms": [term_to_string(t) for t in example["start_terms"]],
        "bounds": {
            "max_depth": bounds.get("max_depth"),
            "max_states": bounds.get("max_states"),
            "max_term_nodes": bounds.get("max_term_nodes"),
        },
        "exploration_complete": exploration["exploration_complete"],
        "state_count": len(states),
        "edge_count": len(edges),
        "normal_forms": sorted(ars.normal_forms()),
        "terminating": ars.is_terminating(),
        "confluent": ars.is_confluent(),
        "graph_peak_count": len(graph_peak_signatures),
        "critical_pair_count": len(enriched_cps),
        "reachable_critical_pair_count": len(reachable_pairs),
        "system_defective_critical_pair_count": system_defective_count,
        "reachable_defective_critical_pair_count": reachable_defective_count,
        "reachable_cross_check_match": not reachable_missing and not graph_missing,
        "reachable_critical_pairs_missing_from_graph_peaks": reachable_missing,
        "graph_peaks_missing_from_reachable_critical_pairs": graph_missing,
        "critical_pairs": enriched_cps,
        "reachable_critical_pairs": reachable_pairs,
        "analysis_scope": "complete reachable closure and complete critical-pair closures",
        "critical_pair_scope": "left_linear_nonvariable_overlaps",
        "left_linear_rules": all(is_left_linear(rule.lhs) for rule in system.rules),
    }
