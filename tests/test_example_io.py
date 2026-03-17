from pathlib import Path

import pytest

from rewriteflat.example_io import load_finite_ars
from rewriteflat.finite_ars import FiniteARS


ROOT = Path(__file__).resolve().parents[1]


def test_load_diamond_example():
    ars = load_finite_ars(ROOT / "data" / "examples" / "E001_diamond_flat.yaml")
    assert isinstance(ars, FiniteARS)
    assert ars.is_confluent()


def test_load_fork_example():
    ars = load_finite_ars(ROOT / "data" / "examples" / "E002_fork_curved.yaml")
    assert isinstance(ars, FiniteARS)
    assert not ars.is_confluent()


def test_invalid_edge_endpoint_is_rejected(tmp_path: Path):
    payload = """\
kind: finite_ars
id: bad_example
label: bad_example
states: [A, B]
edges:
  - [A, C]
"""
    path = tmp_path / "bad.yaml"
    path.write_text(payload, encoding="utf-8")

    with pytest.raises(ValueError, match="edge endpoint not declared"):
        load_finite_ars(path)
