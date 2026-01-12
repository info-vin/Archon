---
name: "Phase 5.3: Data Integrity & RBAC Alignment Fix"
description: "Fix data inconsistencies between seed data and RBAC matrix, and solve the 'ghost account' issue in auth.users."
status: "Completed"
started_at: "2026-01-12"
dependencies: ["Phase 5.2"]
---

## 1. 核心問題 (Core Issues)

經過 `git log` 分析、文件比對與環境風險評估，發現以下嚴重問題：

1.  **RBAC 角色過時**: `seed_mock_data.sql` 中的 Alice 仍為 `project_manager` (舊)，Charlie 為 `member` (舊)。實際上應分別為 `Sales` (Employee) 與 `Manager`。
2.  **Agent 缺失**: `RBAC_Collaboration_Matrix.md` 定義了 4 個 Agents，但資料庫僅有 1 個舊的 `Market Researcher`。
3.  **幽靈帳號 (Ghost Accounts)**: `seed_mock_data.sql` 僅寫入 `public.profiles`，未寫入 `auth.users`。
4.  **執行環境缺失 (Environment Gap)**: `make db-init`目前未加載 `.env`，未安裝 `server` 依賴群組，且未設定 `PYTHONPATH`，導致無法執行 Python 層級的 Auth 同步。
5.  **驗證工具缺失**: `docker-compose.yml` 顯示無本地 DB 容器，資料庫為外部依賴 (Supabase Local)。不能使用 `docker exec supabase-db`。

## 2. 修復計畫 (Remediation Plan)

### 2.1 Infrastructure Fix (`Makefile`)
**Goal**: Prepare the environment for `init_db.py` to import `src` and call Supabase APIs.
- [x] **Dependency**: Add `--group server` to `uv sync` to ensure `supabase` package is installed.
- [x] **Env Vars**: Add `--env-file ../.env` to `uv run` to inject `SUPABASE_SERVICE_KEY`.
- [x] **Python Path**: Set `PYTHONPATH=.` to allow importing `src.server` from `scripts/`.
- [x] **Docker Integration**: Updated `docker-compose.yml` to mount `scripts/` and `migration/`, and pass `SUPABASE_DB_URL` correctly.

### 2.2 Update Seed Data (`seed_mock_data.sql`)
**Goal**: Align database data with `RBAC_Collaboration_Matrix.md`.
- [x] **Alice**: Role -> `member` (Dept: Sales).
- [x] **Charlie**: Role -> `manager` (Dept: Engineering -> Marketing).
- [x] **Agents**: Add `DevBot`, `Librarian`, `Clockwork` with correct IDs and `ai_agent` role.
- [x] **Conflict Resolution**: Updated SQL to use `ON CONFLICT (email)` or subquery-based IDs to prevent unique constraint violations.

### 2.3 Implement Auth Sync (`scripts/init_db.py`)
**Goal**: Programmatically sync `public.profiles` to `auth.users`.
- [x] **Import**: Import `AuthService` from `src.server.services.auth_service`.
- [x] **Logic**:
    1. After SQL migrations, initialize `AuthService`.
    2. Fetch all profiles from DB (or API if DB fails).
    3. Loop through each profile:
       - Check if `auth.users` record exists.
       - If missing, call `auth_service.create_user_by_admin(email, password="password123", ...) `.
       - Log success/failure.
- [x] **Robustness**: Implemented **API Fallback** strategy. If `psycopg2` fails to connect (e.g. due to Supavisor Circuit Breaker), the script falls back to fetching profiles via Supabase HTTP API to ensure Auth Sync still completes.

### 2.4 Verification SOP

**Step 1: 執行初始化**
```bash
make db-init
```
> **Note**: Due to Supavisor connection limits/circuit breakers on the free tier, SQL migrations might be skipped in the script. In such cases, run `migration/seed_mock_data.sql` manually in the Supabase Dashboard SQL Editor. The script *will* handles Auth Sync via HTTP API automatically.

**Step 2: 自動化驗證 (Automated Verification)**
```bash
make verify-data
```
> Replaced manual `docker exec` with a robust python script `scripts/verify_seed.py` that checks both DB integrity and Auth consistency.

**Step 3: 功能驗證 (Login Test)**
- Open `http://localhost:5173`
- Login as Alice (`alice@archon.com` / `password123`) -> Should succeed and see Sales view.
- Login as Admin (`admin@archon.com` / `password123`) -> Should succeed and see Admin view.

## 4. Revised Data Specification

| Persona | Name | Role | Dept | Agent ID (if applicable) | Password |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **Admin** | Admin User | `system_admin` | IT | - | `password123` |
| **Manager** | Charlie Brown | `manager` | Marketing | - | `password123` |
| **Sales** | Alice Johnson | `member` | Sales | - | `password123` |
| **Marketing** | Bob Williams | `member` | Marketing | - | `password123` |
| **Agent** | DevBot | `ai_agent` | AI | `agent-dev-001` | (API Key Only) |
| **Agent** | MarketBot | `ai_agent` | AI | `agent-mr-001` | (API Key Only) |
| **Agent** | Librarian | `ai_agent` | AI | `agent-lib-001` | (API Key Only) |
| **Agent** | Clockwork | `ai_agent` | AI | `agent-sys-001` | (API Key Only) |