DEFAULT_GOAL := help
PROJECT=everett

.PHONY: help
help:
	@echo "Available rules:"
	@fgrep -h "##" Makefile | fgrep -v fgrep | sed 's/\(.*\):.*##/\1:/'

.PHONY: clean
clean:  ## Clean build artifacts
	rm -rf build dist ${PROJECT}.egg-info .tox
	rm -rf docs/_build/*
	find ${PROJECT}/ tests/ -name __pycache__ | xargs rm -rf
	find ${PROJECT}/ tests/ -name '*.pyc' | xargs rm -rf

.PHONY: lint
lint:  ## Lint and black reformat files
	black --target-version=py35 ${PROJECT} tests
	flake8 ${PROJECT} tests

.PHONY: docs
docs:  ## Build docs
	make -C docs/ html
