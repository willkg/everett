sphinxbuild := "../.venv/bin/sphinx-build"

@_default:
    just --list

# Build a development environment
devenv:
    uv sync --extra sphinx --extra ini --extra yaml --extra dev --refresh --upgrade

# Run tests, linting, and static typechecking
test: devenv
    uv run tox

# Format files
format: devenv
    uv run tox exec -e py310-lint -- ruff format

# Lint files
lint: devenv
    uv run tox -e py310-lint

# Wipe devenv and build artifacts
clean:
    rm -rf .venv uv.lock
    rm -rf build dist src/everett.egg-info .tox .pytest_cache .mypy_cache
    rm -rf docs/_build/*
    find src/ tests/ -name __pycache__ | xargs rm -rf
    find src/ tests/ -name '*.pyc' | xargs rm -rf

# Runs cog and builds Sphinx docs
docs: devenv
    uv run python -m cogapp -r README.rst
    uv run python -m cogapp -r docs/components.rst
    uv run python -m cogapp -r docs/configmanager.rst
    uv run python -m cogapp -r docs/configuration.rst
    SPHINXBUILD={{sphinxbuild}} make -e -C docs/ clean
    SPHINXBUILD={{sphinxbuild}} make -e -C docs/ doctest
    SPHINXBUILD={{sphinxbuild}} make -e -C docs/ html

# Build files for relase
build: devenv
    rm -rf build/ dist/
    uv run python -m build
    uv run twine check dist/*
