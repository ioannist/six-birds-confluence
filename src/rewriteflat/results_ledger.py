"""Central results ledger builder for generated artifacts under results/."""

from __future__ import annotations

import csv
import hashlib
import json
import re
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

REQUIRED_COLLECTIONS = [
    "exhaustive_ars_audits",
    "boundary_counterexamples",
    "string_examples",
    "critical_pair_audits",
    "completion_case_study",
    "figures",
    "term_rewrite_examples",
    "two_complex_artifacts",
]

_DEFAULT_EXCLUDED_PATHS = [
    "results/index.json",
    "results/summary.csv",
    "results/.gitkeep",
]

_EXAMPLE_ID_RE = re.compile(r"(E\d{3}_[A-Za-z0-9_]+)")
_CASE_ID_RE = re.compile(r"(CS\d{3}_[A-Za-z0-9_]+)")


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


def _ts_iso(dt: datetime) -> str:
    return dt.strftime("%Y-%m-%dT%H:%M:%SZ")


def _run_id(dt: datetime) -> str:
    return "results_ledger_" + dt.strftime("%Y%m%dT%H%M%SZ")


def _normalize_path(path: str | Path) -> str:
    return Path(path).as_posix()


def _stable_artifact_id(relative_path: str) -> str:
    sanitized = re.sub(r"[^A-Za-z0-9]+", "_", relative_path).strip("_").upper()
    return f"ART_{sanitized}"


def _sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def _collection_for_path(relative_path: str) -> str:
    rel = relative_path
    if rel.startswith("results/audits/exhaustive_finite_ars_"):
        return "exhaustive_ars_audits"
    if rel.startswith("results/audits/boundary_counterexample_"):
        return "boundary_counterexamples"
    if rel.startswith("results/audits/critical_pair_curvature_audit"):
        return "critical_pair_audits"
    if rel.startswith("results/audits/naive_graph_flatness_audit"):
        return "naive_graph_audit"
    if rel.startswith("results/string_rewrite/"):
        return "string_examples"
    if rel.startswith("results/critical_pairs/"):
        return "critical_pair_analysis"
    if rel.startswith("results/case_studies/"):
        return "completion_case_study"
    if rel.startswith("results/diagrams/"):
        return "figures"
    if rel.startswith("results/term_rewrite/"):
        return "term_rewrite_examples"
    if rel.startswith("results/two_complex/"):
        return "two_complex_artifacts"
    if rel.startswith("results/freeze/"):
        return "freeze_artifacts"
    if rel.startswith("results/peaks/"):
        return "peak_artifacts"
    if rel.startswith("results/plaquettes/"):
        return "plaquette_artifacts"
    return "other"


def _infer_kind(path: Path, ext: str) -> tuple[str, dict[str, Any] | None]:
    if ext == "json":
        try:
            payload = json.loads(path.read_text(encoding="utf-8"))
            if isinstance(payload, dict):
                kind = payload.get("kind")
                if isinstance(kind, str) and kind:
                    return kind, payload
                return "json_document", payload
        except Exception:
            return "json_document", None
        return "json_document", None
    if ext == "csv":
        return "csv_table", None
    if ext == "dot":
        return "graphviz_dot", None
    if ext == "svg":
        return "svg_figure", None
    if ext == "png":
        return "png_figure", None
    return f"file_{ext}" if ext else "file"


def _extract_ids(relative_path: str, payload: dict[str, Any] | None) -> tuple[str | None, str | None]:
    example_id: str | None = None
    case_id: str | None = None

    if isinstance(payload, dict):
        ex = payload.get("example_id")
        cs = payload.get("case_id")
        if isinstance(ex, str) and ex:
            example_id = ex
        if isinstance(cs, str) and cs:
            case_id = cs

    if example_id is None:
        m = _EXAMPLE_ID_RE.search(relative_path)
        if m:
            example_id = m.group(1)
    if case_id is None:
        m = _CASE_ID_RE.search(relative_path)
        if m:
            case_id = m.group(1)

    return example_id, case_id


def scan_results_artifacts(root: str = "results") -> list[dict[str, Any]]:
    repo_root = Path(__file__).resolve().parents[2]
    root_path = (repo_root / root).resolve()
    excluded_paths = {_normalize_path(p) for p in _DEFAULT_EXCLUDED_PATHS}

    files: list[Path] = []
    if root_path.exists():
        for path in root_path.rglob("*"):
            if path.is_file():
                rel = _normalize_path(path.relative_to(repo_root))
                if rel in excluded_paths:
                    continue
                files.append(path)

    files.sort(key=lambda p: _normalize_path(p.relative_to(repo_root)))

    now = _utc_now()
    ts = _ts_iso(now)
    rid = _run_id(now)

    artifacts: list[dict[str, Any]] = []
    for path in files:
        rel = _normalize_path(path.relative_to(repo_root))
        ext = path.suffix.lower().lstrip(".")
        kind, payload = _infer_kind(path, ext)
        if isinstance(kind, tuple):
            kind, payload = kind  # defensive; not used
        example_id, case_id = _extract_ids(rel, payload)
        artifacts.append(
            {
                "artifact_id": _stable_artifact_id(rel),
                "relative_path": rel,
                "collection": _collection_for_path(rel),
                "kind": kind,
                "file_ext": ext,
                "size_bytes": path.stat().st_size,
                "sha256": _sha256(path),
                "example_id": example_id,
                "case_id": case_id,
                "run_id": rid,
                "indexed_at_utc": ts,
            }
        )

    return artifacts


def build_results_ledger(root: str = "results") -> dict[str, Any]:
    artifacts = scan_results_artifacts(root=root)
    counts = Counter(a["collection"] for a in artifacts)
    collection_counts = {k: counts[k] for k in sorted(counts)}
    missing_required = [c for c in REQUIRED_COLLECTIONS if counts.get(c, 0) == 0]

    generated_at = artifacts[0]["indexed_at_utc"] if artifacts else _ts_iso(_utc_now())
    run_id = artifacts[0]["run_id"] if artifacts else _run_id(_utc_now())

    return {
        "schema_version": 1,
        "kind": "results_ledger",
        "generated_at_utc": generated_at,
        "run_id": run_id,
        "root": root,
        "excluded_paths": list(_DEFAULT_EXCLUDED_PATHS),
        "required_collections": list(REQUIRED_COLLECTIONS),
        "missing_required_collections": missing_required,
        "artifact_count": len(artifacts),
        "collection_counts": collection_counts,
        "artifacts": artifacts,
    }


def write_results_ledger(root: str = "results") -> dict[str, Any]:
    repo_root = Path(__file__).resolve().parents[2]
    root_path = (repo_root / root).resolve()
    root_path.mkdir(parents=True, exist_ok=True)

    ledger = build_results_ledger(root=root)

    index_path = root_path / "index.json"
    summary_path = root_path / "summary.csv"

    index_path.write_text(json.dumps(ledger, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    fields = [
        "artifact_id",
        "relative_path",
        "collection",
        "kind",
        "file_ext",
        "example_id",
        "case_id",
        "size_bytes",
        "sha256",
        "run_id",
        "indexed_at_utc",
    ]

    with summary_path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        for artifact in ledger["artifacts"]:
            writer.writerow({field: artifact.get(field) for field in fields})

    return ledger
