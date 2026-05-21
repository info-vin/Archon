# Archon Makefile - Simple, Secure, Cross-Platform
UV := uv
PNPM := pnpm
SHELL := /bin/bash
.SHELLFLAGS := -ec

# Docker compose command - prefer newer 'docker compose' plugin over standalone 'docker-compose'
COMPOSE ?= $(shell docker compose version >/dev/null 2>&1 && echo "docker compose" || echo "docker-compose")

.PHONY: help dev dev-docker stop test test-fe test-be lint lint-fe lint-be clean install check install-ui db-init db-migrate tech-debt-audit audit-qa

help:
	@echo "Archon Development Commands"
	@echo "==========================="
	@echo "  make dev        - Backend in Docker, frontend local (recommended)"
	@echo "  make dev-docker - Everything in Docker"
	@echo "  make stop       - Stop all services"
	@echo "  make db-init    - Initialize database (Base: Migrations + Seeds + Auth)"
	@echo "  make db-fuel    - Inject 6 month historical data for Nexus Trends (Optional)"
	@echo "  make db-migrate - Run schema migrations ONLY"
	@echo "  make db-reset   - WIPE and Re-initialize database (Destructive)"
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
	@echo "  make tech-debt-audit - Check for stale files and cluttered directories"
	@echo "  make audit-qa   - Run unified E2E, semantic & static Quality Gateway suite"

# Install dependencies
install:
	@echo "Cleaning old build artifacts..."
	@rm -rf enduser-ui-fe/dist archon-ui-main/dist
	@echo "Installing dependencies..."
	@cd enduser-ui-fe && $(PNPM) install
	@cd python && $(UV) sync --group all --group dev
	@echo "✓ Dependencies installed"

install-ui:
	@echo "Installing missing monorepo UI dependencies (archon-ui)..."
	@$(PNPM) install --filter archon-ui

# Database initialization (Idempotent)
db-init:
	@echo "Initializing database inside archon-server container..."
	@docker exec -i archon-server /venv/bin/python scripts/init_db.py $(ARGS)
# Inject historical trend data (GAP-027, 030, 032, 033, 034)
db-fuel:
	@echo "Fueling Nexus with 180-day strategic data..."
	@docker exec -i archon-server /venv/bin/python scripts/fuel_nexus.py

# Database Migration Only
db-migrate:
	@echo "Running schema migrations inside archon-server container..."
	@docker exec -i archon-server /venv/bin/python scripts/init_db.py --migrate-only

# Database reset (Clean & Re-init)
db-reset:
	@echo "⚠️  WARNING: This will WIPE the entire database (including Cloud data)."
	@read -p "Are you sure? (y/N) " -n 1 -r; \
	echo; \
	if [[ $$REPLY =~ ^[Yy]$$ ]]; then \
		echo "Resetting database inside archon-server container..."; \
		docker exec -i archon-server /venv/bin/python scripts/init_db.py --clean; \
	else \
		echo "Cancelled"; \
	fi

# Verify database seed data
verify-data:
	@echo "Verifying database state inside docker container..."
	@docker exec -i archon-server /venv/bin/python - < scripts/verify_seed.py

# Run Librarian Probe (Diagnostics)
# --- 5-Persona Physical Health Gate ---
persona-audit:
	@echo "🔍 Performing Global Persona Physical Audit (Alice, Bob, Charlie, David, Agents)..."
	@docker exec -i archon-server /venv/bin/python scripts/persona_smoke_test.py

# --- Automated Quality Gateway (Milestone 5) ---
audit-qa:
	@echo "🚨 [AuditQA] Starting Unified Quality Gateway Automation Suite..."
	@echo "Step 1: Running Linter & Type Checker (make lint)..."
	@make lint
	@echo "Step 2: Running Frontend Unit Tests (pnpm)..."
	@cd enduser-ui-fe && $(PNPM) run test:unit
	@cd archon-ui-main && $(PNPM) test
	@echo "Step 3: Running DNS Leak Probe static scan..."
	@bash scripts/probe_dns_leak.sh
	@echo "Step 4: Running Mobile Viewport Scroll Lockup static scan..."
	@cd python && $(UV) run python ../scripts/check_scroll_lockup.py
	@echo "Step 5: Running Shadow DB Migration verifier..."
	@cd python && $(UV) run python ../scripts/verify_migrations.py
	@echo "Step 6: Running LLM Content Judge Semantic checks..."
	@cd python && $(UV) run python ../scripts/llm_judge_content.py
	@echo "Step 7: Running Backend Pytest suite..."
	@make test-be
	@echo "🎉 [AuditQA] ALL STATIC & HERMETIC UNIT GATEWAYS PASSED SUCCESSFULLY!"

# 獨立出會重置資料庫的 E2E 測試門禁
audit-qa-e2e:
	@echo "🚨 [AuditQA-E2E] Running destructive E2E suite (Resets Database)..."
	@cd enduser-ui-fe && npx playwright test tests/playwright/BudgetWarning.mbt.spec.ts
	@echo "🎉 [AuditQA-E2E] E2E GATEWAY PASSED."

probe:
	@echo "Running Librarian Probe inside archon-server..."
	@docker exec -i archon-server /venv/bin/python -c "from src.server.services.health_service import HealthService; import asyncio; hs = HealthService(); print(asyncio.run(hs.check_rag_integrity()))"

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
	@$(COMPOSE) --profile backend --profile agents up -d --build
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
	@set -a; [ -f .env ] && . ./.env; set +a; \
	$(COMPOSE) --profile backend --profile frontend --profile enduser --profile agents up -d --build
	@echo "✓ All services running"
	@echo "Admin UI: http://localhost:3737"
	@echo "End-User UI: http://localhost:5173"
	@echo "API Server: http://localhost:8181"

# Stop all services
stop:
	@echo "Stopping all services..."
	@$(COMPOSE) --profile backend --profile frontend --profile enduser --profile agents down
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
	@cd enduser-ui-fe && $(PNPM) run test:unit && $(PNPM) run test:e2e
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
	@if [ "$(project)" = "enduser-ui-fe" ]; then \
		cd $(project) && $(PNPM) run test:e2e -- -t "$(test)"; \
	else \
		cd $(project) && $(PNPM) test -- -t "$(test)"; \
	fi

# Run backend tests
test-be:
	@echo "Running backend tests..."
	@if [ "$$(grep SUPABASE_URL .env.test | cut -d= -f2 | grep -i 'supabase.co' | grep -v 'test-isolated')" != "" ] && [ "$$FORCE_PROD_TEST" != "true" ]; then \
		echo "❌ ERROR: Production database detected in .env.test! Testing blocked to prevent data wipe."; \
		echo "Use 'FORCE_PROD_TEST=true make test-be' if you really mean it."; \
		exit 1; \
	fi
	@touch .env.test
	@cd python && $(UV) sync --group dev --group mcp --group agents --group server && $(UV) run --env-file ../.env.test pytest


# Run performance diagnostic
test-perf:
	@echo "Running Token Usage Performance Diagnostic..."
	@cd python && $(UV) run python ../scripts/reproduce_blocking_token_usage.py

# Run all linters
lint: lint-fe lint-be

# Run all frontend linters
lint-fe:
	@echo "Linting all frontend projects..."
	@echo "--- Linting End-User UI (enduser-ui-fe) ---"
	@cd enduser-ui-fe && $(PNPM) run --if-present lint && $(PNPM) tsc --noEmit
	@echo "--- Linting Admin UI (archon-ui-main) ---"
	@cd archon-ui-main && $(PNPM) run --if-present lint && $(PNPM) tsc --noEmit

# Run backend linter
lint-be:
	@echo "Linting backend..."
	@cd python && $(UV) sync --all-groups
	@cd python && $(UV) run ruff check --fix
	@cd python && $(UV) run mypy src --ignore-missing-imports

# Clean everything (with confirmation)
clean:
	@echo "⚠️  This will remove all containers and volumes"
	@read -p "Are you sure? (y/N) " -n 1 -r; \
	echo; \
	if [[ $$REPLY =~ ^[Yy]$$ ]]; then \
		$(COMPOSE) --profile backend --profile frontend --profile enduser --profile agents down -v --remove-orphans; \
		echo "✓ Cleaned"; \
	else \
		echo "Cancelled"; \
	fi

.PHONY: twin-scout twin-scout-action twin-scout-fanout twin-fix

# 執行自動偵察 (容器化對帳模式)
twin-scout:
	@echo "🚀 啟動數位孿生偵察員 (容器化對帳 | 目標 Prompt: $${T:-twin_scout_mission})..."
	@docker exec -i -e SCOUT_PROMPT_KEY=$${T:-twin_scout_mission} archon-server /venv/bin/python scripts/twin_scout.py --mode audit

# 執行自動偵察 (本地原生行動與星型群聊自癒巡檢)
twin-scout-action:
	@echo "🚀 啟動數位孿生偵察員 (本機原生模式 | 目標 Prompt: $${T:-twin_scout_mission})..."
	@set -a; [ -f .env ] && . ./.env; set +a; \
	$(UV) run --env-file .env python scripts/twin_scout.py --mode action --headless false

# 執行 Fan-out 並發引擎物理公證
twin-scout-fanout:
	@echo "🚀 啟動數位孿生偵察員 (Fan-out 併發公證)..."
	@set -a; [ -f .env ] && . ./.env; set +a; \
	$(UV) run --env-file .env python scripts/twin_scout.py --mode fanout --headless false

# 提示 Antigravity 維修流程
twin-fix:
	@echo "🛠️  請在 Antigravity 中執行："
	@echo "1. 指令: '閱讀 .twin/diagnostics/ 下的最新報告'"
	@echo "2. 指令: '根據報告修復代碼並更新 RAG 知識庫'"

.DEFAULT_GOAL := help

# Phase 4.6.28: 終極物理同步與重建
sync-grounding:
	@echo "Syncing latest changes from remote..."
	@git fetch -a
	@git pull --rebase origin feat/twins
	@echo "Sync complete."
	@echo "Building and starting all services (Clean State)..."
	@$(COMPOSE) --profile backend --profile agents --profile frontend --profile enduser build --no-cache
	@$(COMPOSE) --profile backend --profile agents --profile frontend --profile enduser up -d
	@echo "Environment reborn. Initializing data..."
	@docker exec -i archon-server /venv/bin/python scripts/init_db.py --clean
	@echo "🎉 FULL SYSTEM SYNC COMPLETE & VERIFIED."
	@docker images --format "table {{.Repository}}\t{{.Size}}" | grep -E "archon|enduser"
	@docker compose ps

# Run Technical Debt Audit (Charlie's Command to DevBot)
tech-debt-audit:
	@echo "🧹 Running Technical Debt Audit (DevBot Prep)..."
	@echo "--- 1. Unarchived PRPs Check ---"
	@count=$$(ls -1 PRPs/Phase_*.md 2>/dev/null | wc -l | tr -d ' '); \
	if [ "$$count" -ge 5 ]; then \
		echo "⚠️  [WARNING] PRPs directory is cluttered ($$count unarchived files). Charlie: Assign DevBot to archive completed phases."; \
	else \
		echo "✅ PRPs directory is clean."; \
	fi
	@echo "--- 2. Stale Scripts Check ---"
	@threshold=$$(date -v-14d +%s 2>/dev/null || date -d "14 days ago" +%s 2>/dev/null); \
	stale_found=0; \
	for file in scripts/*.py scripts/*.sh python/scripts/*.py; do \
		if [ -f "$$file" ]; then \
			last_commit=$$(git log -1 --format="%ct" -- "$$file" 2>/dev/null); \
			if [ -n "$$last_commit" ] && [ "$$last_commit" -lt "$$threshold" ]; then \
				echo "⚠️  [WARNING] Stale script found: $$file (No updates in > 14 days)."; \
				stale_found=1; \
			fi \
		fi \
	done; \
	if [ "$$stale_found" -eq 0 ]; then \
		echo "✅ No stale scripts found."; \
	fi
	@echo "--- 3. Action Item ---"
	@echo "💡 Charlie: If warnings exist, assign a cleanup task to DevBot."
