"""Load finite-ARS examples from YAML/JSON files."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import yaml

from .finite_ars import FiniteARS
from .string_rewriting import StringRewriteSystem


def _load_mapping(path: str | Path) -> dict[str, Any]:
    path_obj = Path(path)
    suffix = path_obj.suffix.lower()
    raw = path_obj.read_text(encoding="utf-8")

    if suffix == ".json":
        data = json.loads(raw)
    elif suffix in (".yaml", ".yml"):
        data = yaml.safe_load(raw)
    else:
        raise ValueError(f"unsupported example format: {suffix}")
    if not isinstance(data, dict):
        raise ValueError("example payload must be a mapping")
    return data


def finite_ars_from_mapping(data: dict[str, Any]) -> FiniteARS:
    if data.get("kind") != "finite_ars":
        raise ValueError("example kind must be 'finite_ars'")

    states = data.get("states")
    edges = data.get("edges")
    if not isinstance(states, list):
        raise ValueError("'states' must be a list")
    if not isinstance(edges, list):
        raise ValueError("'edges' must be a list")

    parsed_edges: list[tuple[str, str]] = []
    for item in edges:
        if not isinstance(item, list) or len(item) != 2:
            raise ValueError(f"invalid edge entry: {item!r}")
        src, dst = item
        if not isinstance(src, str) or not isinstance(dst, str):
            raise ValueError(f"edge endpoints must be strings: {item!r}")
        parsed_edges.append((src, dst))

    return FiniteARS(states=states, edges=parsed_edges)


def load_finite_ars(path: str | Path) -> FiniteARS:
    data = _load_mapping(path)
    return finite_ars_from_mapping(data)


def string_rewrite_example_from_mapping(data: dict[str, Any]) -> dict[str, Any]:
    if data.get("kind") != "string_rewrite_system":
        raise ValueError("example kind must be 'string_rewrite_system'")

    rules = data.get("rules")
    start_strings = data.get("start_strings")
    bounds = data.get("bounds", {})
    if not isinstance(rules, list) or not rules:
        raise ValueError("'rules' must be a non-empty list")
    if not isinstance(start_strings, list) or not start_strings:
        raise ValueError("'start_strings' must be a non-empty list")
    if any(not isinstance(word, str) for word in start_strings):
        raise ValueError("start_strings entries must be strings")
    if not isinstance(bounds, dict):
        raise ValueError("'bounds' must be a mapping")

    parsed_rules: list[tuple[str, str]] = []
    for rule in rules:
        if not isinstance(rule, list) or len(rule) != 2:
            raise ValueError(f"invalid rule shape: {rule!r}")
        lhs, rhs = rule
        if not isinstance(lhs, str) or not isinstance(rhs, str):
            raise ValueError(f"rule entries must be strings: {rule!r}")
        if lhs == "":
            raise ValueError("rule lhs must be non-empty")
        parsed_rules.append((lhs, rhs))

    parsed_bounds: dict[str, int | None] = {}
    for key in ("max_depth", "max_states", "max_word_length"):
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
        "start_strings": list(start_strings),
        "bounds": parsed_bounds,
    }


def load_string_rewrite_example(path: str | Path) -> dict[str, Any]:
    data = _load_mapping(path)
    return string_rewrite_example_from_mapping(data)


def load_string_rewrite_system(path: str | Path) -> tuple[dict[str, Any], StringRewriteSystem]:
    example = load_string_rewrite_example(path)
    system = StringRewriteSystem(rules=example["rules"])
    return example, system
