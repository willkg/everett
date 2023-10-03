DEFAULT_GOAL := help
PROJECT=everett

.PHONY: help
help:
	@echo "Available rules:"
	@fgrep -h "##" Makefile | fgrep -v fgrep | sed 's/\(.*\):.*##/\1:  /'

.PHONY: test
test:  ## Run tests, linting, and static typechecking
	tox

.PHONY: lint
lint:  ## Lint and black reformat files
	# NOTE(willkg): Make sure this matches what's in tox.ini.
	black src setup.py tests docs examples
	tox -e py38-lint

.PHONY: clean
clean:  ## Clean build artifacts
	rm -rf build dist src/${PROJECT}.egg-info .tox .pytest_cache .mypy_cache
	rm -rf docs/_build/*
	find src/ tests/ -name __pycache__ | xargs rm -rf
	find src/ tests/ -name '*.pyc' | xargs rm -rf

.PHONY: docs
docs:  ## Runs cog and builds Sphinx docs
	python -m cogapp -d -o README.rst docs_tmpl/README.rst
	python -m cogapp -d -o docs/components.rst docs_tmpl/components.rst
	python -m cogapp -d -o docs/configmanager.rst docs_tmpl/configmanager.rst
	python -m cogapp -d -o docs/configuration.rst docs_tmpl/configuration.rst
	make -C docs/ clean
	make -C docs/ doctest
	make -C docs/ html

.PHONY: checkrot
checkrot:  ## Check package rot for dev dependencies
	python -m venv ./tmpvenv/
	./tmpvenv/bin/pip install -U pip
	./tmpvenv/bin/pip install -r requirements-dev.txt
	./tmpvenv/bin/pip list -o
	rm -rf ./tmpvenv/
