# AGENTS.md

Instructions for AI coding agents. There are two situations; pick yours.

## You are writing code that uses mytk

myTk ships an agent skill: one Markdown file that describes the whole API (the `App` class, layout, every widget, dialogs, settings, tables, property bindings, notifications, remote control) and lists what myTk already does so that you do not re-code it with raw tkinter. **Read it before writing any mytk or tkinter code.**

Where it is:

- In a clone of this repository: [`.claude/skills/mytk/SKILL.md`](.claude/skills/mytk/SKILL.md). Claude Code discovers it automatically from there.
- After `pip install mytk`: bundled in the package at `mytk/resources/skills/mytk/SKILL.md`. Print its location with:

  ```sh
  python -c "from importlib import resources; print(resources.files('mytk.resources') / 'skills/mytk/SKILL.md')"
  ```

You may install it so that it is available in future sessions. It only copies that one file:

```sh
python -m mytk --install-skill            # into ~/.claude/skills/mytk/  (every project of this user)
python -m mytk --install-skill --project  # into ./.claude/skills/mytk/  (the current project only)
```

Prefer `--project` unless the user asked for a user-wide install: the first form writes into the user's home directory, so tell the user before doing it. An agent that does not use `.claude/skills/` can simply read the file at the location above; it is plain Markdown.

The skill is written for the version of mytk it ships with. If the installed package is older than the skill you are reading, trust the installed source code.

## You are working on the myTk repository itself

Read [`CLAUDE.md`](CLAUDE.md): layout, tests, branch and PR workflow, tag-driven releases, documentation. Two rules matter most:

- Always branch off `main` and open a PR; do not commit to `main` and do not merge without being asked.
- The skill exists in two copies that must stay byte-identical (`.claude/skills/mytk/SKILL.md` and `mytk/resources/skills/mytk/SKILL.md`); `mytk/tests/testSkill.py` fails otherwise. When you change the API, update the skill in the same PR.
