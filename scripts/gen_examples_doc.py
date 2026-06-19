#!/usr/bin/env python3
"""Generate the "Example applications" docs page from the example apps.

Scans ``mytk/example_apps/*.py``, reads each module docstring (the single source
of truth for the description), and writes ``docs/source/examples.rst`` with, for
each app: a heading, the description, a screenshot (when one exists under
``docs/source/_static/examples/``) and the full source via ``literalinclude``.

It is run two ways:
  * automatically at Sphinx build time, from ``conf.py`` (so Read the Docs always
    rebuilds it), and
  * manually via ``make examples-doc`` / ``python scripts/gen_examples_doc.py``.
"""
import ast
import os
from pathlib import Path

EXCLUDE = {"__init__.py"}
# Show the comprehensive showcase first; the rest follow alphabetically.
FEATURED_FIRST = ["example.py"]

REPO = Path(__file__).resolve().parent.parent
DEFAULT_EXAMPLES_DIR = REPO / "mytk" / "example_apps"
DEFAULT_OUTPUT = REPO / "docs" / "source" / "examples.rst"
DEFAULT_IMAGE_ABS = REPO / "docs" / "source" / "_static" / "examples"
IMAGE_REL = "/_static/examples"


def _docstring(path):
    return ast.get_docstring(ast.parse(path.read_text(encoding="utf-8")))


def _sorted_examples(examples_dir):
    files = [p for p in examples_dir.glob("*.py") if p.name not in EXCLUDE]
    order = {name: i for i, name in enumerate(FEATURED_FIRST)}
    return sorted(files, key=lambda p: (order.get(p.name, len(order)), p.name))


def generate(output_path=DEFAULT_OUTPUT, examples_dir=DEFAULT_EXAMPLES_DIR,
             image_dir_abs=DEFAULT_IMAGE_ABS):
    """Write ``examples.rst`` and return the list of example filenames included."""
    examples_dir = Path(examples_dir)
    image_dir_abs = Path(image_dir_abs)
    files = _sorted_examples(examples_dir)

    out = []
    title = "Example applications"
    out += [
        ".. _examples:",
        "",
        title,
        "=" * len(title),
        "",
        "myTk ships a set of runnable example apps in ``mytk/example_apps/``.",
        "Launch any of them as a module, for example::",
        "",
        "    python -m mytk.example_apps.example",
        "",
        "Each section shows what the example demonstrates, a screenshot and its",
        "full source.",
        "",
    ]

    for path in files:
        name = path.name
        doc = (_docstring(path) or name).strip()
        doc_lines = doc.splitlines()
        first = doc_lines[0]
        summary = first.split("—", 1)[1].strip() if "—" in first else first
        body = "\n".join(doc_lines[1:]).strip()

        out += [name, "-" * len(name), "", f"**{summary}**", ""]
        if body:
            out += [body, ""]
        out += [f"Run it with ``python -m mytk.example_apps.{path.stem}``.", ""]

        image = image_dir_abs / f"{path.stem}.png"
        if image.exists():
            out += [
                f".. image:: {IMAGE_REL}/{path.stem}.png",
                f"   :alt: {name} screenshot",
                "   :width: 100%",
                "",
            ]
        else:
            out += [
                ".. note::",
                "   Screenshot not yet available — regenerate with "
                "``make example-shots``.",
                "",
            ]

        out += [
            f".. literalinclude:: ../../mytk/example_apps/{name}",
            "   :language: python",
            "   :linenos:",
            "",
        ]

    Path(output_path).write_text("\n".join(out) + "\n", encoding="utf-8")
    return [p.name for p in files]


if __name__ == "__main__":
    names = generate()
    print(f"Wrote {DEFAULT_OUTPUT} ({len(names)} examples)")
