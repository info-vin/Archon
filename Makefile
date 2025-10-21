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

# Run all tests
test: test-fe test-be

# NOTE: 執行環境差異提醒
# 以下前端測試在本地終端機中執行速度很快 (約 7 秒)，
# 但透過自動化工具 (如 Gemini CLI) 執行時可能會顯著變慢。
# 這屬於已知環境差異。
# Run all frontend tests
test-fe:
	@echo "Running all frontend tests..."
	@echo "--- Testing End-User UI (enduser-ui-fe) ---"
	@cd enduser-ui-fe && $(PNPM) test
	@echo "--- Testing Admin UI (archon-ui-main) ---"
	@cd archon-ui-main && $(PNPM) test

# 在背景執行完整的前端測試，並將結果輸出到日誌檔案
test-fe-background:
	@echo "Starting all frontend tests in the background..."
	@echo "Output will be saved to frontend-test-results.log"
	@make test-fe > frontend-test-results.log 2>&1 &

# 2. 測試特定前端子專案 (Test a specific frontend subproject)
#    用法 (Usage): make test-fe-project project=<project_name>
#    範例 (Example): make test-fe-project project=enduser-ui-fe
test-fe-project:
	@echo "Running frontend tests for $(project)..."
	@cd $(project) && $(PNPM) test

# 3. 測試特定單一前端測試 (Test a single frontend test)
#    用法 (Usage): make test-fe-single project=<project_name> test=<test_name>
#    範例 (Example): make test-fe-single project=enduser-ui-fe test="TaskModal"
test-fe-single:
	@echo "Running single frontend test '$(test)' in $(project)..."
	@cd $(project) && $(PNPM) test -- -t "$(test)"

# Run backend tests
test-be:
	@echo "Running backend tests..."
	@cd python && $(UV) sync --group dev --group mcp --group agents --group server
	@cd python && $(UV) run pytest

# Run all linters
lint: lint-fe lint-be

# Run all frontend linters
lint-fe:
	@echo "Linting all frontend projects..."
	@echo "--- Linting End-User UI (enduser-ui-fe) ---"
	@cd enduser-ui-fe && $(PNPM) run --if-present lint
	@echo "--- Linting Admin UI (archon-ui-main) ---"
	@cd archon-ui-main && $(PNPM) run --if-present lint

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
