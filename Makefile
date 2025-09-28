# Archon Makefile - Simple, Secure, Cross-Platform
UV := $(HOME)/.local/bin/uv
PNPM := $(HOME)/.npm-global/bin/pnpm
SHELL := /bin/bash
.SHELLFLAGS := -ec

# Docker compose command - prefer newer 'docker compose' plugin over standalone 'docker-compose'
COMPOSE ?= $(shell docker compose version >/dev/null 2>&1 && echo "docker compose" || echo "docker-compose")

.PHONY: help dev dev-docker stop test test-fe test-be lint lint-fe lint-be clean install check install-ui

help:
	@echo "Archon Development Commands"
	@echo "==========================="
	@echo "  make dev        - Backend in Docker, frontend local (recommended)"
	@echo "  make dev-docker - Everything in Docker"
	@echo "  make stop       - Stop all services"
	@echo "  make test       - Run all tests"
	@echo "  make test-fe    - Run frontend tests only"
	@echo "  make test-fe-project project=<project> - Run tests for a specific frontend project"
	@echo "  make test-fe-single project=<project> test=<test> - Run a single frontend test"
	@echo "  make test-be    - Run backend tests only"
	@echo "  make lint       - Run all linters"
	@echo "  make lint-fe    - Run frontend linter only"
	@echo "  make lint-be    - Run backend linter only"
	@echo "  make clean      - Remove containers and volumes"
	@echo "  make install    - Install dependencies"
	@echo "  make install-ui - Install monorepo UI dependencies"
	@echo "  make check      - Check environment setup"

# Install dependencies
install:
	@echo "Installing dependencies..."
	@cd enduser-ui-fe && $(PNPM) install
	@cd python && $(UV) sync --group all --group dev
	@echo "✓ Dependencies installed"

install-ui:
	@echo "Installing missing monorepo UI dependencies (archon-ui)..."
	@$(PNPM) install --filter archon-ui

# NOTE: The following check target uses syntax that is not compatible with Windows cmd/PowerShell.
# It will cause an error on Windows systems.
# Check environment
check:
	@echo "Checking environment..."
	@node -v >/dev/null 2>&1 || { echo "✗ Node.js not found (require Node 18+)."; exit 1; }
	@node check-env.js
	@echo "Checking Docker..."
	@docker --version > /dev/null 2>&1 || { echo "✗ Docker not found"; exit 1; }
	@$(COMPOSE) version > /dev/null 2>&1 || { echo "✗ Docker Compose not found"; exit 1; }
	@echo "✓ Environment OK"


# Hybrid development (recommended)
dev: check
	@echo "Starting hybrid development..."
	@echo "Backend: Docker | Frontend: Local with hot reload"
	@$(COMPOSE) --profile backend up -d --build
	@set -a; [ -f .env ] && . ./.env; set +a; \
	echo "Backend running at http://$${HOST:-localhost}:$${ARCHON_SERVER_PORT:-8181}"
	@echo "Starting frontend..."
	@cd archon-ui-main && \
	VITE_ARCHON_SERVER_PORT=$${ARCHON_SERVER_PORT:-8181} \
	VITE_ARCHON_SERVER_HOST=$${HOST:-} \
	$(PNPM) run dev

# Full Docker development
dev-docker: check
	@echo "Starting full Docker environment..."
	@$(COMPOSE) --profile full up -d --build
	@echo "✓ All services running"
	@echo "Frontend: http://localhost:3737"
	@echo "API: http://localhost:8181"

# Stop all services
stop:
	@echo "Stopping all services..."
	@$(COMPOSE) --profile backend --profile frontend --profile full down
	@echo "✓ Services stopped"

# Run all tests (fast version)
# This runs backend tests and a quick frontend smoke test on enduser-ui-fe.
# The full, slow archon-ui-main tests are skipped for efficiency.
test: test-fe-enduser test-be

# Run all frontend tests (fast and slow)
test-fe-all: test-fe-enduser test-fe-admin

# Run QUICK frontend tests for the End-User UI (enduser-ui-fe)
test-fe-enduser:
	@echo "Running FAST frontend tests for End-User UI (enduser-ui-fe)..."
	@cd enduser-ui-fe && $(PNPM) test

# Run SLOW, COMPREHENSIVE frontend tests for the Admin UI (archon-ui-main)
# NOTE: These tests are known to be very slow (>20 minutes). Run them intentionally.
test-fe-admin:
	@echo "Running SLOW frontend tests for Admin UI (archon-ui-main)..."
	@cd archon-ui-main && /Users/vincenta/.npm-global/bin/pnpm test

# (Legacy) Alias for the fast enduser-ui-fe tests to maintain backward compatibility.
test-fe: test-fe-enduser

# Test a specific frontend subproject
# Usage: make test-fe-project project=<project_name>
# Example: make test-fe-project project=enduser-ui-fe
test-fe-project:
	@echo "Running frontend tests for $(project)..."
	@cd $(project) && $(PNPM) test

# Test a single frontend test file
# Usage: make test-fe-single project=<project_name> test=<test_name>
# Example: make test-fe-single project=enduser-ui-fe test="TaskModal"
test-fe-single:
	@echo "Running single frontend test '$(test)' in $(project)..."
	@cd $(project) && $(PNPM) test -- -t "$(test)"

# Run backend tests
test-be:
	@echo "Running backend tests..."
	@cd python && $(UV) sync --group dev --group mcp --group agents --group server
	@cd python && $(UV) run pytest

# Run all linters (fast version)
lint: lint-fe-enduser lint-be

# Run all frontend linters
lint-fe-all: lint-fe-enduser lint-fe-admin

# Run linter for the End-User UI (enduser-ui-fe)
lint-fe-enduser:
	@echo "Linting End-User UI (enduser-ui-fe)..."
	@cd enduser-ui-fe && $(PNPM) run lint

# Run linter for the Admin UI (archon-ui-main)
lint-fe-admin:
	@echo "Linting Admin UI (archon-ui-main)..."
	@cd archon-ui-main && /Users/vincenta/.npm-global/bin/pnpm run lint

# (Legacy) Alias for the enduser-ui-fe linter.
lint-fe: lint-fe-enduser

# Run backend linter
lint-be:
	@echo "Linting backend..."
	@cd python && $(UV) sync --group dev
	@cd python && $(UV) run ruff check

# Clean everything (with confirmation)
clean:
	@echo "⚠️  This will remove all containers and volumes"
	@read -p "Are you sure? (y/N) " -n 1 -r; \
	echo; \
	if [[ $$REPLY =~ ^[Yy]$$ ]]; then \
		$(COMPOSE) down -v --remove-orphans; \
		echo "✓ Cleaned"; \
	else \
		echo "Cancelled"; \
	fi

.DEFAULT_GOAL := help
