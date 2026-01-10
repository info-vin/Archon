---
name: "Phase 5.2: RBAC Enforcement Infrastructure (權限執行基礎設施)"
description: "基於現況調查，填補前後端 Auth 架構的巨大空白，修復角色漏洞，並實作標準化的 RBAC 執行機制。"
status: "Completed"
completed_at: "2026-01-09"
---

## 1. 核心目標 (Goal)

**Feature Goal**: 從零建立缺失的 `src/server/auth` (後端) 與 `src/features/auth` (前端)，移除不安全的 `X-User-Role` 依賴，並確保系統能精確執行 `RBAC_Collaboration_Matrix.md`。

**Deliverable (交付成果)**:
1.  **Secure Backend Auth**: [x] 建立 `src/server/auth/` 模組，實作 JWT 驗證與 `get_current_user` Dependency。
2.  **Frontend Auth Module (Dual Sync)**: [x] 在 `archon-ui-main` 與 `enduser-ui-fe` 建立相同的 Auth 基礎設施 (`AuthContext`, `usePermission`)。
3.  **Dev Auto-Login**: [x] 實作開發環境自動登入機制，維持 Admin UI 的無感操作體驗 (後端 `/api/auth/dev-token` + 前端 Context 自動獲取)。
4.  **Role Fix**: [x] 修復 `rbac_service.py`，補上缺失的 `Sales` 角色。
5.  **Standardized Enforcement**: [x] 將 `settings_api.py` 等關鍵 API 重構為使用 `Depends(requires_permission)`。
6.  **Navigation RBAC**: [x] 在 `enduser-ui-fe` 實作基於權限的側邊欄導航 (Sidebar)。

---

## 2. 現況與差距分析 (Gap Analysis)

| 構面 | 現況 (As-Is) | 目標 (To-Be) | 差距 | 解決狀態 |
| :--- | :--- | :--- | :--- | :--- |
| **後端 Auth 目錄** | `python/src/server/auth` 不存在 | 目錄存在且包含 `dependencies.py` | **Missing Directory** | **已建立** |
| **前端 Auth 目錄** | `src/features/auth` 不存在 | 在兩個前端專案中都存在 | **Missing Directory** | **已移植** |
| **Admin UI 登入** | 無登入頁面，依賴 Header | 自動獲取 Dev Token，無感登入 | **UX/Security Gap** | **已實作** |
| **End-User UI 導航** | 硬編碼顯示所有連結 | 根據 `usePermission` 動態隱藏 | **UX/Security Gap** | **已整合** |
| **API 驗證** | 部分 API 依賴前端傳來的 `X-User-Role` | 僅信任 Supabase JWT Token (`Authorization: Bearer`) | **Security Risk** | **已移除** |

---

## 3. 實作藍圖 (Implementation Blueprint)

### 3.1 Backend Implementation (Python/FastAPI)

*   **Task 1: 建立 Auth 基礎設施 (Create Auth Infrastructure)** (Completed)
    *   [x] 建立 `python/src/server/auth/` 模組。
    *   [x] 實作 `get_user_from_token` 與 `dependencies.py`。

*   **Task 2: 定義權限與依賴 (Define Permissions & Dependencies)** (Completed)
    *   [x] 實作 `permissions.py` 與 `ROLE_PERMISSIONS` 字典。

*   **Task 3: 開發環境自動登入 (Dev Auto-Login API)** (Completed)
    *   [x] 實作 `POST /api/auth/dev-token`。

*   **Task 4: 重構關鍵 API (Refactor APIs)** (Completed)
    *   [x] 重構 `settings_api.py` 使用 `Depends(get_current_admin)`。
    *   [x] 修復 `rbac_service.py` 加入 Sales 角色。

### 3.2 Frontend Implementation (React)

*   **Task 1: 建立 Admin UI Auth (archon-ui-main)** (Completed)
    *   [x] 建立 `features/auth`模組。
    *   [x] 實作 `AuthContext` (Dev Auto-Login) 與 `apiClient` 整合。

*   **Task 2: 移植 End-User UI Auth (enduser-ui-fe)** (Completed)
    *   [x] **Action**: 將 `archon-ui-main/src/features/auth` 複製到 `enduser-ui-fe/src/features/auth`。
    *   [x] **Adaptation**: 調整 `usePermission` 以使用現有的 `useAuth`，並擴充 `src/types.ts` 中的 `EmployeeRole` Enum。
    *   [x] **Action**: 修改 `MainLayout` (Sidebar)，使用 `usePermission` 隱藏無權限連結。
    *   [x] **Action**: 修改 `App.tsx` 與 `MarketingPage`/`StatsPage`，使用 `PermissionGuard` 保護路由與內容。

---

## 4. 手動驗證協議 (Manual Verification Scripts)

請複製以下 Shell 指令並在終端機執行，以驗證資料庫狀態：

### 流程 A：驗證角色變更 (Verify Role Change)
**操作**: 在 `localhost:3737` 變更員工角色後執行。
```bash
# 預期輸出: role 應更新為您設定的新角色 (如 manager)
docker exec -i supabase-db psql -U postgres -d postgres <<EOF
SELECT email, role FROM public.profiles WHERE email = 'alice@archon.com';
EOF
```

### 流程 B：驗證密碼更新 (Verify Password Update)
**操作**: 在 `localhost:5173` 更新密碼後執行。
```bash
# 預期輸出: updated_at 應顯示為剛剛的操作時間
docker exec -i supabase-db psql -U postgres -d postgres <<EOF
SELECT email, updated_at FROM auth.users WHERE email = 'alice@archon.com';
EOF
```

### 流程 C：驗證導航權限 (Navigation Check)
*   **Sales (Alice)**: 登入後應看到側邊欄有 "Market Intel"，無 "Admin Panel"。
*   **Manager (Charlie)**: 登入後應看到 "HR Dashboard" (全隊數據) 與 "Approvals"。

---

## 5. 實作細節與設計決策 (Design Decisions)

*   **不開發 Admin 登入頁面**: 為了維持極致的 DX (開發者體驗)，我們在開發環境使用 `dev-token` 機制實現無感登入，而非強迫開發者手動登入。
*   **數據透明度 vs 隱私**: 在 `StatsPage` 中，我們決定讓所有員工都能看到「團隊任務狀態分佈」，但「成員個人績效」僅限 Manager 以上可見。
*   **路徑別名限制**: 由於 `enduser-ui-fe` 目前不支持 `@` 路徑別名，所有移植的 Auth 元件皆使用相對路徑 (`../../`) 以確保編譯成功。
