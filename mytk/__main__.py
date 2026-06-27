import argparse
import importlib.resources as resources
import shutil
import subprocess
import sys
from pathlib import Path

from mytk import Bindable

SKILL_RESOURCE = "skills/mytk/SKILL.md"


def install_skill(scope="user"):
    """Copy the bundled mytk agent skill into a Claude Code skills directory.

    The skill ships as package data so it is available after ``pip install
    mytk``; this installs it where Claude Code can discover it. ``scope="user"``
    targets ``~/.claude/skills/mytk/`` (available everywhere); ``scope="project"``
    targets ``./.claude/skills/mytk/`` (the current directory only).
    """
    source = resources.files("mytk.resources").joinpath(SKILL_RESOURCE)
    if not source.is_file():
        print(f"Could not find the bundled skill at {SKILL_RESOURCE}.", file=sys.stderr)
        return 1

    base = Path.home() if scope == "user" else Path.cwd()
    destination = base / ".claude" / "skills" / "mytk" / "SKILL.md"
    destination.parent.mkdir(parents=True, exist_ok=True)

    with resources.as_file(source) as source_path:
        shutil.copyfile(source_path, destination)

    print(f"Installed mytk skill to {destination}")
    print("Claude Code will discover it from this .claude/skills/ directory.")
    return 0


def printClassHierarchy(aClass):  # noqa: N802, N803
    """Print the class hierarchy in Graphviz DOT format."""
    def printAllChilds(aClass):  # noqa: N802, N803
        for child in aClass.__subclasses__():
            print('"{0}" -> "{1}"'.format(aClass.__name__, child.__name__))
            printAllChilds(child)

    print("# Paste this in the text field of http://www.webgraphviz.com/")
    print("digraph G {")
    print('  rankdir="LR";')
    printAllChilds(aClass)
    print("}")


def main():
    """Run the mytk command-line interface for examples, tests, and class inspection."""
    root = Path(__file__).parent
    examples_dir = root / "example_apps"
    examples = [
        f.name
        for f in sorted(examples_dir.iterdir())
        if f.suffix == ".py" and not f.name.startswith("__")
    ]

    ap = argparse.ArgumentParser(prog="python -m mytk")
    ap.add_argument(
        "-e",
        "--examples",
        required=False,
        default="all",
        help="Specific example numbers, separated by a comma",
    )
    ap.add_argument(
        "-c",
        "--classes",
        required=False,
        action="store_const",
        const=True,
        help="Print the class hierarchy in graphviz format",
    )
    ap.add_argument(
        "-l",
        "--list",
        required=False,
        action="store_const",
        const=True,
        help="List all the accessible examples",
    )
    ap.add_argument(
        "-t",
        "--tests",
        required=False,
        action="store_const",
        const=True,
        help="Run all Unit tests",
    )
    ap.add_argument(
        "--install-skill",
        required=False,
        action="store_const",
        const=True,
        help="Install the bundled mytk agent skill into a Claude Code skills directory",
    )
    ap.add_argument(
        "--project",
        required=False,
        action="store_const",
        const=True,
        help="With --install-skill, install into ./.claude/ instead of ~/.claude/",
    )

    args = vars(ap.parse_args())
    runExamples = args["examples"]  # noqa: N806
    runTests = args["tests"]  # noqa: N806
    printClasses = args["classes"]  # noqa: N806
    listExamples = args["list"]  # noqa: N806
    installSkill = args["install_skill"]  # noqa: N806
    skillScope = "project" if args["project"] else "user"  # noqa: N806

    if installSkill:
        sys.exit(install_skill(scope=skillScope))

    if runExamples == "all":
        runExamples = range(1, len(examples) + 1)  # noqa: N806
    elif runExamples == "":
        runExamples = []  # noqa: N806
    else:
        runExamples = [int(y) for y in runExamples.split(",")]  # noqa: N806

    if printClasses:
        printClassHierarchy(Bindable)

    elif runTests:
        tests_dir = Path(__file__).resolve().parent / "tests"
        result = subprocess.run(
            [sys.executable, "-m", "unittest"],
            cwd=tests_dir,
        )
        sys.exit(result.returncode)

    elif listExamples:
        for i, app in enumerate(sorted(examples)):
            print(f"{i+1:2d}. {app}")

    elif runExamples:
        for i in runExamples:
            entry = examples[i - 1]
            filepath = examples_dir / entry
            title = f"# mytk example file: {filepath}"

            print("\n\n\n")
            print("#" * len(title))
            print(title)
            print("#" * len(title))
            print("\n")

            with open(filepath, "r") as file:
                print(file.read())

            subprocess.run([sys.executable, str(examples_dir / entry)])


if __name__ == "__main__":
    main()
