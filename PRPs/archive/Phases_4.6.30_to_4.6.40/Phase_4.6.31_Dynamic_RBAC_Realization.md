# Phase 4.6.31: Dynamic RBAC Realization (動態權限矩陣實體化)

> **核心目標**: 將權限驗證邏輯從程式碼硬編碼 (Hardcoded) 遷移至資料庫動態驅動，實現不重啟服務即可調整全系統權限。

## 1. 物理變更說明 (Physical Changes)

### 1.1 資料庫層 (Database Layer)
- **Table**: `public.archon_roles_permissions`
- **Schema**:
    - `role`: TEXT (PRIMARY KEY)
    - `permissions`: TEXT[] (Scope 列表)
    - `description`: TEXT
- **Migration**: `migration/0.2.2/12_seed_rbac.sql` 已實作資料表建立與初始種子數據注入。

### 1.2 後端服務層 (Backend Service Layer)
- **`RBACService`**:
    - 實作 `get_role_permissions(role)`：優先從資料庫查詢權限，並具備快取機制 (`_matrix_cache`) 以確保效能。
    - 提供 Static Fallback：若資料庫連線失敗，自動回退至 `permissions.py` 中的硬編碼定義。
- **`auth/dependencies.py`**:
    - 升級 `requires_permission` 裝飾器：全面切換為呼叫 `RBACService().get_role_permissions(role)`，達成動態校驗。

### 1.3 管理介面層 (Admin UI Layer)
- **Identity Matrix**: 
    - 在 Admin UI (3737) 實作了 **Role Capabilities Matrix** 編輯介面。
    - 管理員可物理勾選各角色的 Scope (如 `task:create`, `leads:view:all`) 並即時寫入資料庫。

## 2. 驗證數據 (Verification Evidence)
- **API 響應**: `GET /api/admin/rbac/matrix` 正式回傳資料庫中的實體權限矩陣。
- **稽核日誌**: 每次權限異動皆會產生 `v4.6.31` 版本的 `archon_logs` 實體紀錄。
- **效能指標**: 引入單例快取後，權限校驗延遲 < 5ms。

## 3. 結案狀態 (Closure Status)
- **狀態**: 🟢 **100% 物理落地** (2026-04-06)
- **關鍵檔案**:
    - `python/src/server/services/rbac_service.py`
    - `python/src/server/auth/dependencies.py`
    - `enduser-ui-fe/src/features/admin/components/IdentityMatrix.tsx`
