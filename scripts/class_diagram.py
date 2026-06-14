#!/usr/bin/env python3
"""Regenerate README.assets/class-hierarchy.png from the Design doc's diagram.

The styled Graphviz source (coloured roots, dashed mixins) lives once in
``docs/source/design.rst`` so the docs and the README stay in sync. This
extracts that ``digraph`` block and renders it with ``dot``. Invoke via
``make class-diagram``.

Requires the Graphviz ``dot`` binary on PATH (``brew install graphviz``).
The underlying edges come from ``python -m mytk -c``; if you add classes,
update the diagram in design.rst, then run this.
"""
import os
import shutil
import subprocess
import sys

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DESIGN = os.path.join(REPO, "docs", "source", "design.rst")
OUT = os.path.join(REPO, "README.assets", "class-hierarchy.png")
DPI = "140"


def main() -> int:
    if shutil.which("dot") is None:
        sys.exit("Graphviz `dot` not found on PATH (try: brew install graphviz).")

    text = open(DESIGN).read()
    start = text.index("digraph myTk")
    end = text.index("}\n", start) + 1
    dot_src = text[start:end]

    proc = subprocess.run(
        ["dot", "-Tpng", f"-Gdpi={DPI}", "-o", OUT],
        input=dot_src.encode(),
    )
    if proc.returncode != 0:
        sys.exit(f"dot failed (rc={proc.returncode}).")
    size = os.path.getsize(OUT)
    print(f"Wrote {OUT} ({size // 1024} KB)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
