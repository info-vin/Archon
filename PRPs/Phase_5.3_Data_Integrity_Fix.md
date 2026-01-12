---
name: "Phase 5.3: Data Integrity & RBAC Alignment Fix"
description: "Fix data inconsistencies between seed data and RBAC matrix, and solve the 'ghost account' issue in auth.users."
status: "In Progress"
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
- [ ] **Dependency**: Add `--group server` to `uv sync` to ensure `supabase` package is installed.
- [ ] **Env Vars**: Add `--env-file ../.env` to `uv run` to inject `SUPABASE_SERVICE_KEY`.
- [ ] **Python Path**: Set `PYTHONPATH=.` to allow importing `src.server` from `scripts/`.

### 2.2 Update Seed Data (`seed_mock_data.sql`)
**Goal**: Align database data with `RBAC_Collaboration_Matrix.md`.
- [ ] **Alice**: Role -> `member` (Dept: Sales).
- [ ] **Charlie**: Role -> `manager` (Dept: Engineering -> Marketing).
- [ ] **Agents**: Add `DevBot`, `Librarian`, `Clockwork` with correct IDs and `ai_agent` role.

### 2.3 Implement Auth Sync (`scripts/init_db.py`)
**Goal**: Programmatically sync `public.profiles` to `auth.users`.
- [ ] **Import**: Import `AuthService` from `src.server.services.auth_service`.
- [ ] **Logic**:
    1. After SQL migrations, initialize `AuthService`.
    2. Fetch all profiles from DB.
    3. Loop through each profile:
       - Check if `auth.users` record exists.
       - If missing, call `auth_service.create_user_by_admin(email, password="password123", ...) `.
       - Log success/failure.

### 2.4 Verification SOP

**Step 1: 執行初始化**
```bash
make db-init
```

**Step 2: 驗證資料庫狀態 (Run in terminal)**
> 使用 `archon-server` 容器內的 Python 環境連接資料庫進行驗證，以避開本地環境差異。

```bash
docker exec -i archon-server python -c "
import os
import psycopg2
# Use SUPABASE_DB_URL from container env
conn = psycopg2.connect(os.environ['SUPABASE_DB_URL'])
cur = conn.cursor()

print('\n--- 1. Checking Profiles (Should align with Matrix) ---')
cur.execute(\"SELECT name, role, department FROM profiles WHERE name IN ('Charlie Brown', 'Alice Johnson');\")
for row in cur.fetchall():
    print(f'User: {row[0]}, Role: {row[1]}, Dept: {row[2]}')

print('\n--- 2. Checking Auth Users (Should not be empty) ---')
cur.execute(\"SELECT email, created_at FROM auth.users WHERE email IN ('admin@archon.com', 'alice@archon.com', 'market.bot@archon.com');\")
results = cur.fetchall()
print(f'Found {len(results)} auth users.')
for row in results:
    print(f'Email: {row[0]}')
"
```

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