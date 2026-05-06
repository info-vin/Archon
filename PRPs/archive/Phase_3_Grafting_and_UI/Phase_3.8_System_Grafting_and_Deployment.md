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

---

# Appendix: Historical Lessons & Environment Analysis (歷史教訓與環境分析)

> **Note**: This section was migrated from `CONTRIBUTING_tw.md` to preserve the historical context of system decisions made during the grafting phase.

## 1. 重要架構決策與歷史紀錄 (Key Architectural Decisions & History)

### 2025-10-07: 首次部署的歷史調查
- **情境**: 為了釐清首次部署時，為何 `enduser-ui-fe` 成功，而 `archon-ui-main` 失敗。
- **調查結論**: 兩個獨立事件同時發生：
    1.  **成功的 `enduser-ui-fe`**: 當時的部署目標只有 `enduser-ui-fe`。雖然遇到了 `pnpm-lock.yaml` 缺失的問題（並透過 `--no-frozen-lockfile` 臨時繞過），但最終成功部署並設定了正確的 API URL。
    2.  **失敗的 `archon-ui-main`**: `archon-ui-main` 的程式碼當時寫死了一個已被後端重構移除的 API 端點 (`/api/projects/health`)，導致其本地和線上都無法連線，這與部署流程本身無關。
- **確立原則**: 此調查確立了在除錯時，必須區分「部署流程問題」與「應用程式自身 Bug」的重要性。

### 2025-09-30: Render 部署流程確立
- **情境**: 在部署演練中，`git push render` 指令失敗，回報 `repository not found`。
- **決策理由**: 經查證，Render 提供的 URL 是一個「Deploy Hook」，只能被 `curl` 等工具觸發，而不能作為 Git remote。因此，專案的部署流程**不應**使用 `git push render`。
- **確立原則**: 確立了正確的部署流程：將程式碼 `push` 到 Render 所監控的 `origin` (GitHub) 分支，依靠 Render 的 GitHub App 自動觸發部署。

### 2025-09-29: `Makefile` 意圖的最終仲裁
- **情境**: `make test` 指令緩慢且包含所有前後端測試，與 `ci.yml` 中僅測試後端的行為產生矛盾。
- **決策理由**: 直接修改 `Makefile` 是危險的。透過 `git log -p -- Makefile` 深入分析提交歷史，發現開發者曾短暫嘗試過快慢測試分離，但很快就手動還原了該修改。這證明了 `make test` 的「緩慢但完整」是**刻意為之**的選擇。
- **確立原則**: 當文件、程式碼、CI/CD 腳本之間出現矛盾時，`git log -p` 是揭示真實意圖的最終仲裁者。

### 2025-09-27: 測試背景任務的 API
- **情境**: 為 `/documents/upload` 這個啟動背景任務的端點編寫單元測試時，不知如何斷言。
- **決策理由**: 單元測試應專注於被測單元的「職責」，而非其「依賴的實作細節」。此端點的職責是「接收請求並正確啟動任務」，而不是「完成任務」。
- **確立原則**: 確立了測試此類端點的最佳實踐：模擬 (Mock) `asyncio.create_task` 本身，並驗證它是否被以正確的參數呼叫。測試中出現的 `RuntimeWarning: coroutine ... was never awaited` 是此策略下預期內且無害的副作用。

### 2025-09-23: 「自動修復」的陷阱
- **情境**: 執行 `make lint-be` 驗證程式碼，卻導致大量不相關的檔案被自動修改，汙染了工作區。
- **決策理由**: 閱讀 `Makefile` 後發現，`lint-be` 指令包含了 `--fix` 參數，使其從一個「檢查工具」變成了「修改工具」。
- **確立原則**: 確立了處理此類工具的安全工作流程：「先用唯讀模式 (`ruff check`) 分析 -> 將所有修改一次性用 `write_file` 寫入 -> 最後再用原指令 (`make lint-be`) 進行純粹的驗證」。

### 2025-09-22: `Makefile` 與 `pyproject.toml` 的矛盾
- **情境**: `make test-be` 失敗，因為 `Makefile` 中的 `uv sync --extra` 指令與 `pyproject.toml` 的 `[dependency-groups]` 結構不符。
- **決策理由**: 透過 `git log -p -- Makefile` 追溯歷史，發現專案曾刻意選擇 `[dependency-groups]` 結構，從而確認了 `Makefile` 需要被修正以使用 `--group` 參數，而不是反過來修改 `pyproject.toml`。
- **確立原則**: 再次印證了「追溯 `git log` 以理解歷史意圖」的重要性。

### 2025-12-27: 合併後完整性驗證的重要性
- **情境**: 將一個修復 E2E 測試的 `fix/...` 分支合併回 `feature/...` 分支後，儘管程式碼邏輯正確，但 CI/CD 流程中的 `lint` 和 `test` 檢查依然失敗。
- **決策理由**: 調查發現，合併後產生了新的、非程式碼邏輯的錯誤，包括 `import` 語句遺漏和 Lint 格式問題。這證明了即使是看似安全的合併，也可能引入預期外的副作用。
- **確立原則**: 在任何 `git merge` 或 `git cherry-pick` 操作完成後，**必須**立即在本地執行完整的、端到端的驗證流程（至少包含 `make lint` 和 `make test`）。這確保了程式碼的「邏輯正確性」和「工程完整性」都得到保障，避免將破碎的提交推送到遠端。

### 2025-09-27: 後端端到端 (E2E) Agent 工作流測試模式
- **情境**: 需要為一個完整的、非同步的「AI as a Teammate」工作流（從 API 觸發到 Agent 回呼）建立一個可靠的後端整合測試。
- **決策理由**: 此類測試的挑戰在於，它跨越多個非同步服務和 API 回呼，直接測試的複雜度和不穩定性都很高。因此，需要一個清晰、可重複的模式來模擬工作流的各個階段。
- **確立原則**: 確立了後端 E2E Agent 工作流的測試模式，其核心要素包括：
    1.  **遵循服務模擬黃金模式**: 使用 `setup_module` 在 `app` 導入前 `patch` 核心的 `AgentService`。
    2.  **分階段驗證**: 測試必須清晰地分為三個階段：
        *   **任務指派**: 呼叫 `POST /api/tasks`，並斷言 `agent_service.run_agent_task` 被 `await`。
        *   **模擬 Agent 回呼**: Mock `run_agent_task` 的實作，讓它使用 `TestClient` 反向呼叫 `archon-server` 的狀態更新和結果回傳 API（`/api/tasks/{id}/agent-status` 和 `/api/tasks/{id}/agent-output`）。
        *   **結果驗證**: 斷言 `task_service` 的相應方法被正確呼叫，以確認回呼已成功觸發了核心業務邏輯。

### 2025-09-21: 資料庫腳本的冪等性
- **情境**: 執行資料庫遷移腳本 `000_unified_schema.sql` 時，因 `policy ... already exists` 錯誤而中斷。
- **決策理由**: 遷移腳本的穩定性與可重複執行性，比微不足道的效能更重要。
- **確立原則**: 所有資料庫遷移腳本都必須具備「冪等性」。對於不支援 `CREATE ... IF NOT EXISTS` 的物件（如 `POLICY`），在 `CREATE` 之前必須先使用 `DROP ... IF EXISTS`。

### 2025-09-19: `Makefile` 作為單一事實來源
- **情境**: 專案中的 `README.md` 記載了與 `Makefile` 不一致的啟動指令，導致開發者遵循文件操作時發生錯誤。
- **決策理由**: 可執行的腳本是指令的最終真理，文件應作為其說明而存在。
- **確立原則**: 確立了 `Makefile` 作為所有專案指令的「單一事實來源」。所有 `.md` 文件在指導操作時，都應引用 `make <command>`，而不是複製貼上其底層指令。

## 2. 系統比較分析 (System Comparison Analysis)

### `make dev` vs `make dev-docker` 比較分析

這份表格是基於對 `Makefile` 內容的直接分析得出的「單一事實」。

| 特性 | `make dev` (混合開發) | `make dev-docker` (全 Docker 開發) | 差異原因分析 |
| :--- | :--- | :--- | :--- |
| **啟動模式** | 混合模式 | 全 Docker 模式 | `dev` 模式旨在為前端開發提供最佳體驗，因此只在 Docker 中運行後端，而在本地直接運行前端以利用熱重載(Hot Reload)功能。`dev-docker` 則模擬一個更接近生產的環境，所有服務都在 Docker 容器中運行。 |
| **Docker Profiles** | `--profile backend --profile agents` | `--profile backend --profile frontend --profile enduser --profile agents` | `dev` 模式只啟動後端相關的 `backend` 和 `agents` profiles。`dev-docker` 額外啟動了 `frontend` (archon-ui-main) 和 `enduser` (enduser-ui-fe) 兩個前端 profile，將它們也容器化。 |
| **前端服務** | 在本地主機上通過 `pnpm run dev` 啟動 `archon-ui-main`。 | `archon-ui-main` 和 `enduser-ui-fe` 都在 Docker 容器內運行。 | `dev` 模式讓前端開發者可以直接在本地編輯器中修改程式碼，並立即在瀏覽器中看到結果，無需重新建置 Docker 映像。`dev-docker` 則將前端作為獨立的容器化服務來管理。 |
| **`enduser-ui-fe`** | **不啟動** | 在 Docker 容器內啟動 | `dev` 模式的設計目標是專注於 `archon-ui-main` (管理後台) 的開發，因此沒有包含 `enduser-ui-fe`。而 `dev-docker` 則會啟動包括 `enduser-ui-fe` 在內的所有服務。 |
| **主要用途** | 專注於**管理後台 (`archon-ui-main`)** 的前端開發，同時需要後端 API 支持。 | 進行**全系統整合測試**，或當開發者不需要頻繁修改前端程式碼，只想啟動一個完整的、隔離的本地環境時使用。 | 兩種模式為不同的開發場景提供了優化。`dev` 專注於效率，`dev-docker` 專注於環境一致性。 |


<!-- EOF -->
