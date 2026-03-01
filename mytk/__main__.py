import argparse
import os
import subprocess
import sys

from mytk import Bindable


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
    root = os.path.dirname(__file__)
    examples_dir = os.path.join(root, "example_apps")
    examples = [
        f
        for f in sorted(os.listdir(examples_dir))
        if f.endswith(".py") and not f.startswith("__")
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

    args = vars(ap.parse_args())
    runExamples = args["examples"]  # noqa: N806
    runTests = args["tests"]  # noqa: N806
    printClasses = args["classes"]  # noqa: N806
    listExamples = args["list"]  # noqa: N806

    if runExamples == "all":
        runExamples = range(1, len(examples) + 1)  # noqa: N806
    elif runExamples == "":
        runExamples = []  # noqa: N806
    else:
        runExamples = [int(y) for y in runExamples.split(",")]  # noqa: N806

    if printClasses:
        printClassHierarchy(Bindable)

    elif runTests:
        tests_dir = os.path.join(os.path.dirname(os.path.realpath(__file__)), "tests")
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
            filepath = os.path.join(examples_dir, entry)
            title = f"# mytk example file: {filepath}"

            print("\n\n\n")
            print("#" * len(title))
            print(title)
            print("#" * len(title))
            print("\n")

            with open(filepath, "r") as file:
                print(file.read())

            subprocess.run([sys.executable, os.path.join(examples_dir, entry)])


if __name__ == "__main__":
    main()
