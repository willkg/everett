# Build a development environment
devenv:
    uv sync --extra sphinx --extra ini --extra yaml --extra dev

# Run tests, linting, and static typechecking
test: devenv
    uv run tox

# Format files
format: devenv
    uv run tox exec -e py38-lint -- ruff format

# Lint files
lint: devenv
    uv run tox -e py38-lint

# Wipe devenv and build artifacts
clean:
    rm -rf .venv uv.lock
    rm -rf build dist src/everett.egg-info .tox .pytest_cache .mypy_cache
    rm -rf docs/_build/*
    find src/ tests/ -name __pycache__ | xargs rm -rf
    find src/ tests/ -name '*.pyc' | xargs rm -rf

# Runs cog and builds Sphinx docs
docs: devenv
    uv run python -m cogapp -d -o README.rst docs_tmpl/README.rst
    uv run python -m cogapp -d -o docs/components.rst docs_tmpl/components.rst
    uv run python -m cogapp -d -o docs/configmanager.rst docs_tmpl/configmanager.rst
    uv run python -m cogapp -d -o docs/configuration.rst docs_tmpl/configuration.rst
    make -C docs/ clean
    make -C docs/ doctest
    make -C docs/ html
