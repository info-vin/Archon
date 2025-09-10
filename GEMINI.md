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

- **部署管道驗證成功 (2025-09-10)**:
  - **任務**: 成功完成 `spike/verify-deployment-pipeline` 任務，驗證了後端服務在 Render 平台上的部署流程。
  - **環境修復**: 解決了首次部署時遇到的五大設定問題（Dockerfile 路徑、根目錄、啟動指令、Port 綁定、健康檢查寬限期）。
  - **產出**: 相關的除錯經驗與最佳實踐，已作為「Render 部署除錯實戰指南」歸檔至 `CONTRIBUTING_tw.md`，為未來的穩定部署奠定基礎。

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
