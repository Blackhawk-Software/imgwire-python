SHELL := /bin/sh

VENV ?= .venv
PYTHON ?= python3
NODE ?= yarn

VENV_PYTHON := $(VENV)/bin/python
VENV_PIP := $(VENV)/bin/pip

.PHONY: help install install-js venv install-py generate verify-generated test build format format-py format-js release-set clean ci

help:
	@printf "%s\n" \
		"Targets:" \
		"  make install            Install JS tooling and Python dev environment" \
		"  make install-js         Install Yarn tooling with frozen lockfile" \
		"  make venv               Create the local Python virtualenv" \
		"  make install-py         Install Python package and dev tooling into $(VENV)" \
		"  make generate           Regenerate checked-in OpenAPI and generated client artifacts" \
		"  make verify-generated   Verify checked-in generated artifacts are current" \
		"  make test               Run Python unit tests" \
		"  make build              Build sdist and wheel" \
		"  make format             Run Python and non-Python formatting" \
		"  make format-py          Run the Python formatter" \
		"  make format-js          Run Prettier for repo metadata and docs" \
		"  make release-set VERSION=X.Y.Z  Set the repo/package version manually" \
		"  make clean              Remove local build artifacts" \
		"  make ci                 Run generation verification, tests, and package build"

install: install-js install-py

install-js:
	$(NODE) install --frozen-lockfile

venv:
	$(PYTHON) -m venv $(VENV)

install-py: venv
	$(VENV_PYTHON) -m pip install --upgrade pip setuptools wheel
	$(VENV_PIP) install -e ".[dev]"

generate:
	$(NODE) generate

verify-generated:
	$(NODE) verify-generated

test:
	$(VENV_PYTHON) -m unittest discover -s tests -p 'test_*.py'

build:
	$(VENV_PYTHON) -m build

format:
	$(MAKE) format-py
	$(MAKE) format-js

format-py:
	$(VENV_PYTHON) -m ruff format imgwire tests

format-js:
	$(NODE) format

release-set:
	@test -n "$(VERSION)" || (echo "VERSION is required. Usage: make release-set VERSION=0.2.0" && exit 1)
	$(NODE) release:set-version $(VERSION)

clean:
	rm -rf build dist imgwire.egg-info

ci: verify-generated test build
