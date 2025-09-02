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

## uv.lock and Makefile Debugging Log (2025/09/02)

This section documents the debugging process for a series of failures related to `uv.lock` and the `Makefile` on Windows, and the conclusions drawn from it.

### Initial Problem

The backend tests (`make test-be`) were failing due to issues with the `torch` dependency. The errors were different on different platforms:
*   **macOS:** `torch` did not have a compatible wheel for `macosx_13_0_x86_64`.
*   **Windows (Python 3.13):** The pinned version `torch==2.2.0` was not compatible with Python 3.13.

This indicated that pinning the `torch` dependency in `pyproject.toml` was not a viable long-term solution for cross-platform development.

### Investigation and Resolution

1.  **Transitive Dependency:** We confirmed that `torch` was not a direct dependency of our application code, but a transitive dependency of `sentence-transformers`.
2.  **Removing Pinned Dependency:** The `torch` dependency was removed from `pyproject.toml`.
3.  **Regenerating `uv.lock`:** The `python/uv.lock` file was deleted to allow `uv` to resolve a compatible version of `torch` for the current platform.
4.  **`pytest-mock` not found:** After regenerating the lock file, the tests failed again with `fixture 'mocker' not found`. This was because `pytest-mock` is an optional dependency for testing and was not being installed by the default `uv sync` command.
5.  **Incorrect `uv` syntax:** An attempt to fix this by adding `uv sync --with test` to the `Makefile` failed because `--with` is not a valid flag for `uv sync`.
6.  **Correct `uv` syntax:** The correct flag `--extra` was identified.
7.  **`Makefile` issues on Windows:** The `make` command on Windows was failing to parse comments correctly, leading to errors.
8.  **Final `Makefile` fix:** The `Makefile` was corrected to use `uv sync --extra test` for `test-be` and `uv sync --extra dev` for `lint-be`, and the comments were removed to avoid parsing issues with `make` on Windows.

### Key Takeaways and Recommendations

*   **Avoid Pinning Platform-Specific Dependencies:** For libraries like `torch` that have different builds for different platforms and Python versions, avoid pinning them directly in `pyproject.toml`. Let the package manager resolve the correct version.
*   **Add `uv.lock` to `.gitignore`:** To prevent cross-platform conflicts with lock files, `python/uv.lock` should be added to `.gitignore`. This allows each developer to have a lock file that is specific to their environment.
*   **Explicit Dependency Installation in `Makefile`:** The `Makefile` should be explicit about installing dependencies for different tasks. The `test-be` and `lint-be` targets were updated to run `uv sync --extra <group>` before executing the tests or linter. This ensures that the correct dependencies are always installed.
