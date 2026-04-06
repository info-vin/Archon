# Phase 4.6.30: RBAC Enforcement & Scope Refinement (權限外掛化與 Scope 精煉)

## 1. 專案背景 (Project Context)
在 Phase 4.6.29 達成全系統 `0.2.2` 對齊後，系統的地基已穩固。然而，目前的 RBAC 執行邏輯（特別是「部門隔離」）仍散落在 API 路由層 (`projects/core.py`)，而非由 `RBACService` 集中管理。這導致了代碼重複且難以維護。

## 2. 核心目標 (Core Objectives)
1. **權限外掛化 (Scope Mounting)**: 將 `projects/core.py` 中的端點與 `permissions.py` 中的細粒度 Scope 正式掛鉤。
2. **邏輯封裝 (Logic Encapsulation)**: 將 API 層的手寫角色判斷 (`if u_role not in ["admin"]`) 物理轉移至 `RBACService`。
3. **部門隔離硬化 (Department Isolation)**: 確保 `GET /projects` 自動根據使用者的 `department` 欄位進行物理過濾。

## 3. 具體修改計畫 (Implementation Steps)

### 3.1 `rbac_service.py` 功能擴充
**目標**: 新增 `scope_projects_query` 方法，封裝部門隔離邏輯。

**修改方案**:
- **File**: `python/src/server/services/rbac_service.py`
- **邏輯**: 若使用者非 Admin，自動回傳適合其部門的過濾條件。

### 3.2 `projects/core.py` 權限外掛
**目標**: 移除 API 層的 Role 寫死邏輯。

**修改範圍**:
- `GET /projects`: 掛載 `TASK_READ_TEAM` 或 `TASK_READ_ALL` (由 `requires_permission` 管理)。
- `GET /projects/{project_id}`: 使用 `RBACService` 進行實體權限校驗。

## 4. 物理基準驗證 (Verification Protocols)
1. **測試重啟**: 修改後重跑 `make test-be` (基準：555 PASSED)。
2. **專項稽核**: 針對 `test_phase49_rbac_service.py` 執行負面測試，確認非管理員無法越權存取其他部門專案。

## 5. 修改預覽 (Non-Fantasy Preview)
此計畫嚴禁修改現有的資料庫 Schema 或 ENUM 定義，僅針對應用層邏輯進行「外掛化」與「收攏」。
