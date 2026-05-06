# Phase 4.9 實作計畫 (Implementation Plan) - Security & Autonomy

> **目標 (Goal)**: 
> 1. **實施門禁制度**: 在 API 層級嚴格執行 RBAC，確保 Alice/Bob 只能看見並使用其職權範圍內的 AI 員工。
> 2. **升級巡邏能力**: 讓 Clockwork (維運機器人) 從單純的「統計員」進化為「巡邏員」，能主動分析錯誤日誌並通知 DevBot 處理。

## User Review Required
> [!IMPORTANT]
> **API Hardening**: 本次變動將使 `/api/agents/assignable` 從公開變為私有（需 JWT Token）。若前端有任何未登入即呼叫此 API 的情境，將會報錯。
> **Autonomy Level**: Clockwork 目前僅被授權「觀察」與「指派任務」，不會直接修改代碼。所有修復仍需經由 Charlie 或 Admin 審核。

## Proposed Changes

### 1. RBAC Enforcement (門禁強化)
#### [MODIFY] `python/src/server/api_routes/agents_api.py`
- [ ] 注入 `get_current_user` 依賴。
- [ ] 實作角色過濾邏輯：
    - `system_admin`: 全部可用。
    - `sales`: 僅 `MarketBot`。
    - `marketing`: `MarketBot` + `Librarian`。
    - `manager`: 全部可用。

#### [MODIFY] `python/src/server/services/agent_service.py`
- [ ] 更新 `get_assignable_agents` 函式，支援接收 `user_role` 與 `user_dept` 作為過濾參數。

### 2. Clockwork Evolution (主動巡邏)
#### [MODIFY] `python/src/server/services/scheduler_service.py`
- [ ] **Job 3: `log_patrol` (每小時執行)**:
    - 掃描最近 1 小時內的 `archon_logs` (level=ERROR)。
    - 使用 LLM 對錯誤進行分類（環境問題 vs 代碼問題）。
- [ ] **Action Trigger**:
    - 若判定為代碼問題，自動建立一個標註為 `Clockwork-Identified` 的任務，並指派給 `DevBot` 執行自癒。

### 3. Verification & Tests
#### [NEW] `python/tests/integration/services/test_phase49_rbac.py`
- [ ] 驗證以 Alice 身份登入時，API 是否只回傳 MarketBot。
- [ ] 驗證未登入者是否被 401 拒絕。

#### [NEW] `python/tests/integration/services/test_phase49_clockwork_patrol.py`
- [ ] 模擬一個 ERROR 日誌，驗證 Clockwork 是否能正確識別並建立修復任務。

## 驗收標準 (Acceptance Criteria)
1. **RBAC 合規**: 不同角色的使用者呼叫同一個 API，回傳的 Agent 清單必須與 `RBAC_Collaboration_Matrix.md` 完全一致。
2. **自動診斷**: 當系統發生錯誤時，Clockwork 應在 1 小時內於 `archon_logs` 中留下「分析報告」並產出相關任務。
3. **零誤殺**: Clockwork 不應針對環境問題（如網路暫時斷線）重複指派修復任務。

## 實作進度
- [x] **Step 1**: RBAC 門禁邏輯實作。
- [x] **Step 2**: Clockwork 日誌分析迴圈開發。
- [x] **Step 3**: 整合測試與安全驗證。

