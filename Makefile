# myTk developer helpers. Run `make` (or `make help`) to list targets.

# Prefer the project venv if present, else the system python3.
PYTHON ?= $(shell [ -x .venv/bin/python ] && echo .venv/bin/python || echo python3)

.DEFAULT_GOAL := help
.PHONY: help screenshot class-diagram readme-assets example-shots examples-doc docs

help:  ## List available targets
	@echo "myTk make targets:"
	@echo "  make screenshot     Regenerate README.assets/example-ui.png from example.py (macOS)"
	@echo "  make class-diagram  Regenerate README.assets/class-hierarchy.png from docs/source/design.rst"
	@echo "  make readme-assets  Regenerate both README images"
	@echo "  make example-shots  Capture a screenshot of each example app (macOS)"
	@echo "  make examples-doc   Regenerate docs/source/examples.rst from the example apps"
	@echo "  make docs           Build the HTML documentation"

example-shots:  ## Capture a screenshot of each example app (macOS, Screen Recording permission)
	$(PYTHON) scripts/example_screenshots.py

examples-doc:  ## Regenerate the examples gallery page from the example apps
	$(PYTHON) scripts/gen_examples_doc.py

screenshot:  ## Regenerate the example-app screenshot (macOS, needs Screen Recording permission)
	$(PYTHON) scripts/screenshot.py

class-diagram:  ## Regenerate the class-hierarchy diagram (needs graphviz `dot`)
	$(PYTHON) scripts/class_diagram.py

readme-assets: class-diagram screenshot  ## Regenerate both README images

docs:  ## Build the HTML documentation
	$(PYTHON) -m sphinx -b html docs/source docs/build/html
