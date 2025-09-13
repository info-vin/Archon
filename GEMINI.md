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
- **流程優化專家 (Process Improvement Expert)**

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

- **策略重新校準與文件驅動開發 (2025-09-12)**:
  - **核心問題**: 意識到先前的計畫過於專注分支合併，而忽略了「端對端功能驗證」的核心目標。直接合併 `spike` 與 `feature` 分支存在巨大風險。
  - **關鍵發現 1 (分支衝突)**: `spike` 分支與 `feature/gemini-log-api` 分支在資料庫遷移腳本 (`migration/`) 上存在嚴重分歧。
  - **關鍵發現 2 (部署經驗)**: 過去的後端部署日誌顯示，**手動執行資料庫遷移**是服務能成功啟動的關鍵前置步驟。
  - **關鍵發現 3 (前端測試)**: 對 `spike` 分支的調查顯示，`archon-ui-main` 的大型測試集 (如 `pages.test.tsx`) 已不存在，因此前端測試效能並非當前在此分支上的問題。
  - **最終決策**: 暫停所有合併活動。轉向「文件驅動」的「先驗證，再規劃」模式。所有文件更新將在 `spike/verify-deployment-pipeline` 分支上進行，以其作為建立端對端測試環境的基礎。
  - **產出**:
    1. 更新 `AGENTS.md`，加入「端對端思維」原則。
    2. 更新 `CONTRIBUTING_tw.md`，提供包含前後端的完整部署 SOP。
    3. 更新 `TODO.md`，將 `Phase 2.6` 調整為「程式碼驗證與測試計畫」，`Phase 2.7` 調整為「建立端對端功能驗證環境」。
    4. 將此結論與發現記錄於 `GEMINI.md`。

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

- **開發流程優化與核心問題聚焦 (2025-09-13)**:
  - **背景**: 本次會話旨在完成 Phase 2.8 的功能整合與測試，但過程中暴露出我對專案目標理解不清、計畫脫離現實、且未能有效學習歷史教訓等根本性問題。
  - **過程與決策**:
    1.  **目標重新校準**: 在使用者反覆提醒下，最終澄清了當前的核心目標前端是 `enduser-ui-fe`，而非 `archon-ui-main`，解決了計畫始終偏離軌道的核心原因。
    2.  **前端功能完善**: 澄清目標後，我們聚焦於 `enduser-ui-fe`，透過 `msw` 模擬後端，成功地在隔離環境中驗證、修復並完善了「附件」功能的 UI 顯示與下載行為。
    3.  **根本性障礙識別**: 透過對歷史日誌和 `spike` 分支的分析，我們再次確認了「資料庫遷移腳本衝突」是阻礙任何真實端對端測試的根本性障礙。
    4.  **資料庫衝突解決**: 遵從使用者「理解意圖而非機械合併」的指導，我們分析了各資料表與 UI 的對應關係，並以可部署的 `spike` 分支為基準，成功將 `feature` 分支的變更整合，建立了一個統一、乾淨的 `000_unified_schema.sql`。
    5.  **文件與流程重構**:
        - **歸檔經驗**: 遵從使用者指示，將本次會話中學到的「警惕副本任務」、「驗證而非假設」等核心開發心法，整理並歸檔至 `CONTRIBUTING_tw.md`。
        - **重構藍圖**: 全面重構了 `TODO.md`，正式結束了 2.6, 2.7, 2.8 等歷史階段，並建立了清晰的 **Phase 2.9**，其核心任務就是我們剛剛完成的「資料庫衝突修復」以及後續的「端對端整合測試」。
  - **結論**: 經過一次漫長但極富成效的深度對話，我們不僅完成了前端功能的整合，更重要的是，理清了專案的核心障礙、優化了開發流程文件，並為下一階段的真實測試鋪平了道路。