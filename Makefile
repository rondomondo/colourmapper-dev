# colourmapper-dev - Makefile
.DEFAULT_GOAL := help
SHELL := /bin/bash

# Colors
CYAN  := \033[36m
RESET := \033[0m

# Python
PYTHON   := python3
VENV     := .venv
PIP      := $(VENV)/bin/pip
PYTEST   := $(VENV)/bin/pytest
RUFF     := $(VENV)/bin/ruff
MYPY     := $(VENV)/bin/mypy
BLACK    := $(VENV)/bin/black --line-length 119 --target-version py312
ISORT    := $(VENV)/bin/isort

.PHONY: help
help: ## Show this help message
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) \
		| awk 'BEGIN {FS = ":.*?## "}; {printf "  $(CYAN)%-20s$(RESET) %s\n", $$1, $$2}'

.PHONY: check-venv
check-venv: venv ## Verify the virtual environment is activated
	@if [ -z "$${VIRTUAL_ENV:-}" ]; then \
	  printf "\033[31mERROR:\033[0m virtual env not active.\n"; \
	  printf "Activate it first:\n\n"; \
	  printf "  \033[32msource $(VENV)/bin/activate\033[0m\n\n"; \
	  printf "Then re-run make.\n"; \
	  exit 1; \
	fi
	@echo "  venv active: $${VIRTUAL_ENV}"

.PHONY: venv
venv: ## Create Python virtual environment (if absent)
	@if [ ! -d "$(VENV)" ]; then \
	  echo "  creating venv in $(VENV)..."; \
	  $(PYTHON) -m venv $(VENV); \
	  $(VENV)/bin/pip install --upgrade pip; \
	  echo "  venv created - activate with: source $(VENV)/bin/activate"; \
	else \
	  echo "  venv already exists in $(VENV)"; \
	fi


.PHONY: install-hooks
install-hooks: # Install git hook config
	git config core.hooksPath .githooks 2>/dev/null


.PHONY: install
install: venv ## Create venv (if absent) and install package + dev dependencies
	$(PIP) install --quiet --upgrade pip
	$(PIP) install -e ".[dev]"
	@echo "  installed. activate with: source $(VENV)/bin/activate"

.PHONY: install-tools
install-tools: venv ## Create venv (if absent) and install package + dev + mapping-file-create tools
	$(PIP) install --quiet --upgrade pip
	$(PIP) install -e ".[dev,tools]"
	@echo "  installed. activate with: source $(VENV)/bin/activate"

.PHONY: format
format: check-venv ## Format Python code (black + isort)
	$(BLACK) src/ tests/
	$(ISORT) src/ tests/

.PHONY: lint
lint: check-venv ## Lint Python code (ruff + mypy)
	$(RUFF) check --fix src/ tests/
	$(MYPY) src/

.PHONY: typecheck
typecheck: check-venv ## Run mypy type checks
	$(MYPY) src/

.PHONY: test
test: check-venv ## Run Python tests with coverage
	$(PYTEST) tests/ -v --tb=short --cov=src --cov-report=term-missing

.PHONY: clean
clean: ## Remove build artifacts and caches
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name .pytest_cache -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name .mypy_cache  -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name .ruff_cache  -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name .venv  -exec rm -rf {} + 2>/dev/null || true
	find ./demo -mindepth 1 -not -name "*.tape" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name dist         -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name build        -exec rm -rf {} + 2>/dev/null || true
	find . -name "*.egg-info" -exec rm -rf {} + 2>/dev/null || true
	rm -rf coverage/ .coverage htmlcov/ 2>/dev/null || true

.PHONY: build
build: check-venv ## Build wheel and sdist into dist/
	$(PIP) install --quiet build
	$(PYTHON) -m build

.PHONY: publish-test
publish-test: build ## Upload to TestPyPI (dry-run / staging)
	$(PIP) install --quiet twine
	$(VENV)/bin/twine upload --repository testpypi dist/*

.PHONY: publish
publish: build ## Upload to PyPI (requires credentials)
	@printf "\033[31mWARNING:\033[0m This will publish to the LIVE PyPI. Press Ctrl-C to abort, Enter to continue.\n" && read _
	$(PIP) install --quiet twine
	$(VENV)/bin/twine upload dist/*

.PHONY: ci
ci: lint test ## Run lint + test (for CI pipelines)
	@echo "CI passed"

# GitHub
.PHONY: github-check
github-check: ## Test GitHub SSH connectivity
	ssh -T git@github.com || true

# Examples
CM                  := src/colourmapper/cm.py
MAPPING_FILE_CREATE := src/colourmapper/mapping_file_create.py

.PHONY: examples
examples: ## Run usage examples (colour lookup + mapping file preview)
	@echo "  example: cm --url 'burnt orange'"
	$(PYTHON) $(CM) --url 'burnt orange' | jq '.'
	@echo ""
	@echo "  example: mapping-file-create --print | jq '.map | to_entries | .[0:5]'"
	$(PYTHON) $(MAPPING_FILE_CREATE) --print | jq '.map | to_entries | .[0:5]'


DEMO_PKGS  := make git jq htop curl cpio build-essential  python3 python3-dev python3.13-venv vim bash
DEMO_IMAGE := ghcr.io/charmbracelet/vhs
REPO_NAME  := colourmapper-dev
TAPE       ?= demo.tape

DEMO_TAPES := $(wildcard demo/*.tape)

.PHONY: demo
demo: ## Regenerate terminal demo GIF (via Docker, no local vhs needed)
	mkdir -p demo
	docker run -it --rm \
		-v $$(pwd):/tmp/src:ro \
		-v $$(pwd)/demo:/output \
		--name "vhs-$(REPO_NAME)" \
		--entrypoint sh $(DEMO_IMAGE) \
		-c "apt-get update -qq && apt-get install -y $(DEMO_PKGS) && \
			DEST=/tmp/$(REPO_NAME) && \
			mkdir -p \$$DEST && \
			cd /tmp/src && scripts/list_files.sh | cpio -pdm \$$DEST 2>/dev/null && \
			cd \$$DEST && \
			make clean && \
			make venv && \
			. \$$DEST/.venv/bin/activate && \
			make install && \
			make test && \
			cd \$$DEST/ && \
 			vhs \$$DEST/demo/$(TAPE) && \
 			cp -f \$$DEST/demo/demo.gif \$$DEST/demo/demo.mp4 /output/ 2>/dev/null || true"

