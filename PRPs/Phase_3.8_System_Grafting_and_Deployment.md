---
name: "PRP 3.8: System Grafting & Deployment (系統嫁接與部署)"
description: "將 `feature/e2e-file-upload` 分支的功能嫁接到 `dev/v1` 分支，並將整合後的系統從 `dev/v1` 部署到 Render，實現 Agent 自動化與 RAG 功能的深度整合，支持人機協作的智慧任務管理。"
---

## Original Story

本專案旨在將 Agent 自動化與 RAG (檢索增強生成) 功能深度整合到 endUser-ui 中，實現人機協作的智慧任務管理。

**Phase 3.8 總目標**: 將 `feature/e2e-file-upload` 分支的功能嫁接到 `dev/v1` 分支後，將整合後的系統從 `dev/v1` 部署到 Render。

## Story Metadata

**Story Type**: Feature
**Estimated Complexity**: High
**Primary Systems Affected**: `enduser-ui-fe`, `archon-server`, `archon-mcp`, `archon-agents`, `archon-ui-main`, Supabase Database, Render Deployment Infrastructure

---

## CONTEXT REFERENCES

- `TODO.md` - 詳細的專案藍圖，包含 Phase 3.8 的詳細規劃與時序圖。
- `CONTRIBUTING_tw.md` - 提供部署標準作業流程 (SOP) 和環境設定細節，對於部署至 Render 至關重要。
- `GEMINI.md` - 記錄了專案開發過程中的關鍵學習與偵錯模式，可作為解決潛在問題的參考。

---

## IMPLEMENTATION TASKS

### Guidelines for Tasks

- We are using Information dense keywords to be specific and concise about implementation steps and details.
- The tasks have to be detailed and specific to ensure clarity and accuracy.
- The developer who will execute the tasks should be able to complete the task using only the context of this file, with references to relevant codebase paths and integration points.

### Phase 3.8.1: 奠定 `dev/v1` 的基礎架構

#### COPY `docker-compose.yml`:
- FROM: `feature` 分支的 `docker-compose.yml`
- TO: `dev/v1` 分支的根目錄
- GOAL: 採用 `feature` 分支更先進的 Docker 服務編排，包含 `profiles` 設定。
- VALIDATE: `diff docker-compose.yml <feature_branch_docker-compose.yml>` (manual check for content equivalence)

#### COPY `Makefile`:
- FROM: `feature` 分支的 `Makefile`
- TO: `dev/v1` 分支的根目錄
- GOAL: 採用 `feature` 分支修復且功能更強大的 `Makefile`，使用 `pnpm` 並修復測試指令。
- VALIDATE: `diff Makefile <feature_branch_Makefile>` (manual check for content equivalence)

#### COPY `.github/workflows/ci.yml`:
- FROM: `feature` 分支的 `.github/workflows/ci.yml`
- TO: `dev/v1` 分支的根目錄
- GOAL: 採用 `feature` 分支完整可用的前端測試配置，使用 `pnpm`。
- VALIDATE: `diff .github/workflows/ci.yml <feature_branch_ci.yml>` (manual check for content equivalence)

#### COMMIT 基礎架構檔案:
- ACTION: 提交這些基礎架構檔案，建立一個穩定的起點。
- VALIDATE: `git log -1` to confirm commit message and changes.

### Phase 3.8.2: 整合 `archon-ui-main` (管理後台)

#### UPDATE `archon-ui-main/package.json`:
- BASE: 以 `dev/v1` (即 `main`) 分支的 `archon-ui-main/package.json` 為基礎。
- ACTION: 將 `feature` 分支中已修復的 `test: "vitest run"` 指令，手動更新至該檔案。
- GOAL: 整合 Admin UI，保留其最新外觀，同時修復其 CI 問題。
- VALIDATE: `cd archon-ui-main && pnpm test` should pass.

#### COMMIT Admin UI 的變更:
- ACTION: 提交 Admin UI 的變更。
- VALIDATE: `git log -1` to confirm commit message and changes.

### Phase 3.8.3: 移植 `enduser-ui-fe` (使用者介面)

#### COPY `enduser-ui-fe` 目錄:
- FROM: `feature` 分支的 `enduser-ui-fe` 整個目錄。
- TO: `dev/v1` 分支的根目錄。
- GOAL: 將「人機協作」的核心前端完整地移植過來。
- VALIDATE: `ls enduser-ui-fe` should show the copied directory structure.

#### COMMIT 全新的 `enduser-ui-fe` 服務:
- ACTION: 提交這個全新的服務。
- VALIDATE: `git log -1` to confirm commit message and changes.

### Phase 3.8.4: 整合後端服務

#### BASE `python/pyproject.toml`:
- BASE: 以 `dev/v1` 的 `python/pyproject.toml` 為基礎 (使用較新的 `crawl4ai` 版本)。
- ACTION: 系統性地移植 `feature` 分支 `python/src/server/` 目錄下的新服務與 API 變更。
- GOAL: 整合 `feature` 分支的後端業務邏輯，嫁接到 `dev/v1` 的後端框架上。
- VALIDATE: `make test-be` should pass.

#### EXECUTE 測試修復計畫:
- ACTION: 執行所有必要的測試修復，確保 `make test-be` 可以 100% 通過。
- DETAILS: 參考 `TODO.md` 中 4.4.1 至 4.4.4 的解決方案。
- VALIDATE: `make test-be` must pass.

### Phase 3.8.5: 整合資料庫遷移

#### COPY `migration` 目錄:
- FROM: `feature` 分支的 `migration` 目錄。
- TO: `dev/v1` 分支的根目錄。
- GOAL: 確保 `dev/v1` 擁有完整、正確的資料庫結構。
- VALIDATE: `ls migration` should show the copied directory structure.

#### COMMIT 新的資料庫遷移腳本:
- ACTION: 提交新的資料庫遷移腳本。
- VALIDATE: `git log -1` to confirm commit message and changes.

### Phase 3.8.6: 同步文件與最終狀態

#### COPY `CONTRIBUTING_tw.md`:
- FROM: `feature` 分支的 `CONTRIBUTING_tw.md`。
- TO: `dev/v1` 分支的根目錄。
- GOAL: 確保所有文件都反映專案的最終狀態。
- VALIDATE: `diff CONTRIBUTING_tw.md <feature_branch_CONTRIBUTING_tw.md>` (manual check for content equivalence)

#### COMMIT `TODO.md` (包含新計畫):
- ACTION: 將這份包含新計畫的 `TODO.md` 提交。
- VALIDATE: `git log -1` to confirm commit message and changes.

#### COPY `GEMINI.md`:
- FROM: `feature` 分支的 `GEMINI.md`。
- TO: `dev/v1` 分支的根目錄。
- GOAL: 確保所有文件都反映專案的最終狀態。
- VALIDATE: `diff GEMINI.md <feature_branch_GEMINI.md>` (manual check for content equivalence)

### Phase 3.8.7: 修正架構違規並完成手動測試

#### FIX 後端服務啟動問題:
- GOAL: 解決 `archon-mcp` 和 `archon-agents` 的啟動失敗問題。
- SOLUTION: 參考 `git show 6f79c43` 透過解除服務耦合進行修復。
- VALIDATE: `make dev-docker` and ensure all backend services start correctly.

#### FIX 前端 `archon-ui-main` 啟動問題:
- GOAL: 解決 `archon-ui-main` 的啟動失敗問題。
- SOLUTION: 參考 `GEMINI.md` 於 2025-10-27 的日誌，移除無用的「殭屍檔案」(`useThemeAware.ts`) 及其錯誤引用。
- VALIDATE: `cd archon-ui-main && pnpm run dev` should start the UI without errors.

### Phase 3.8.8: 修正種子資料遺漏導致的 404 錯誤

#### VERIFY `migration/seed_mock_data.sql`:
- GOAL: 確認 `PROJECTS_ENABLED` 和 `STYLE_GUIDE_ENABLED` 的 `INSERT` 語句已存在於 `migration/seed_mock_data.sql`。
- ACTION: 若不存在，則手動添加。
- VALIDATE: `grep -q "PROJECTS_ENABLED" migration/seed_mock_data.sql`

#### EXECUTE 資料庫重建流程:
- ACTION: 手動執行資料庫重建流程 (`RESET_DB.sql` -> `seed_mock_data.sql`)，確保種子資料被正確應用。
- VALIDATE: `make dev-docker` 進行最終驗證，確認沒有 404 錯誤。

### Phase 3.8.9: 部署至 Render (Deployment to Render)

#### CREATE Render 服務:
- GOAL: 在 Render 上為所有服務 (`archon-server`, `archon-mcp`, `archon-agents`, `archon-ui-main`, `enduser-ui-fe`) 建立對應的服務。
- ACTION: 根據 `TODO.md` 中的「部署偵錯日誌與解決方案總結」來配置建置指令、環境變數和重寫規則。
- VALIDATE: Render 服務成功部署。

#### CONFIGURE Render 路由:
- ACTION: 在 Render 儀表板上為 SPA 前端服務設定正確的兩條重寫規則（API 代理和 SPA 回退），順序至關重要。
- VALIDATE: 存取前端服務的公開網址，進行功能驗證。

#### PUSH 至遠端觸發部署:
- ACTION: 將 `dev/v1` 推送至遠端，觸發 Render 自動部署。
- VALIDATE: Render 儀表板顯示部署成功。

#### VERIFY 部署後驗證:
- ACTION: 監控 Render 部署日誌，存取後端 `/health` 端點，並進行前端功能驗證。
- VALIDATE: 後端回傳 `{"status":"ok"}`，前端功能正常。

---

## Validation Loop

### Level 1: Syntax & Style (Immediate Feedback)

```bash
# Run after each file creation - fix before proceeding
ruff check src/{new_files} --fix     # Auto-format and fix linting issues
mypy src/{new_files}                 # Type checking with specific files
ruff format src/{new_files}          # Ensure consistent formatting

# Project-wide validation
ruff check src/ --fix
mypy src/
ruff format src/

# Expected: Zero errors. If errors exist, READ output and fix before proceeding.
```

### Level 2: Unit Tests (Component Validation)

```bash
# Test each component as it's created
uv run pytest src/services/tests/test_{domain}_service.py -v
uv run pytest src/tools/tests/test_{action}_{resource}.py -v

# Full test suite for affected areas
uv run pytest src/services/tests/ -v
uv run pytest src/tools/tests/ -v

# Coverage validation (if coverage tools available)
uv run pytest src/ --cov=src --cov-report=term-missing

# Expected: All tests pass. If failing, debug root cause and fix implementation.
```

### Level 3: Integration Testing (System Validation)

```bash
# Service startup validation
uv run python main.py &
sleep 3  # Allow startup time

# Health check validation
curl -f http://localhost:8000/health || echo "Service health check failed"

# Feature-specific endpoint testing
curl -X POST http://localhost:8000/{your_endpoint} \
  -H "Content-Type: application/json" \
  -d '{"test": "data"}' \
  | jq .  # Pretty print JSON response

# MCP server validation (if MCP-based)
# Test MCP tool functionality
echo '{"method": "tools/call", "params": {"name": "{tool_name}", "arguments": {}}}' | \
  uv run python -m src.main

# Database validation (if database integration)
# Verify database schema, connections, migrations
psql $DATABASE_URL -c "SELECT 1;" || echo "Database connection failed"

# Expected: All integrations working, proper responses, no connection errors
```

### Level 4: Creative & Domain-Specific Validation

You can use CLI that are installed on the system or MCP servers to extend the validation and self closing loop.

Identify if you are connected to any MCP servers that can be used for validation and if you have any cli tools installed on the system that can help with validation.

For example:

```bash
# MCP Server Validation Examples:

# Playwright MCP (for web interfaces)
playwright-mcp --url http://localhost:8000 --test-user-journey

# Docker MCP (for containerized services)
docker-mcp --build --test --cleanup

# Database MCP (for data operations)
database-mcp --validate-schema --test-queries --check-performance
```

---

## COMPLETION CHECKLIST

- [X] All tasks completed
- [X] Each task validation passed
- [X] Full test suite passes
- [X] No linting errors
- [X] All available validation gates passed
- [X] Story acceptance criteria met

---

## Notes

All tasks in this PRP are derived from the `TODO.md` file, which documents the successful completion of Phase 3.8.
This document serves as a more formal and structured representation of that completed work.

<!-- EOF -->
