# Set the desired Python interpreter (change if needed)
PYTHON := python3.13
VENV := .venv
STAGE?=dev

.PHONY: all venv activate test clean prek update help

all: venv activate install # Initialize complete development environment

venv: # Create new Python virtual environment
	uv venv --seed --python $(PYTHON) $(VENV)

activate: # Activate Python virtual environment
	@. $(VENV)/bin/activate

install: # Install all project dependencies and development tools
	pip install --upgrade pip
	pip install --upgrade uv
	uv pip install --upgrade pip
	uv pip install -r requirements.txt
	uv pip install -r requirements-dev.txt
	uv pip install pytest pytest-snapshot prek


prek: # Run code quality checks on all Python files
	prek install
	prek run --files cdk/constructs/*.py
	prek run --files cdk/schemas/*.py
	prek run --files cdk/stacks/*.py
	prek run --files cdk/stacks/services/*.py
	prek run --files cdk/stages/*.py
	prek run --files cdk/stages/logic/*.py
	prek run --files cdk/tests/infrastructure/*.py
	prek run --files cdk/tests/integration/*.py
	prek run --files cdk/tests/*.py
	prek run --files cdk/documentation/*
	prek run --files *
	prek run --files .github/*
	prek run --files .github/workflows/*

tests: # Run infrastructure tests for specified stage
	STAGE=$(STAGE) pytest cdk/tests/infrastructure/

update-tests: # Update infrastructure test snapshots
	STAGE=$(STAGE) pytest --snapshot-update cdk/tests/infrastructure/

update: # Update all dependencies and tools to latest versions
	pur -r requirements.txt
	pur -r requirements-dev.txt
	prek autoupdate

clean: # Remove virtual environment and cleanup project files
	rm -rf $(VENV)
	rm -rf cdk.out
	prek clean
	prek gc

help: # Display this help message
	@printf "\n\033[1;32mAvailable commands: \033[00m\n\n"
	@awk 'BEGIN {FS = ":.*#"; printf "\033[36m%-30s\033[0m %s\n", "target", "help"} /^[a-zA-Z0-9_-]+:.*?#/ { printf "\033[36m%-30s\033[0m %s\n", $$1, $$2 }' $(MAKEFILE_LIST)
