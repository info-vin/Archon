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

- **RBAC 功能完成**: 後端已完成基於角色的存取控制 (RBAC) 的核心功能，包含了 `GET /api/assignable-users` 端點以及在任務建立/更新時的權限驗證。
- **跨平台開發規範建立**: 解決了因 `uv.lock`、`package-lock.json` 和 `Makefile` 語法導致的跨平台（macOS vs Windows）開發問題。相關的最佳實踐與結論已整理並歸檔至 `CONTRIBUTING_tw.md` 的「後端依賴與環境管理」和「前端測試實踐」章節，作為所有開發者應遵循的規範。
- **目前開發焦點**: 根據 `TODO.md`，下一個主要開發任務為「核心 API 擴充 (Core API)」，為任務添加附件 (attachments) 功能，以及相關的 Agent 工具開發。