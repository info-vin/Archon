# Gemini 專案背景指令 (Project Briefing for Gemini)

在新對話開始時，請先讀取此檔案中列出的文件，以快速了解專案的背景、規範與當前狀態。

## 必讀文件列表 (Must-Read File List)

1.  **`TODO.md`**: 了解整體的開發藍圖與當前的任務進度。
2.  **`CONTRIBUTING_tw.md`**: 了解詳細的開發流程、測試規範以及常見問題的解決方案。
3.  **`Makefile`**: 了解專案定義的標準指令 (例如 `make test-fe`, `make dev` 等)。
4.  **`docker-compose.yml`**: 了解專案的微服務架構以及它們之間的關係。
5.  **`docs/docs/database-design-philosophy.mdx`**: 了解資料庫「聚合模型」的設計理念。

## Gemini Added Memories

- **Current Development Context (2025/09/02):**
  - **RBAC Feature:** Completed backend implementation of Role-Based Access Control (RBAC), including `GET /api/assignable-users` endpoint, server-side validation in `create_task` and `update_task` APIs. `TODO.md` has been updated to reflect this completion.
  - **`seed_mock_data.sql`:** Updated to align mock user roles with RBAC specification and `AGENTS.md` (e.g., "Market Researcher" role added).
  - **`CONTRIBUTING_tw.md`:** Code snippet formatting fixed.
  - **Current Blocker - `torch` Dependency Issue:**
    - `make test-be` and `make lint-be` commands are failing due to `torch` dependency installation error.
    - Error: `torch` (versions 2.7.0, 2.8.0) does not have a compatible wheel for `macosx_13_0_x86_64`.
    - This is a platform-specific issue with `uv`'s dependency resolution.
    - **Attempted Fix:**
      1.  Deleted `python/uv.lock`.
      2.  Modified `python/pyproject.toml` to explicitly add `torch==2.2.0` (found to be compatible with Python 3.12 and macOS x86_64).
      3.  Attempted to run `cd python && uv sync` to regenerate `uv.lock` and install dependencies, but the command is currently stuck/not returning output.
    - **Next Steps for `torch` issue:** Need to resolve the `uv sync` command not returning output.
  - **Next Feature (Blocked):** "核心 API 擴充 (Core API)" - adding attachments support to tasks. This is blocked by the `torch` dependency issue.
  - **Long-term Prevention for `uv.lock`:** Proposed to add `python/uv.lock` to `.gitignore` to prevent future cross-platform issues. This is pending resolution of the current `uv sync` issue.