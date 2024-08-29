# Makefile for setting up and activating a Python virtual environment

# Set the desired Python interpreter (change if needed)
PYTHON := python3.11

# Virtual environment directory
VENV := .venv

STAGE?=ppe

# Default target
all: venv activate install

# Create the virtual environment
venv:
	@echo "Creating Python virtual environment..."
	$(PYTHON) -m venv $(VENV)

# Activate the virtual environment
activate:
	@echo "Activating Python virtual environment..."
	@echo "Run 'deactivate' to exit the virtual environment."
	@. $(VENV)/bin/activate

install:
	@echo "Installing dependencies from requirements files"
	pip install --upgrade pip
	pip install uv pur
	uv pip install --system --native-tls --upgrade pip
	uv pip install --system --native-tls -r requirements.txt
	uv pip install --system --native-tls -r requirements-dev.txt
	uv pip install --system --native-tls pre-commit pytest pytest-snapshot

local_install:
	@echo "Installing dependencies from requirements files"
	pip install --upgrade pip
	pip install uv pur
	uv pip install -r requirements.txt
	uv pip install -r requirements-dev.txt
	uv pip install pre-commit pytest pytest-snapshot


pre-commit:
	@echo "Running pre-commit"
	pre-commit install
	pre-commit run --files app.py
	pre-commit run --files cdk/constructs/*.py
	pre-commit run --files cdk/schemas/*.py
	pre-commit run --files cdk/stacks/*.py
	pre-commit run --files cdk/stacks/services/*.py
	pre-commit run --files cdk/stages/*.py
	pre-commit run --files cdk/tests/infrastructure/*.py
	pre-commit run --files cdk/tests/integration/*.py
	pre-commit run --files cdk/tests/*.py


test:
	@echo "Running pytest for stage "
	STAGE=$(STAGE) pytest cdk/tests/infrastructure/

update-tests:
	@echo "Updating pytest snapshots"
	STAGE=$(STAGE) pytest --snapshot-update cdk/tests/infrastructure/

update:
	@echo "Updating used tools and scripts"
	pur -r requirements.txt
	pur -r requirements-dev.txt
	pre-commit autoupdate

clean:
	@echo "Cleaning up..."
	rm -rf $(VENV)

help:
	@echo "Available commands:"
	@echo "  all              - Create venv, activate it, and install dependencies"
	@echo "  venv             - Create the Python virtual environment"
	@echo "  activate         - Activate the Python virtual environment"
	@echo "  install          - Install dependencies from requirements files"
	@echo "  local_install    - Install dependencies locally, including layer requirements"
	@echo "  pre-commit       - Install and run pre-commit hooks on all files"
	@echo "  test             - Run pytest for the specified stage (default: ppe)"
	@echo "  update-tests     - Update pytest snapshots"
	@echo "  update           - Update dependencies and pre-commit hooks"
	@echo "  clean            - Remove the virtual environment and clean up"
	@echo "  help             - Display this help message"


.PHONY: all venv activate test clean pre-commit update help
