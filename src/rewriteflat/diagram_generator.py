"""Diagram asset generation for finite ARS and string rewriting examples."""

from __future__ import annotations

import json
import shutil
import subprocess
from pathlib import Path
from typing import Any

from .critical_pairs import build_critical_pair_artifact
from .example_io import load_finite_ars, load_string_rewrite_system
from .plaquettes import build_plaquette_artifact
from .string_rewriting import finite_ars_from_exploration

ROOT = Path(__file__).resolve().parents[2]
DEFAULT_OUT_DIR = ROOT / "results" / "diagrams"

REQUIRED_EXAMPLES = [
    "E001_diamond_flat",
    "E002_fork_curved",
    "E003_delayed_join_flat",
    "E006_string_overlap_nonconfluent",
    "E007_completion_before",
    "E008_completion_after",
]


def _q(value: str) -> str:
    escaped = value.replace("\\", "\\\\").replace('"', '\\"')
    return f'"{escaped}"'


def _display_path(path: Path) -> str:
    try:
        return path.relative_to(ROOT).as_posix()
    except ValueError:
        return path.as_posix()


def _distance_map(ars, start: str) -> dict[str, int]:
    distances: dict[str, int] = {start: 0}
    queue = [start]
    idx = 0
    while idx < len(queue):
        current = queue[idx]
        idx += 1
        base = distances[current]
        for nxt in sorted(ars.successors(current)):
            if nxt in distances:
                continue
            distances[nxt] = base + 1
            queue.append(nxt)
    return distances


def _shortest_path_states(ars, start: str, target: str) -> list[str]:
    if start == target:
        return [start]

    parents: dict[str, str | None] = {start: None}
    queue = [start]
    idx = 0
    while idx < len(queue):
        current = queue[idx]
        idx += 1
        for nxt in sorted(ars.successors(current)):
            if nxt in parents:
                continue
            parents[nxt] = current
            if nxt == target:
                queue = []
                break
            queue.append(nxt)

    if target not in parents:
        raise ValueError(f"no path from {start} to {target}")

    path = [target]
    current = target
    while parents[current] is not None:
        current = parents[current]  # type: ignore[index]
        path.append(current)
    path.reverse()
    return path


def _choose_join_witness(ars, left: str, right: str) -> dict[str, Any] | None:
    left_dist = _distance_map(ars, left)
    right_dist = _distance_map(ars, right)
    common = sorted(set(left_dist) & set(right_dist))
    if not common:
        return None

    best_total = min(left_dist[w] + right_dist[w] for w in common)
    candidates = [w for w in common if left_dist[w] + right_dist[w] == best_total]
    witness = sorted(candidates)[0]
    left_path = _shortest_path_states(ars, left, witness)
    right_path = _shortest_path_states(ars, right, witness)
    return {
        "state": witness,
        "left_path_states": left_path,
        "right_path_states": right_path,
        "total_distance": best_total,
    }


def _graph_dot(
    *,
    graph_name: str,
    states: list[str],
    edges: list[tuple[str, str]],
    start_nodes: set[str],
    normal_forms: set[str],
) -> str:
    lines = [f"digraph {graph_name} {{", "  rankdir=LR;"]
    for state in states:
        attrs = ["shape=ellipse"]
        if state in normal_forms:
            attrs = ["shape=doublecircle"]
        if state in start_nodes:
            attrs.append('style="filled,bold"')
            attrs.append('fillcolor="#e8f0fe"')
        lines.append(f"  {_q(state)} [{', '.join(attrs)}];")
    for src, dst in edges:
        lines.append(f"  {_q(src)} -> {_q(dst)};")
    lines.append("}")
    lines.append("")
    return "\n".join(lines)


def _focus_dot(
    *,
    graph_name: str,
    source: str,
    left: str,
    right: str,
    witness: dict[str, Any] | None,
    status: str,
) -> str:
    nodes = sorted({source, left, right} | ({witness["state"]} if witness else set()))
    lines = [f"digraph {graph_name} {{", "  rankdir=LR;"]

    for node in nodes:
        attrs = ["shape=ellipse"]
        if node == source:
            attrs.append('style="filled,bold"')
            attrs.append('fillcolor="#fff3cd"')
        elif node in (left, right):
            attrs.append('style="filled"')
            attrs.append('fillcolor="#fde2e2"' if status == "defective" else 'fillcolor="#e7f5e8"')
        elif witness and node == witness["state"]:
            attrs.append('style="filled,bold"')
            attrs.append('fillcolor="#d6f5d6"')
            attrs[0] = "shape=doublecircle"
        lines.append(f"  {_q(node)} [{', '.join(attrs)}];")

    lines.append(f"  {_q(source)} -> {_q(left)} [penwidth=2];")
    lines.append(f"  {_q(source)} -> {_q(right)} [penwidth=2];")

    if witness:
        left_path = witness["left_path_states"]
        right_path = witness["right_path_states"]
        for path in (left_path, right_path):
            for src, dst in zip(path, path[1:]):
                lines.append(f"  {_q(src)} -> {_q(dst)} [color=green, penwidth=2];")
    else:
        lines.append(f"  {_q(left)} -> {_q(left)} [style=dashed, color=red, label=defect];")
        lines.append(f"  {_q(right)} -> {_q(right)} [style=dashed, color=red, label=defect];")

    lines.append("}")
    lines.append("")
    return "\n".join(lines)


def _render_dot(dot_exec: str | None, dot_path: Path, svg_path: Path, png_path: Path) -> tuple[str | None, str | None, str]:
    if not dot_exec:
        return None, None, "dot_only"

    svg_ok = False
    png_ok = False
    try:
        subprocess.run([dot_exec, "-Tsvg", str(dot_path), "-o", str(svg_path)], check=True)
        svg_ok = True
    except Exception:
        svg_ok = False

    try:
        subprocess.run([dot_exec, "-Tpng", str(dot_path), "-o", str(png_path)], check=True)
        png_ok = True
    except Exception:
        png_ok = False

    if svg_ok and png_ok:
        return _display_path(svg_path), _display_path(png_path), "svg_png"
    if svg_ok:
        return _display_path(svg_path), None, "svg_only"
    if png_ok:
        return None, _display_path(png_path), "png_only"
    return None, None, "dot_only"


def _finite_ars_state(example_id: str) -> tuple[list[str], list[tuple[str, str]], set[str], set[str], Any]:
    ars = load_finite_ars(ROOT / "data" / "examples" / f"{example_id}.yaml")
    states = list(ars.states)
    edges = list(ars.edges)
    indegree = {state: 0 for state in states}
    for src, dst in edges:
        _ = src
        indegree[dst] += 1
    starts = {state for state in states if indegree[state] == 0}
    if not starts:
        starts = {states[0]}
    normal_forms = set(ars.normal_forms())
    return states, edges, starts, normal_forms, ars


def _string_state(example_id: str) -> tuple[list[str], list[tuple[str, str]], set[str], set[str], Any, dict[str, Any], Any]:
    example, system = load_string_rewrite_system(ROOT / "data" / "examples" / f"{example_id}.yaml")
    bounds = example["bounds"]
    exploration = system.explore_bounded(
        start_strings=example["start_strings"],
        max_depth=bounds["max_depth"],
        max_states=bounds["max_states"],
        max_word_length=bounds.get("max_word_length"),
    )
    ars = finite_ars_from_exploration(exploration)
    states = list(exploration["states"])
    edges = list(exploration["edges"])
    starts = set(exploration["start_strings"])
    normal_forms = set(ars.normal_forms())
    return states, edges, starts, normal_forms, ars, example, system


def build_diagram_manifest(output_root: Path | str | None = None, dot_executable: str | None = None) -> dict[str, Any]:
    out_root = Path(output_root) if output_root is not None else DEFAULT_OUT_DIR
    dot_exec = dot_executable if dot_executable is not None else shutil.which("dot")

    plans: list[dict[str, Any]] = []

    # E001 reduction graph + join diamond
    states, edges, starts, normal_forms, ars = _finite_ars_state("E001_diamond_flat")
    plans.append(
        {
            "example_id": "E001_diamond_flat",
            "domain": "finite_ars",
            "diagram_kind": "reduction_graph",
            "feature_status": "full_graph",
            "focus_source": None,
            "focus_branches": None,
            "focus_witness": None,
            "critical_pair_id": None,
            "dot": _graph_dot(
                graph_name="E001_reduction_graph",
                states=states,
                edges=edges,
                start_nodes=starts,
                normal_forms=normal_forms,
            ),
        }
    )
    e001_plaq = build_plaquette_artifact("E001_diamond_flat", ars)["plaquettes"][0]
    plans.append(
        {
            "example_id": "E001_diamond_flat",
            "domain": "finite_ars",
            "diagram_kind": "join_diamond",
            "feature_status": "joinable",
            "focus_source": e001_plaq["source"],
            "focus_branches": [e001_plaq["left_branch_edge"][1], e001_plaq["right_branch_edge"][1]],
            "focus_witness": e001_plaq["join_witness"]["state"],
            "critical_pair_id": None,
            "dot": _focus_dot(
                graph_name="E001_join_diamond",
                source=e001_plaq["source"],
                left=e001_plaq["left_branch_edge"][1],
                right=e001_plaq["right_branch_edge"][1],
                witness=e001_plaq["join_witness"],
                status="joinable",
            ),
        }
    )

    # E002 reduction graph + defective plaquette
    states, edges, starts, normal_forms, ars = _finite_ars_state("E002_fork_curved")
    plans.append(
        {
            "example_id": "E002_fork_curved",
            "domain": "finite_ars",
            "diagram_kind": "reduction_graph",
            "feature_status": "full_graph",
            "focus_source": None,
            "focus_branches": None,
            "focus_witness": None,
            "critical_pair_id": None,
            "dot": _graph_dot(
                graph_name="E002_reduction_graph",
                states=states,
                edges=edges,
                start_nodes=starts,
                normal_forms=normal_forms,
            ),
        }
    )
    e002_def = [p for p in build_plaquette_artifact("E002_fork_curved", ars)["plaquettes"] if p["status"] == "defective"][0]
    plans.append(
        {
            "example_id": "E002_fork_curved",
            "domain": "finite_ars",
            "diagram_kind": "defective_plaquette",
            "feature_status": "defective",
            "focus_source": e002_def["source"],
            "focus_branches": [e002_def["left_branch_edge"][1], e002_def["right_branch_edge"][1]],
            "focus_witness": None,
            "critical_pair_id": None,
            "dot": _focus_dot(
                graph_name="E002_defective_plaquette",
                source=e002_def["source"],
                left=e002_def["left_branch_edge"][1],
                right=e002_def["right_branch_edge"][1],
                witness=None,
                status="defective",
            ),
        }
    )

    # E003 join diamond
    _, _, _, _, ars = _finite_ars_state("E003_delayed_join_flat")
    e003_join = [p for p in build_plaquette_artifact("E003_delayed_join_flat", ars)["plaquettes"] if p["status"] == "joinable"][0]
    plans.append(
        {
            "example_id": "E003_delayed_join_flat",
            "domain": "finite_ars",
            "diagram_kind": "join_diamond",
            "feature_status": "joinable",
            "focus_source": e003_join["source"],
            "focus_branches": [e003_join["left_branch_edge"][1], e003_join["right_branch_edge"][1]],
            "focus_witness": e003_join["join_witness"]["state"],
            "critical_pair_id": None,
            "dot": _focus_dot(
                graph_name="E003_join_diamond",
                source=e003_join["source"],
                left=e003_join["left_branch_edge"][1],
                right=e003_join["right_branch_edge"][1],
                witness=e003_join["join_witness"],
                status="joinable",
            ),
        }
    )

    # E006 explored reduction graph + critical-pair focus
    states, edges, starts, normal_forms, ars, example, system = _string_state("E006_string_overlap_nonconfluent")
    plans.append(
        {
            "example_id": "E006_string_overlap_nonconfluent",
            "domain": "string_rewrite",
            "diagram_kind": "explored_reduction_graph",
            "feature_status": "full_graph",
            "focus_source": None,
            "focus_branches": None,
            "focus_witness": None,
            "critical_pair_id": None,
            "dot": _graph_dot(
                graph_name="E006_explored_reduction_graph",
                states=states,
                edges=edges,
                start_nodes=starts,
                normal_forms=normal_forms,
            ),
        }
    )
    cp_art = build_critical_pair_artifact("E006_string_overlap_nonconfluent", example, system)
    candidates = [cp for cp in cp_art["critical_pairs"] if cp["source_reachable_from_example_starts"]] or cp_art["critical_pairs"]
    cp = sorted(candidates, key=lambda item: item["critical_pair_id"])[0]
    witness = _choose_join_witness(ars, cp["left_branch_term"], cp["right_branch_term"]) if cp["joinable"] else None
    plans.append(
        {
            "example_id": "E006_string_overlap_nonconfluent",
            "domain": "string_rewrite",
            "diagram_kind": "critical_pair_focus",
            "feature_status": "joinable" if cp["joinable"] else "defective",
            "focus_source": cp["source_word"],
            "focus_branches": [cp["left_branch_term"], cp["right_branch_term"]],
            "focus_witness": witness["state"] if witness else None,
            "critical_pair_id": cp["critical_pair_id"],
            "dot": _focus_dot(
                graph_name="E006_critical_pair_focus",
                source=cp["source_word"],
                left=cp["left_branch_term"],
                right=cp["right_branch_term"],
                witness=witness,
                status="joinable" if cp["joinable"] else "defective",
            ),
        }
    )

    # E007 / E008 critical-pair focus
    for eid in ("E007_completion_before", "E008_completion_after"):
        states, edges, starts, normal_forms, ars, example, system = _string_state(eid)
        _ = (states, edges, starts, normal_forms)
        cp_art = build_critical_pair_artifact(eid, example, system)
        candidates = [cp for cp in cp_art["critical_pairs"] if cp["source_reachable_from_example_starts"]] or cp_art["critical_pairs"]
        cp = sorted(candidates, key=lambda item: item["critical_pair_id"])[0]
        witness = _choose_join_witness(ars, cp["left_branch_term"], cp["right_branch_term"]) if cp["joinable"] else None
        plans.append(
            {
                "example_id": eid,
                "domain": "string_rewrite",
                "diagram_kind": "critical_pair_focus",
                "feature_status": "joinable" if cp["joinable"] else "defective",
                "focus_source": cp["source_word"],
                "focus_branches": [cp["left_branch_term"], cp["right_branch_term"]],
                "focus_witness": witness["state"] if witness else None,
                "critical_pair_id": cp["critical_pair_id"],
                "dot": _focus_dot(
                    graph_name=f"{eid}_critical_pair_focus",
                    source=cp["source_word"],
                    left=cp["left_branch_term"],
                    right=cp["right_branch_term"],
                    witness=witness,
                    status="joinable" if cp["joinable"] else "defective",
                ),
            }
        )

    diagrams: list[dict[str, Any]] = []
    for idx, plan in enumerate(plans, start=1):
        example_id = plan["example_id"]
        diagram_kind = plan["diagram_kind"]
        ex_dir = out_root / example_id
        dot_path = ex_dir / f"{diagram_kind}.dot"
        svg_path = ex_dir / f"{diagram_kind}.svg"
        png_path = ex_dir / f"{diagram_kind}.png"

        diagrams.append(
            {
                "diagram_id": f"D{idx:04d}",
                "example_id": example_id,
                "domain": plan["domain"],
                "diagram_kind": diagram_kind,
                "feature_status": plan["feature_status"],
                "focus_source": plan["focus_source"],
                "focus_branches": plan["focus_branches"],
                "focus_witness": plan["focus_witness"],
                "critical_pair_id": plan["critical_pair_id"],
                "dot_path": _display_path(dot_path),
                "svg_path": None,
                "png_path": None,
                "render_status": "dot_only",
                "_dot_text": plan["dot"],
            }
        )

    return {
        "schema_version": 1,
        "kind": "diagram_asset_index",
        "graphviz_dot_available": bool(dot_exec),
        "dot_executable": dot_exec,
        "output_root": str(out_root),
        "diagrams": diagrams,
    }


def write_diagram_assets(output_root: Path | str | None = None, dot_executable: str | None = None) -> dict[str, Any]:
    manifest = build_diagram_manifest(output_root=output_root, dot_executable=dot_executable)
    out_root = Path(manifest["output_root"])
    dot_exec = manifest.get("dot_executable")

    for entry in manifest["diagrams"]:
        dot_text = entry.pop("_dot_text")
        dot_path = ROOT / entry["dot_path"] if not Path(entry["dot_path"]).is_absolute() else Path(entry["dot_path"])
        dot_path.parent.mkdir(parents=True, exist_ok=True)
        dot_path.write_text(dot_text, encoding="utf-8")

        svg_path = dot_path.with_suffix(".svg")
        png_path = dot_path.with_suffix(".png")
        svg_out, png_out, status = _render_dot(dot_exec, dot_path, svg_path, png_path)
        entry["svg_path"] = svg_out
        entry["png_path"] = png_out
        entry["render_status"] = status

    index_path = out_root / "index.json"
    index_path.write_text(
        json.dumps(
            {
                "schema_version": manifest["schema_version"],
                "kind": manifest["kind"],
                "graphviz_dot_available": manifest["graphviz_dot_available"],
                "diagrams": manifest["diagrams"],
            },
            indent=2,
            sort_keys=True,
        )
        + "\n",
        encoding="utf-8",
    )
    return {
        "schema_version": manifest["schema_version"],
        "kind": manifest["kind"],
        "graphviz_dot_available": manifest["graphviz_dot_available"],
        "diagrams": manifest["diagrams"],
        "index_path": _display_path(index_path),
    }
