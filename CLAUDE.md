# CLAUDE.md

Guidance for AI coding agents (and humans) working **on** the myTk repository.

myTk is a Tkinter wrapper for scientists. This file documents how we *develop,
test, release, and document* the project. For how to *use* the library's API
(property bindings, `NotificationCenter`, widgets), do **not** duplicate it
here — read the agent skill at
[`.claude/skills/mytk/SKILL.md`](.claude/skills/mytk/SKILL.md). Keep API usage
guidance in the skill; keep development/process guidance in this file.

## Single source of truth

Each kind of knowledge has exactly one home; the others point to it rather than
copy:

- **How to use the mytk API** → `.claude/skills/mytk/SKILL.md` (the skill).
- **How to develop this repo** → this `CLAUDE.md`.
- The skill is shipped twice on purpose — the repo copy
  (`.claude/skills/mytk/SKILL.md`, auto-discovered in clones) and the packaged
  copy (`mytk/resources/skills/mytk/SKILL.md`, bundled in the wheel for
  `pip install mytk` users). They are kept **byte-identical** by
  `mytk/tests/testSkill.py`. If you edit one, edit the other (the test fails
  otherwise).

## Layout

- `mytk/` — the package. Widgets subclass `Base`; `App` is the application root.
- `mytk/tests/` — unittest suite, camelCase files (`test*.py`).
- `mytk/example_apps/` — runnable examples (`python -m mytk`).
- `mytk/resources/` — packaged data (icons, the bundled skill).
- `docs/source/` — Sphinx documentation sources.
- `scripts/` — dev helpers invoked by the `Makefile`.
- `.github/workflows/` — CI: `tests.yml` and `release.yml`.

## Development environment

- Python **>= 3.11** (CI covers 3.11–3.14).
- Prefer the project venv if present: `.venv/bin/python`. The `Makefile` auto-
  selects it.
- Editable install: `pip install -e .` (extras: `.[view3d]`, `.[video]`,
  `.[dnd]`, `.[svg]`, `.[optics]`, `.[docs]`, or `.[all]`).
- Runtime deps live in `requirements.txt` (wired into `pyproject.toml` via
  `[tool.setuptools.dynamic]`); platform-sensitive features are extras in
  `pyproject.toml`, imported lazily on first use.

## Testing

- Local: from `mytk/tests/`, run
  `python -m unittest discover -p "test*.py"`
  (or from the repo root: `python -m unittest discover -s mytk/tests`).
- GUI note: tests use Tk. On Linux a virtual display is required
  (`xvfb-run -a ...`); macOS/Windows have one. Some event-loop tests run a real
  `mainloop()` with a timed `app.quit()`.
- Always run the suite before tagging a release.
- CI (`tests.yml`) runs the matrix **ubuntu/macos/windows × py3.11–3.14** on
  every push to `main` and every PR (macOS+3.11 is excluded — a Tk mainloop
  hang on that runner).

## Versioning & release (tag-driven, fully automated)

Versioning is handled by **setuptools-scm** — the version comes from the latest
git tag and is written to `mytk/_version.py`.

- **Never edit the version by hand** in `pyproject.toml` (it is `dynamic`).
- To cut a release, **create and push an annotated tag** `vX.Y.Z`:
  ```sh
  git tag -a v1.5.0 -m "v1.5.0: <summary>"
  git push origin v1.5.0
  ```
- Pushing a `v*` tag triggers `release.yml`, which **builds sdist+wheel →
  `twine check` → publishes to PyPI → creates a GitHub Release** with the
  artifacts and generated notes. No manual `build`/`twine upload` step is
  needed.
- PyPI auth is the `PYPI_API_TOKEN` repo secret (Settings → Secrets and
  variables → Actions).
- Choose the bump semantically: new feature → minor (`x.Y.0`), fix → patch
  (`x.y.Z`). Tag from a clean `main` at the commit you want released.
- Published package: <https://pypi.org/project/mytk/>.

## Documentation (Sphinx + ReadTheDocs)

- Sources in `docs/source/` (`conf.py` uses autodoc, napoleon, autosummary,
  graphviz, myst-parser). The version shown comes from the installed package
  metadata.
- Build locally: `make docs` (→ `docs/build/html`).
- Hosted on **ReadTheDocs**, configured by `.readthedocs.yaml` (Python 3.12,
  installs `.[docs]`, needs the `graphviz` apt package). RTD rebuilds
  automatically on pushes to `main`/tags.
- Live docs: <https://mytk.readthedocs.io/>.
- Regenerate doc/README assets with the `Makefile` targets below (some need
  macOS Screen Recording permission and/or graphviz `dot`).

## Make targets

Run `make help` for the list. Notable:

- `make docs` — build HTML docs.
- `make readme-assets` — regenerate the README images (`class-diagram` +
  `screenshot`).
- `make example-shots` — screenshot each example app (macOS).
- `make examples-doc` — regenerate `docs/source/examples.rst` from the examples.

## Branch & PR workflow

- **Always branch** off `main` before making changes; never commit straight to
  `main`.
- Open a **PR** to `main`; CI (`tests.yml`) must pass.
- The maintainer usually reviews/merges PRs himself — ask before merging unless
  told otherwise. Do **not** auto-commit; let changes be reviewed first.
- After merge, the tag-driven release flow above handles publishing.

## Distributing the agent skill

- Repo clones: auto-discovered from `.claude/skills/`.
- pip users (opt in): `python -m mytk --install-skill` (into `~/.claude/skills/`)
  or `python -m mytk --install-skill --project` (into `./.claude/skills/`).
