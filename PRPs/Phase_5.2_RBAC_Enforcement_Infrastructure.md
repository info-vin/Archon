---
name: "Phase 5.2: RBAC Enforcement Infrastructure (權限執行基礎設施)"
description: "基於現況調查，填補前後端 Auth 架構的巨大空白，修復角色漏洞，並實作標準化的 RBAC 執行機制。"
---

## 1. 核心目標 (Goal)

**Feature Goal**: 從零建立缺失的 `src/server/auth` (後端) 與 `src/features/auth` (前端)，移除不安全的 `X-User-Role` 依賴，並確保系統能精確執行 `RBAC_Collaboration_Matrix.md`。

**Deliverable (交付成果)**:
1.  **Secure Backend Auth**: 建立 `src/server/auth/` 模組，實作 JWT 驗證與 `get_current_user` Dependency。
2.  **Frontend Auth Module**: 建立 `archon-ui-main/src/features/auth`，實作 `AuthContext`, `useAuth`, `usePermission`。
3.  **Dev Auto-Login**: 實作開發環境自動登入機制，維持 Admin UI 的無感操作體驗。
4.  **Role Fix**: 修復 `rbac_service.py`，補上缺失的 `Sales` 角色。
5.  **Standardized Enforcement**: 將 `settings_api.py` 等關鍵 API 重構為使用 `Depends(requires_permission)`。
6.  **Automated Verification**: 透過 `make test-be` 與 `make test-fe` 自動驗證權限邏輯。

---

## 2. 現況與差距分析 (Gap Analysis)

| 構面 | 現況 (As-Is) | 目標 (To-Be) | 差距 |
| :--- | :--- | :--- | :--- |
| **後端 Auth 目錄** | `python/src/server/auth` 不存在 | 目錄存在且包含 `dependencies.py` | **Missing Directory** |
| **前端 Auth 目錄** | `src/features/auth` 不存在 | 目錄存在且包含 Context/Hooks | **Missing Directory** |
| **Admin UI 登入** | 無登入頁面，依賴 Header | 自動獲取 Dev Token，無感登入 | **UX/Security Gap** |
| **API 驗證** | 部分 API 依賴前端傳來的 `X-User-Role` | 僅信任 Supabase JWT Token (`Authorization: Bearer`) | **Security Risk** |
| **角色定義** | `rbac_service.py` 缺少 `Sales` | 包含 `Sales`, `Marketing`, `Manager` | **Logic Bug** |
| **前端 RBAC** | 邏輯分散/不存在 | 統一使用 `usePermission` Hook 與 `PermissionGuard` | **Tech Debt** |

---

## 3. 實作藍圖 (Implementation Blueprint)

### 3.1 Backend Implementation (Python/FastAPI)

*   **Task 1: 建立 Auth 基礎設施 (Create Auth Infrastructure)**
    *   **Action**: 建立 `python/src/server/auth/` 目錄與 `__init__.py`。
    *   **File**: `python/src/server/auth/utils.py`
        *   實作 `get_user_from_token(token)`：呼叫 Supabase Auth API 驗證 Token。
    *   **File**: `python/src/server/auth/dependencies.py`
        *   實作 `get_current_user`：解析 Token，查詢 DB 確認 User 狀態與 Role。
        *   實作 `get_current_admin`：基於 `get_current_user`，強制檢查 Admin Role。

*   **Task 2: 定義權限與依賴 (Define Permissions & Dependencies)**
    *   **File**: `python/src/server/auth/permissions.py`
        *   定義 Scope 常數與 `ROLE_PERMISSIONS` 字典。
    *   **Update**: `python/src/server/auth/dependencies.py`
        *   實作 `requires_permission(scope: str)` Dependency。

*   **Task 3: 開發環境自動登入 (Dev Auto-Login API)**
    *   **File**: `python/src/server/api_routes/auth_api.py`
        *   **Action**: 新增 `POST /api/auth/dev-token`。
        *   **Logic**: 僅在非 Production 環境下，使用 `service_role` 簽發一個臨時的 Admin JWT Token 回傳給前端。這解決了 Admin UI 無法登入的問題。

*   **Task 4: 重構關鍵 API (Refactor APIs)**
    *   **File**: `python/src/server/api_routes/settings_api.py`
        *   移除 `X-User-Role` Header 依賴。
        *   全面改用 `Depends(get_current_admin)` 或 `Depends(requires_permission('USER_MANAGE'))`。
    *   **File**: `python/src/server/services/rbac_service.py`
        *   補完 `permissions` 字典，加入 `"Sales": ["MarketBot"]` 等規則。

### 3.2 Frontend Implementation (React)

*   **Task 1: 建立 Auth Feature (Create Auth Feature)**
    *   **Action**: 建立 `archon-ui-main/src/features/auth/{components,hooks,types,contexts}` 目錄結構。
    *   **File**: `src/features/auth/types/index.ts` (定義 User, Role, Permission)。
    *   **File**: `src/features/auth/contexts/AuthContext.tsx` (管理 User State)。
        *   **Logic**: `useEffect` 啟動時呼叫 `/api/auth/dev-token`，取得 Token 後注入 `apiClient` 並設定 User State。

*   **Task 2: 權限 Hook (usePermission)**
    *   **File**: `src/features/auth/hooks/usePermission.ts`
    *   **Logic**:
        1.  從 `useAuth` 取得 `user.role`。
        2.  對照前端的 `ROLE_PERMISSIONS` (需與後端保持同步)。
        3.  回傳 `hasPermission(scope)` 函式。

*   **Task 3: 權限守衛元件 (PermissionGuard)**
    *   **File**: `src/features/auth/components/PermissionGuard.tsx`
    *   **Logic**: 遵循 UI_STANDARDS，無權限則回傳 `null`。

### 3.3 Automated Verification Strategy (自動化驗收策略)

1.  **Backend Unit Tests (`make test-be`)**:
    *   測試 `get_current_user` 能正確拒絕無效 Token。
    *   測試 `dev-token` 端點存在且能回傳 Token。
2.  **Frontend Unit Tests (`make test-fe`)**:
    *   測試 `AuthContext` 能正確處理 Token 獲取失敗的情況 (顯示 Error 而非白屏)。

---

## 4. 執行順序 (Execution Order)

1.  **Backend Infra**: Create `auth/` directory & `dependencies.py` (已完成).
2.  **Backend Dev API**: Implement `POST /api/auth/dev-token`.
3.  **Backend Logic**: Update `rbac_service.py` & `permissions.py` (已完成).
4.  **Backend Refactor**: Secure `settings_api.py` (已完成).
5.  **Backend Test**: Run `make test-be` (已完成).
6.  **Frontend Infra**: Create `features/auth` structure & Context (進行中).
7.  **Frontend Logic**: Implement `usePermission` & `PermissionGuard`.
8.  **Frontend Test**: Run `make test-fe` to verify UI logic.
