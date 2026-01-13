---
name: "Phase 5.3: Data Integrity & RBAC Alignment Fix"
description: "Fix data inconsistencies between seed data and RBAC matrix, and solve the 'ghost account' issue in auth.users."
status: "Completed"
started_at: "2026-01-12"
completed_at: "2026-01-13"
dependencies: ["Phase 5.2"]
---

## 1. 核心問題與數據分析 (Core Issues & Data Analysis)
(已歸檔)

## 2. 實作結果 (Implementation Results)

### 2.1 雙重同步策略 (Dual Sync Strategy)

我們最終採用了 **Strategy A + B** 的混合策略，成功解決了所有問題：

1.  **Strategy A (Metadata Sync)**:
    -   透過 `init_db.py` 偵測重複使用者 (Handle 422/Already Registered)。
    -   強制更新 Auth User 的 Metadata (`role`, `name`)，確保 JWT 包含權限資訊。

2.  **Strategy B (ID Alignment - 關鍵修復)**:
    -   **發現**: 前端出現 `406 Not Acceptable` 錯誤。
    -   **原因**: 前端使用 Auth UUID 查詢 `profiles` 表，但 Mock Data 的 Profile ID 與 Auth UUID 不一致。
    -   **解法**: 在 `init_db.py` 中，當偵測到重複使用者時，執行 `UPDATE profiles SET id = auth_uuid WHERE email = ...`。
    -   **安全性**: 經查證 Schema，`profiles` 表無 FK 依賴，此操作是安全的。

### 2.2 程式碼改進
-   **init_db.py**: 加入了強健的錯誤判定邏輯 (同時檢查 Status Code 422 與關鍵字)，並實作了上述的 ID 同步邏輯。
-   **auth_service.py**: 優化了日誌輸出，壓制了預期內的 "Already Registered" Traceback，保持終端機整潔。

## 3. 驗收標準 (Acceptance Criteria) - 測試紀錄

### Step 1: 執行修復腳本
- [x] **API Mode Active**: 成功連線至 Supabase Cloud。
- [x] **Auth Sync**: Log 顯示 `✅ Updated existing user: alice@archon.com`。
- [x] **ID Sync**: Log 顯示 `✅ Synced Profile ID for alice@archon.com to match Auth UUID`。

### Step 2: 前端登入驗證 (End-User UI)
- [x] **Login Success**: Alice 成功登入。
- [x] **No 406 Error**: Profile API 請求成功 (因為 ID 已對齊)。
- [x] **Role Verification**: 成功進入 Dashboard 並看到 Sales 相關功能。

## 4. Revised Data Specification

| Persona | Name | Role | Dept | Agent ID (if applicable) | Password |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **Admin** | Admin User | `system_admin` | IT | - | `password123` |
| **Manager** | Charlie Brown | `manager` | Marketing | - | `password123` |
| **Sales** | Alice Johnson | `member` | Sales | - | `password123` |
| **Marketing** | Bob Williams | `member` | Marketing | - | `password123` |