---
name: "Phase 5.3: Data Integrity & RBAC Alignment Fix"
description: "Fix data inconsistencies between seed data and RBAC matrix, and solve the 'ghost account' issue in auth.users."
status: "In Progress"
started_at: "2026-01-12"
dependencies: ["Phase 5.2"]
---

## 1. 核心問題與數據分析 (Core Issues & Data Analysis)

經過 `git log` 分析、Log 查證與架構審查，我們確認了導致 End-User UI (5173) 登入失敗的根本原因。

### 1.1 現狀數據分析 (Current Data State)

| 組件 | 狀態 | 證據/詳情 | 影響 |
| :--- | :--- | :--- | :--- |
| **Profile Data** | ✅ 正確 | `seed_mock_data.sql` 已更新 (Alice=Sales, Charlie=Manager)。 | DB 中的角色定義正確。 |
| **Auth Account** | ⚠️ 存在但脫節 | `init_db.py` 報錯 `already registered`。 | 帳號存在但密碼未知，且 Metadata 滯後。 |
| **Metadata** | 🔴 **未同步** | 舊帳號的 `user_metadata` 缺少 `role` 欄位。 | **關鍵失效點**: 5173 前端依賴 JWT 中的 Metadata 判斷權限。 |
| **ID Mismatch** | 🔴 **潛在風險** | Profile ID 可能為文字 (如 `'2'`)，而 Auth ID 必為 UUID。 | 若直接用 Profile ID 更新 Auth，可能導致 `User not found` 錯誤。 |
| **DB 連線** | 🔴 受限 | `psycopg2` 連線失敗 (Supavisor 限制/密碼錯誤)。 | 必須依賴 API 模式進行修復 (Strategy A)。 |

### 1.2 根本原因 (Root Cause)
1.  **Metadata 缺失**: 5173 需要 JWT 內含 `role` 才能放行，但目前的 `init_db.py` 未同步 Metadata。
2.  **邏輯漏洞**: 腳本遇到重複帳號時選擇 `pass`。
3.  **ID 匹配風險**: 腳本假設 Profile ID == Auth User ID，這在 Mock Data 混用文字 ID 與 UUID 的情況下不可靠。

## 2. 修復計畫 (Remediation Plan - Strategy A)

**Strategy A**: Bypass DB connection issues and focus on robust API-based synchronization.

### 2.1 Refined Implementation (`scripts/init_db.py`)
**Goal**: Perform a **Full Sync** (Password + Metadata) for existing users via Supabase Admin API, handling ID resolution correctly.

**Logic Change**:
在 `sync_profiles_to_auth` 函式中，當捕獲 `already registered` 異常時：
1.  **Resolve Auth ID**: 不直接使用 Profile ID。先呼叫 `supabase.auth.admin.list_users()` (或過濾查詢) 透過 `email` 找到正確的 **Auth User UUID**。
2.  **Full Update**: 呼叫 `update_user_by_id(auth_user_id, payload)`。
    *   Payload: `password="password123"`, `email_confirm=True`, `user_metadata={"name":..., "role":...}`。
3.  **Logging**: 記錄明確的成功訊息。

### 2.2 Infrastructure Fix (`Makefile`) - [已完成]
- [x] **Dependency**: Add `--group server` to `uv sync`.
- [x] **Env Vars**: Inject `SUPABASE_SERVICE_KEY` and `SUPABASE_DB_URL`.

## 3. 驗收標準 (Acceptance Criteria) - Step-by-Step

### Step 1: 執行修復腳本
執行指令：
```bash
make db-init
```

**驗收檢查點 (Checklist)**:
- [ ] **API Mode Active**: Log 顯示 `Fetching profiles via Supabase HTTP API...`。
- [ ] **ID Resolution**: Log 顯示類似 `🔍 Resolved Auth ID for alice@archon.com: <UUID>` (證明 ID 查找邏輯生效)。
- [ ] **Update Success**: Log 顯示 `✅ Updated existing user: alice@archon.com (Role: member)`。
- [ ] **No Crash**: 腳本完整執行完畢，顯示 `✅ Auth Sync Complete.`。

### Step 2: 前端登入驗證 (End-User UI - Port 5173)
打開瀏覽器訪問 `http://localhost:5173`。

**驗收檢查點 (Checklist)**:
- [ ] **Login Success**: 使用 `alice@archon.com` / `password123` 登入，無紅字錯誤。
- [ ] **Redirect**: 成功跳轉至 `/dashboard` 或首頁。
- [ ] **Role Verification**:
    - 右上角頭像顯示 Alice 的名字。
    - 側邊欄顯示 "Sales" 相關功能 (如 `Leads`, `Stats`)。
    - **關鍵**: 不應出現 "Permission Denied" 或 "403" 畫面。

## 4. Revised Data Specification

| Persona | Name | Role | Dept | Agent ID (if applicable) | Password |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **Admin** | Admin User | `system_admin` | IT | - | `password123` |
| **Manager** | Charlie Brown | `manager` | Marketing | - | `password123` |
| **Sales** | Alice Johnson | `member` | Sales | - | `password123` |
| **Marketing** | Bob Williams | `member` | Marketing | - | `password123` |