# MCP Server Template — Makefile
# Developer workflow for Python backend, testing, linting, and environment setup

# Colors (for pretty output)
GREEN  := $(shell tput -Txterm setaf 2)
YELLOW := $(shell tput -Txterm setaf 3)
BLUE   := $(shell tput -Txterm setaf 4)
CYAN   := $(shell tput -Txterm setaf 6)
RED    := $(shell tput -Txterm setaf 1)
RESET  := $(shell tput -Txterm sgr0)

.DEFAULT_GOAL := help

# Python tooling
UV    ?= uv
RUN   ?= $(UV) run

# Paths
SRC_DIR := src
TEST_DIR := tests
EXAMPLES_DIR := examples
SCRIPTS_DIR := scripts

## Show help
help:
	@echo ''
	@echo '$(CYAN)MCP Server Template — Developer Commands$(RESET)'
	@echo ''
	@echo 'Usage:'
	@echo '  $(YELLOW)make$(RESET) $(GREEN)<target>$(RESET)'
	@echo ''
	@echo 'Targets:'
	@awk '/^[a-zA-Z\-_0-9]+:/ { \
		helpMessage = match(lastLine, /^## (.*)/); \
		if (helpMessage) { \
			helpCommand = substr($$1, 0, index($$1, ":")-1); \
			helpMessage = substr(lastLine, RSTART + 3, RLENGTH); \
			printf "\033[36m%-20s\033[0m %s\n", helpCommand, helpMessage; \
		} \
	} \
	{ lastLine = $$0 }' $(MAKEFILE_LIST)

# =============================================================================
# SETUP AND QUALITY
# =============================================================================

## Install project dependencies with uv
install:
	@echo "$(BLUE)Installing dependencies (uv sync)...$(RESET)"
	$(UV) sync
	@echo "$(GREEN)Dependencies installed.$(RESET)"

## Setup dev env: install deps, ensure .env exists
setup: install ensure-env
	@echo "$(GREEN)Development environment ready.$(RESET)"

## Ensure .env exists (copies from .env.example if present)
ensure-env:
	@if [ ! -f .env ] && [ -f .env.example ]; then \
		echo "$(YELLOW).env not found. Creating from .env.example$(RESET)"; \
		cp .env.example .env; \
	else \
		echo "$(GREEN).env present.$(RESET)"; \
	fi

## Lint with Ruff
lint:
	@echo "$(BLUE)Ruff lint...$(RESET)"
	$(RUN) ruff check $(SRC_DIR) $(TEST_DIR)

## Format with Ruff
format:
	@echo "$(BLUE)Ruff format...$(RESET)"
	$(RUN) ruff format $(SRC_DIR) $(TEST_DIR)

## Type-check with MyPy
mypy:
	@echo "$(BLUE)MyPy type-check...$(RESET)"
	$(RUN) mypy $(SRC_DIR)

## Run tests (pytest)
test:
	@echo "$(BLUE)Running tests...$(RESET)"
	$(RUN) pytest -q

## Run coverage report
coverage:
	@echo "$(BLUE)Running coverage...$(RESET)"
	$(RUN) pytest --cov=$(SRC_DIR) --cov-report=html
	@echo "$(GREEN)Coverage report generated in htmlcov/.$(RESET)"

# =============================================================================
# RUNNING THE SERVER
# =============================================================================

## Run the MCP server (dev mode)
run:
	@echo "$(BLUE)Starting MCP server...$(RESET)"
	$(RUN) python $(SCRIPTS_DIR)/run_server.py

## Run example client
example:
	@echo "$(BLUE)Running example client...$(RESET)"
	$(RUN) python $(EXAMPLES_DIR)/simple_client.py

# =============================================================================
# UTILITIES
# =============================================================================

## Clean Python cache and coverage artifacts
clean:
	@echo "$(YELLOW)Cleaning cache and coverage...$(RESET)"
	rm -rf __pycache__ $(SRC_DIR)/**/__pycache__ $(TEST_DIR)/**/__pycache__ .pytest_cache htmlcov .mypy_cache .ruff_cache
	@echo "$(GREEN)Cleaned.$(RESET)"

.PHONY: help install setup ensure-env lint format mypy test coverage run example clean
