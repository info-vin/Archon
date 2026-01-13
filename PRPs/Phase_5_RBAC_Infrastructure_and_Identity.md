---
name: "Phase 5: RBAC Infrastructure & Identity Unification (權限架構與身份統一總結報告)"
description: "整合 Phase 5.1, 5.2, 5.3 的完整實作紀錄。從零建立後端權限驗證機制、修復管理員能力，並確保資料庫身分的一致性。"
status: "Completed"
period: "2026-01-08 to 2026-01-13"
---

## 1. 專案摘要 (Executive Summary)

### 👨‍💼 給非技術夥伴的白話文說明 (For Non-Tech Colleagues)

在 Phase 5 之前，我們的系統像是一個「榮譽商店」——我們相信使用者會在前台 (Frontend) 乖乖遵守規則，但後台 (Backend) 其實沒有嚴格檢查他們的識別證。這導致了幾個具體的痛點：

1.  **虛設的安檢**：之前只要在瀏覽器修改一下 Header，任何人都能偽裝成 Admin。這就像是只要戴上「警衛」的帽子，就能隨意進出金庫。
2.  **無力的管理員**：真正的管理員想要把 Alice 從「業務」升遷為「經理」時，系統卻報錯 (500 Error)，因為後台根本不認識「更改角色」這個指令。此外，當 Bob 離職後，管理員竟然無法刪除他留下的過時文章，因為系統堅持「只有作者本人能刪除」。
3.  **幽靈人口**：系統裡的 Alice 和 Bob 只是為了展示用的「假人 (Mock Data)」。當我們試著讓真正的 Alice 登入時，她會被系統踢出來 (406 Error)，因為她手上的身分證號碼 (Auth UUID) 和人事資料庫裡的號碼 (Profile ID) 對不上。

**Phase 5 的完成意味著：**
我們建立了一套嚴格的數位安檢系統 (RBAC)。現在，每一次資料請求都必須經過權限中心核對。管理員擁有了真正的實權，可以調動人事、管理所有內容。同時，Alice 和 Bob 已經從「假人」變成了擁有真實帳號、密碼且資料同步的「合法公民」。

---

## 2. 核心目標 (Core Goals)

| 代號 | 目標描述 | 交付成果 (Deliverables) |
| :--- | :--- | :--- |
| **5.1** | **管理員賦能** | 修復 Admin API，允許變更使用者 `role` 與跨使用者編輯 Blog。 |
| **5.2** | **權限基礎建設** | 建立 `src/server/auth` (後端) 與 `src/features/auth` (前端)，移除不安全的 `X-User-Role` Header。 |
| **5.3** | **資料完整性** | 實作「雙重同步策略 (Dual Sync)」，解決 Auth UUID 與 Profile ID 不一致導致的 406 錯誤。 |

---

## 3. 開發歷程與實作細節 (Implementation Timeline & Details)

### Phase 5.1: 管理員權限補強 (Admin Capability)

**核心任務**: 解決管理員「看得到動不了」的權限缺失問題。

*   **後端修改**:
    *   `settings_api.py`: 更新 `AdminUserProfileUpdate` Pydantic 模型，新增 `role` 欄位，解決 API 接收參數時的驗證錯誤。
    *   `rbac_service.py`: 重寫權限檢查邏輯 (Override Logic)。當操作者角色為 `system_admin` 時，程式會主動跳過「資源擁有權檢查 (Ownership Check)」，允許刪除非本人建立的資源。
*   **前端修改**:
    *   `BlogDetailPage.tsx`: 修正條件渲染邏輯。原先僅檢查 `isAuthor`，現在改為 `isAuthor || isAdmin`，讓管理員能看到編輯與刪除按鈕。

### Phase 5.2: RBAC 基礎設施 (Infrastructure Build)

**核心任務**: 建立標準化的權限驗證流水線，取代散亂的邏輯。

*   **Backend (Python)**:
    *   **新建** `src/server/auth/` 模組：
        *   `service.py`: 封裝 Supabase Auth API，負責處理 Token 驗證與使用者資訊獲取。
        *   `dependencies.py`: 實作 FastAPI 的 `Depends` 函式 (如 `get_current_user`, `require_admin`)，作為 API 的守門員。
        *   `permissions.py`: 定義角色權限矩陣 (Role-Permission Matrix)。
    *   **關鍵技術**: 實作 `get_current_user` 函式，解析 HTTP Header 中的 `Authorization: Bearer <token>`，驗證 JWT 合法性。
    *   **Dev Experience**: 新增 `POST /api/auth/dev-token`，讓開發者在本地環境能一鍵取得 Admin 權限 Token。
*   **Frontend (React)**:
    *   **新建** `src/features/auth/` 模組：
        *   `AuthContext.tsx`: 管理全域登入狀態與 Token 儲存。
        *   `usePermission.ts`: 提供 `hasPermission('manage_users')` 等 Hook 供元件使用。
        *   `PermissionGuard.tsx`: 用於保護路由 (Route) 的高階元件 (HOC)。
    *   **UI 整合**: 修改 `Sidebar`，將導航連結分為 `common`, `manager`, `admin` 三類，根據使用者權限動態渲染。

### Phase 5.3: 資料完整性修復 (Data Integrity Fix)

**核心任務**: 解決真實登入時的「身分證號不符」問題 (406 Error)。

*   **問題描述**: 當前端呼叫 `/profiles` 查詢個人資料時，會使用登入後的 Auth UUID (例如 `a1b2...`) 去查詢資料庫。但 Mock Data 建立的 Profile ID 是寫死的字串 (例如 `user-alice`)。查詢不到資料導致前端崩潰。
*   **解決方案**: **雙重同步策略 (Dual Sync Strategy)**
    *   修改 `scripts/init_db.py` 的 `sync_profiles_to_auth` 函式：
    *   **同步 A (Metadata)**: 在建立或更新 Auth 帳號時，強制將 `role` 寫入 User Metadata，確保 Token 內含權限資訊。
    *   **同步 B (ID Alignment)**: 當偵測到 Email 已存在時，執行 SQL `UPDATE profiles SET id = auth_uuid WHERE email = ...`。這是一個關鍵的手術，直接將資料庫中的舊 ID 替換為正確的 Auth UUID。

---

## 4. 驗收標準與測試結果 (Acceptance Criteria & Verification)

本章節對應第 3 章的三個開發階段，逐項列出驗收結果。

### ✅ Phase 5.1 驗收 (管理員能力)
- [x] **Role Update**: Admin 在 User Management 頁面將 User A 的角色改為 `manager`，API 回傳 200 OK，資料庫更新成功。
- [x] **Blog Override**: Admin 進入 User B 撰寫的文章頁面，能看到「刪除」按鈕，並能成功刪除文章。

### ✅ Phase 5.2 驗收 (權限基建)
- [x] **Secure API**: 使用 Postman 發送未帶 Token 的請求至 `/api/users`，後端正確回傳 `401 Unauthorized` (不再接受 `X-User-Role` 偽造)。
- [x] **Dev Login**: 開發環境啟動前端時，系統自動呼叫 `/api/auth/dev-token` 並成功登入為 Admin，無需手動輸入。
- [x] **Sidebar Logic**:
    - 以 `sales` 角色登入：**看不到** "Admin Panel" 與 "HR Dashboard"。
    - 以 `manager` 角色登入：**看得到** "HR Dashboard" 但看不到 "Admin Panel"。
    - 以 `admin` 角色登入：**看得到** 所有選項。

### ✅ Phase 5.3 驗收 (資料完整性)
- [x] **Script Execution**: 執行 `python scripts/init_db.py`，終端機顯示 `✅ Synced Profile ID for alice@archon.com...`。
- [x] **Real Login**: 使用 `alice@archon.com` / `password123` 在登入頁面成功登入。
- [x] **Profile Access**: 登入後進入 Profile 頁面，能正確顯示 Alice 的頭像與名稱 (代表 `/profiles` API 查詢成功，ID 已對齊)。

---

## 5. 數據規格 (Revised Data Specification)

以下是經 Phase 5.3 修復後，系統中標準化的使用者數據規格。這些帳號現在皆可用於真實登入測試。

| Persona (角色) | Name | Role (權限等級) | Department | Email | Password | 備註 |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **System Admin** | Admin User | `system_admin` | IT | `admin@archon.com` | `password123` | 擁有全系統最高權限 |
| **Manager** | Charlie Brown | `manager` | Marketing | `charlie@archon.com` | `password123` | 可查看團隊績效儀表板 |
| **Sales Rep** | Alice Johnson | `member` | Sales | `alice@archon.com` | `password123` | 負責 Phase 4.2 業務功能測試 |
| **Marketing** | Bob Williams | `member` | Marketing | `bob@archon.com` | `password123` | 負責 Blog 內容測試 |

---

## 6. 技術細節與檔案變更 (Technical Reference)

**關鍵檔案列表**:

| 模組 | 檔案路徑 | 用途 |
| :--- | :--- | :--- |
| **Auth Core** | `python/src/server/auth/service.py` | 封裝 Supabase Auth 操作 (Login, Verify Token)。 |
| **Dependency** | `python/src/server/auth/dependencies.py` | FastAPI `Depends` 函式，用於 API 路由保護。 |
| **Init Script** | `scripts/init_db.py` | 資料庫初始化與 ID 同步邏輯 (**關鍵修復**)。 |
| **Frontend Auth** | `*/src/features/auth/AuthContext.tsx` | 管理前端登入狀態與 Token 儲存。 |
| **Frontend Guard** | `*/src/features/auth/components/PermissionGuard.tsx` | UI 元件級別的權限柵欄。 |

**手動驗證常用指令 (Verification CLI)**:

對於不熟悉 UI 的人員，可使用以下指令確認資料庫同步狀態：

```bash
# A. 驗證 Alice 的 ID 是否已對齊 (Auth UUID vs Profile ID)
docker exec -i supabase-db psql -U postgres -d postgres -c "SELECT email, id FROM public.profiles WHERE email = 'alice@archon.com';"

# B. 驗證 User Metadata 中的 Role 是否正確
# (需手動檢查輸出 JSON 中的 user_metadata 欄位)
docker exec -i supabase-db psql -U postgres -d postgres -c "SELECT email, raw_user_meta_data FROM auth.users WHERE email = 'alice@archon.com';"
```

---

## 7. 下一步 (Next Steps)

隨著基礎設施 (Phase 5) 的完工，系統現在具備了安全的身分驗證地基。接下來將全力推進 **Phase 4.2 (Business Feature Expansion)**，利用這些真實身分來進行：

1.  **Sales Intelligence**: 讓 Alice (Sales) 能使用爬蟲工具收集潛在客戶。
2.  **Market Analysis**: 讓 Bob (Marketing) 能撰寫並發布受權限保護的市場分析報告。

> 此文件取代並歸檔原有的 `Phase_5.1`, `Phase_5.2`, `Phase_5.3` 計畫文件。
