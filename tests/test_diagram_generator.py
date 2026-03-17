import json
from pathlib import Path

from rewriteflat.diagram_generator import build_diagram_manifest, write_diagram_assets


REQUIRED_EXAMPLES = {
    "E001_diamond_flat",
    "E002_fork_curved",
    "E003_delayed_join_flat",
    "E006_string_overlap_nonconfluent",
    "E007_completion_before",
    "E008_completion_after",
}


def _by_key(diagrams: list[dict]) -> dict[tuple[str, str], dict]:
    return {(d["example_id"], d["diagram_kind"]): d for d in diagrams}


def test_manifest_structure_is_json_serializable(tmp_path):
    manifest = write_diagram_assets(output_root=tmp_path)
    assert manifest["schema_version"] == 1
    assert manifest["kind"] == "diagram_asset_index"
    assert "graphviz_dot_available" in manifest
    assert "diagrams" in manifest
    json.dumps(manifest, sort_keys=True)


def test_required_examples_are_covered(tmp_path):
    manifest = write_diagram_assets(output_root=tmp_path)
    examples = {entry["example_id"] for entry in manifest["diagrams"]}
    assert REQUIRED_EXAMPLES.issubset(examples)


def test_required_diagram_kinds_exist(tmp_path):
    manifest = write_diagram_assets(output_root=tmp_path)
    keyed = _by_key(manifest["diagrams"])

    assert ("E001_diamond_flat", "reduction_graph") in keyed
    assert ("E001_diamond_flat", "join_diamond") in keyed
    assert ("E002_fork_curved", "defective_plaquette") in keyed
    assert ("E006_string_overlap_nonconfluent", "critical_pair_focus") in keyed
    assert ("E007_completion_before", "critical_pair_focus") in keyed
    assert ("E008_completion_after", "critical_pair_focus") in keyed


def test_dot_files_exist_and_nonempty(tmp_path):
    manifest = write_diagram_assets(output_root=tmp_path)
    for entry in manifest["diagrams"]:
        dot_path = Path(entry["dot_path"])
        assert dot_path.exists()
        text = dot_path.read_text(encoding="utf-8")
        assert text.strip()
        assert "digraph" in text


def test_focus_metadata_is_sensible(tmp_path):
    manifest = write_diagram_assets(output_root=tmp_path)
    keyed = _by_key(manifest["diagrams"])

    assert keyed[("E001_diamond_flat", "join_diamond")]["focus_witness"] == "D"
    assert keyed[("E003_delayed_join_flat", "join_diamond")]["focus_witness"] == "F"
    assert keyed[("E002_fork_curved", "defective_plaquette")]["feature_status"] == "defective"
    assert keyed[("E008_completion_after", "critical_pair_focus")]["feature_status"] == "joinable"


def test_rendering_fallback_behavior(tmp_path):
    manifest = write_diagram_assets(output_root=tmp_path)
    diagrams = manifest["diagrams"]
    if manifest["graphviz_dot_available"]:
        assert any(d["svg_path"] is not None or d["png_path"] is not None for d in diagrams)
    else:
        assert all(d["render_status"] == "dot_only" for d in diagrams)


def test_forced_dot_unavailable_still_generates_dot_assets(tmp_path):
    manifest = write_diagram_assets(output_root=tmp_path, dot_executable="")
    assert manifest["graphviz_dot_available"] is False
    assert all(d["render_status"] == "dot_only" for d in manifest["diagrams"])
    assert all(d["svg_path"] is None and d["png_path"] is None for d in manifest["diagrams"])


def test_index_file_written(tmp_path):
    manifest = write_diagram_assets(output_root=tmp_path)
    index_path = Path(manifest["index_path"])
    assert index_path.exists()
    data = json.loads(index_path.read_text(encoding="utf-8"))
    assert data["schema_version"] == 1
    assert data["kind"] == "diagram_asset_index"
    assert len(data["diagrams"]) == len(manifest["diagrams"])


def test_build_manifest_has_required_keys_without_writing():
    manifest = build_diagram_manifest()
    assert manifest["schema_version"] == 1
    assert manifest["kind"] == "diagram_asset_index"
    assert "graphviz_dot_available" in manifest
    assert "diagrams" in manifest
    assert manifest["diagrams"]
