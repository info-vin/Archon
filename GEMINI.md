# Gemini 專案背景指令 (Project Briefing for Gemini)

在新對話開始時，請先讀取此檔案中列出的文件，以快速了解專案的背景、規範與當前狀態。

## 必讀文件列表 (Must-Read File List)

1.  **`TODO.md`**: 了解整體的開發藍圖與當前的任務進度。
2.  **`CONTRIBUTING.md`**: 了解英文版的開發流程與標準。
3.  **`CONTRIBUTING_tw.md`**: 了解詳細的開發流程、測試規範以及常見問題的解決方案。
4.  **`Makefile`**: 了解專案定義的標準指令 (例如 `make test-fe`, `make dev` 等)。
5.  **`docker-compose.yml`**: 了解專案的微服務架構以及它們之間的關係。
6.  **`docs/docs/database-design-philosophy.mdx`**: 了解資料庫「聚合模型」的設計理念。

## Core Principles & Workflow

- **Understand First**: Before implementing, thoroughly understand the use case and requirements. Use file reading and search tools to analyze existing code.
- **Follow Conventions**: Strictly adhere to the project's existing coding styles, naming conventions, and architectural patterns.
- **Plan and Confirm**: For complex tasks, propose a clear, step-by-step plan and await user confirmation before proceeding.
- **Verify Changes**: After making changes, run relevant tests (`make test-be`, `make test-fe`) and linters to ensure code quality and correctness.
- **Clean Commits**: Prefer to combine small file changes with related feature development into a single, clean commit.

## AI Agent Roles

This project utilizes a team of specialized AI agents. When performing tasks, adopt the appropriate role as defined in `AGENTS.md`:

- **市場研究員 (Market Researcher)**
- **內部知識庫專家 (Internal Knowledge Expert)**
- **系統維護專家 (System Maintenance Expert)**

## Architecture Overview

Archon is a microservices-based knowledge management system:

- **Frontend (`archon-ui-main/`)**: React + TypeScript + Vite + TailwindCSS (Port 3737)
- **Main Server (`python/src/server/`)**: FastAPI with HTTP polling (Port 8181)
- **MCP Server (`python/src/mcp/`)**: Lightweight HTTP-based MCP protocol server (Port 8051)
- **Agents Service (`python/src/agents/`)**: PydanticAI agents for AI/ML operations (Port 8052)
- **Database**: Supabase (PostgreSQL + pgvector)

## Development Commands (via `Makefile`)

- `make dev`: Starts backend services in Docker and frontend locally.
- `make dev-docker`: Starts all services in Docker.
- `make test`: Runs all backend and frontend tests.
- `make test-be`: Runs backend (Python) tests.
- `make test-fe`: Runs frontend (React) tests.
- `make lint-be`: Lints the backend Python code.

## File Organization

- **`python/src/server/services/`**: Core backend business logic.
- **`python/src/server/api_routes/`**: API route handlers.
- **`archon-ui-main/src/components/`**: Reusable UI components.
- **`archon-ui-main/src/pages/`**: Main application pages.
- **`archon-ui-main/src/services/`**: Frontend API communication.
- **`docs/`**: Docusaurus documentation site.
- **`migration/`**: Database migration scripts and seeds.

## Environment Variables

Required in `.env`:

```bash
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_SERVICE_KEY=your-service-key-here
```

## 專案近期動態與結論 (Recent Project Updates & Key Decisions)

- **分支策略與部署流程釐清 (2025-09-12)**:
  - **發現問題**: 經分析，`main` (及其衍生的 `spike` 分支) 與 `feature/gemini-log-api` 分支在**資料庫遷移腳本 (`migration/`)** 上存在嚴重分歧，直接合併風險極高。
  - **核心決策**: 暫停所有分支合併活動。當前最優先任務是**建立一份完整、可驗證的部署標準作業流程 (SOP)**，並將其記錄在預計用於部署的 `spike/verify-deployment-pipeline` 分支上。
  - **產出**:
    1. 在 `spike` 分支上更新 `CONTRIBUTING_tw.md`，包含詳細的後端與前端部署SOP。
    2. 在 `spike` 分支上更新 `TODO.md`，明確標示出 `migration/` 的衝突問題，並將其設為分支合併的前置任務。
    3. 將 `deployment_verification_log.txt` 複製到 `spike` 分支，以保留關鍵的除錯歷史。
    4. 將此結論記錄於 `GEMINI.md`。

- **後端重構 (2025-09-08)**:
  - **RBAC 服務化**: 遵循 Phase 2.5 的規劃，已將分散在 API 路由的權限邏輯，統一遷移至專門的 `RBACService`，提升了程式碼的內聚性與可維護性。
  - **健康檢查整合**: 將分散於 `main.py` 與 `projects_api.py` 的健康檢查邏輯，統一整合至 `HealthService`，並由根目錄的 `/health` 提供單一的系統狀態報告，移除了重複的端點。

- **前端核心功能完成 (2025-09-08)**:
  - **任務附件顯示**: 在 `DashboardPage` 的所有主要視圖（列表、表格、看板）中，成功實作了任務附件的顯示功能，並為此新增了對應的單元測試。
  - **使用者頭像更新**: 成功將 `UserAvatar` 元件整合至 `DashboardPage` 的所有主要視圖中。現在系統能根據使用者角色，正確顯示人類（圓形）和 AI（方形）的頭像，並已完成相關測試。
  - **開發流程學習**: 本次開發過程中的經驗（`write_file` 的重要性、`vi.mock` 的變數提升問題）已被記錄至 `CONTRIBUTING_tw.md`，作為團隊的共享知識。

- **RBAC 功能完成**: 後端已完成基於角色的存取控制 (RBAC) 的核心功能，包含了 `GET /api/assignable-users` 端點以及在任務建立/更新時的權限驗證。
- **前端「任務指派」功能完成**: 已完成與 RBAC 對應的前端「任務指派選單」功能。此過程建立了完整的前端測試模式，包括如何為沒有測試的元件從零開始建立 `msw` API 模擬環境，相關實踐已歸檔至 `CONTRIBUTING_tw.md`。
- **跨平台開發規範建立**: 解決了因 `uv.lock`、`package-lock.json` 和 `Makefile` 語法導致的跨平台（macOS vs Windows）開發問題。相關的最佳實踐與結論已整理並歸檔至 `CONTRIBUTING_tw.md` 的「後端依賴與環境管理」和「前端測試實踐」章節，作為所有開發者應遵循的規範。
- **資料庫遷移與環境除錯 (2025-09-05)**:
  - **任務**: 成功新增 `customers` 與 `vendors` 兩個新的資料表，並完成對應的資料庫遷移腳本 `migration/20250905_add_customers_and_vendors_tables.sql`。
  - **環境修復**: 解決了在 Windows 環境下啟動 Docker 的一系列問題。主要包括：
    - 修正了 `docker-compose.yml` 中網路驅動的拼寫錯誤 (`bridgedge` -> `bridge`)。
    - 透過日誌分析，定位到 `archon-server` 啟動失敗的原因為 `.env` 檔案中 `SUPABASE_URL` 未正確設定，導致 DNS 解析失敗。
    - 記錄了 `Makefile` 在 Windows PowerShell/cmd 環境下的相容性問題，並在檔案中添加了註解。相關解法已歸檔至 `CONTRIBUTING_tw.md`。
- **目前開發焦點**: 根據 `TODO.md`，下一個主要開發任務為前端的「任務附件顯示 (Task Attachments)」與「使用者頭像更新 (User Avatar Update)」。