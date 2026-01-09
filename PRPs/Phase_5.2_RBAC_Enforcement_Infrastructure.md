---
name: "Phase 5.2: RBAC Enforcement Infrastructure (權限執行基礎設施)"
description: "基於現況調查，填補前後端 Auth 架構的巨大空白，修復角色漏洞，並實作標準化的 RBAC 執行機制。"
---

## 1. 核心目標 (Goal)

**Feature Goal**: 從零建立缺失的 `src/server/auth` (後端) 與 `src/features/auth` (前端)，移除不安全的 `X-User-Role` 依賴，並確保系統能精確執行 `RBAC_Collaboration_Matrix.md`。

**Deliverable (交付成果)**:
1.  **Secure Backend Auth**: 建立 `src/server/auth/` 模組，實作 JWT 驗證與 `get_current_user` Dependency。
2.  **Frontend Auth Module**: 建立 `archon-ui-main/src/features/auth`，實作 `AuthContext`, `useAuth`, `usePermission`。
3.  **Role Fix**: 修復 `rbac_service.py`，補上缺失的 `Sales` 角色。
4.  **Standardized Enforcement**: 將 `settings_api.py` 等關鍵 API 重構為使用 `Depends(requires_permission)`。
5.  **Automated Verification**: 透過 `make test-be` 與 `make test-fe` 自動驗證權限邏輯。

---

## 2. 現況與差距分析 (Gap Analysis)

| 構面 | 現況 (As-Is) | 目標 (To-Be) | 差距 |
| :--- | :--- | :--- | :--- |
| **後端 Auth 目錄** | `python/src/server/auth` 不存在 | 目錄存在且包含 `dependencies.py` | **Missing Directory** |
| **前端 Auth 目錄** | `src/features/auth` 不存在 | 目錄存在且包含 Context/Hooks | **Missing Directory** |
| **API 驗證** | 部分 API 依賴前端傳來的 `X-User-Role` | 僅信任 Supabase JWT Token (`Authorization: Bearer`) | **Security Risk** |
| **角色定義** | `rbac_service.py` 缺少 `Sales` | 包含 `Sales`, `Marketing`, `Manager` | **Logic Bug** |
| **前端 RBAC** | 邏輯分散/不存在 | 統一使用 `usePermission` Hook 與 `PermissionGuard` | **Tech Debt** |

---

## 3. 實作藍圖 (Implementation Blueprint)

### 3.1 Backend Implementation (Python/FastAPI)

*   **Task 1: 建立 Auth 基礎設施 (Create Auth Infrastructure)**
    *   **Action**: 建立 `python/src/server/auth/` 目錄與 `__init__.py`。
    *   **File**: `python/src/server/auth/utils.py`
        *   實作 `verify_token(token: str)`：使用 `python-jose` 解析 JWT，驗證簽名。
    *   **File**: `python/src/server/auth/dependencies.py`
        *   實作 `get_current_user`：從 Header 解析 Token，查詢 DB 確認 User 狀態，回傳 User 物件 (含 Role)。
        *   實作 `get_current_admin`：基於 `get_current_user`，額外檢查 Role 是否為 Admin。

*   **Task 2: 定義權限與依賴 (Define Permissions & Dependencies)**
    *   **File**: `python/src/server/auth/permissions.py`
        *   定義 Scope 常數：`TASK_CREATE`, `CODE_APPROVE`, `LEADS_VIEW` 等。
        *   定義 `ROLE_PERMISSIONS` 字典：映射 Role -> Scopes (包含補上 `Sales` 的權限)。
    *   **Update**: `python/src/server/auth/dependencies.py`
        *   實作 `requires_permission(scope: str)` Dependency。

*   **Task 3: 重構關鍵 API (Refactor APIs)**
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
    *   新增 `tests/server/auth/test_dependencies.py`: 測試 `verify_token` 與 `requires_permission`。
    *   新增 `tests/server/api_routes/test_settings_api_rbac.py`: 測試 Alice 呼叫 Admin API 回傳 403。

2.  **Frontend Unit Tests (`make test-fe`)**:
    *   新增 `src/features/auth/hooks/tests/usePermission.test.ts`: 測試不同 Role 的權限判斷邏輯。

---

## 4. 執行順序 (Execution Order)

1.  **Backend Infra**: Create `auth/` directory & `dependencies.py` (填補真空).
2.  **Backend Logic**: Update `rbac_service.py` & `permissions.py` (修復邏輯).
3.  **Backend Refactor**: Secure `settings_api.py` (消除隱患).
4.  **Backend Test**: Run `make test-be` to verify API security.
5.  **Frontend Infra**: Create `features/auth` structure & Context.
6.  **Frontend Logic**: Implement `usePermission` & `PermissionGuard`.
7.  **Frontend Test**: Run `make test-fe` to verify UI logic.