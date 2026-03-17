#!/usr/bin/env python
"""Generate diagram DOT assets and optional Graphviz renders."""

from __future__ import annotations

from rewriteflat.diagram_generator import write_diagram_assets


def main() -> int:
    manifest = write_diagram_assets()
    diagrams = manifest["diagrams"]
    svg_count = sum(1 for d in diagrams if d["svg_path"] is not None)
    png_count = sum(1 for d in diagrams if d["png_path"] is not None)
    example_ids = sorted({d["example_id"] for d in diagrams})

    print(f"graphviz_dot_available={manifest['graphviz_dot_available']}")
    print(f"diagram_count={len(diagrams)}")
    print(f"svg_count={svg_count}")
    print(f"png_count={png_count}")
    print("examples=" + ",".join(example_ids))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
