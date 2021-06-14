DEFAULT_GOAL := help
PROJECT=everett

.PHONY: help
help:
	@echo "Available rules:"
	@fgrep -h "##" Makefile | fgrep -v fgrep | sed 's/\(.*\):.*##/\1:  /'

.PHONY: test
test:  ## Run tests and static typechecking
	tox

.PHONY: typecheck
typecheck:  ## Run typechecking (requires Python 3.8)
	mypy src/everett/

.PHONY: lint
lint:  ## Lint and black reformat files
	black --target-version=py36 --line-length=88 src setup.py tests docs
	flake8 src tests

.PHONY: clean
clean:  ## Clean build artifacts
	rm -rf build dist src/${PROJECT}.egg-info .tox .pytest_cache .mypy_cache
	rm -rf docs/_build/*
	find src/ tests/ -name __pycache__ | xargs rm -rf
	find src/ tests/ -name '*.pyc' | xargs rm -rf

.PHONY: docs
docs:  ## Build docs
	make -C docs/ html

.PHONY: checkrot
checkrot:  ## Check package rot for dev dependencies
	python -m venv ./tmpvenv/
	./tmpvenv/bin/pip install -U pip
	./tmpvenv/bin/pip install '.[dev,ini,yaml]'
	./tmpvenv/bin/pip list -o
	rm -rf ./tmpvenv/
