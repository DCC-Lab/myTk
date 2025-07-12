import os
import sys
import argparse
import subprocess
from mytk import *

def printClassHierarchy(aClass):
    def printAllChilds(aClass):
        for child in aClass.__subclasses__():
            print("\"{0}\" -> \"{1}\"".format(aClass.__name__, child.__name__))
            printAllChilds(child)
    print("# Paste this in the text field of http://www.webgraphviz.com/")
    print("digraph G {")
    print("  rankdir=\"LR\";")
    printAllChilds(aClass)
    print("}")

root = os.path.dirname(__file__)
examples_dir = os.path.join(root, "example_apps")
examples = [ f for f in sorted(os.listdir(examples_dir)) if f.endswith('.py') and not f.startswith('__') ]

ap = argparse.ArgumentParser(prog='python -m mytk')
ap.add_argument("-e", "--examples", required=False, default='all',
                help="Specific example numbers, separated by a comma")
ap.add_argument("-c", "--classes", required=False, action='store_const',
                const=True, help="Print the class hierarchy in graphviz format")
ap.add_argument("-l", "--list", required=False, action='store_const',
                const=True, help="List all the accessible examples")
ap.add_argument("-t", "--tests", required=False, action='store_const',
                const=True, help="Run all Unit tests")

args = vars(ap.parse_args())
runExamples = args['examples']
runTests = args['tests']
printClasses = args['classes']
listExamples = args['list']

if runExamples == 'all':
    runExamples = range(1, len(examples)+1)
elif runExamples == '':
    runExamples = []
else:
    runExamples = [int(y) for y in runExamples.split(',')]

if printClasses:
    printClassHierarchy(Bindable)

elif runTests:
    moduleDir = os.path.dirname(os.path.realpath(__file__))
    err = os.system('cd {0}/tests; {1} -m unittest'.format(moduleDir, sys.executable))
elif listExamples:
	for i, app in enumerate(sorted(examples)):
		print(f"{i+1:2d}. {app}")
elif runExamples:
    for i in runExamples:
        entry = examples[i-1]

        filepath = os.path.join(examples_dir, entry)
        title = f"# mytk example file: {filepath}"

        print(f"\n\n\n")
        print("#"*len(title))
        print(title)
        print("#"*len(title))
        print(f"\n")

        with open(filepath, "r") as file:
            print(file.read())

        subprocess.run([sys.executable, os.path.join(examples_dir, entry)])

