# Phase 4.6.23 實作計畫 (Implementation Plan) - Unified Tool Dispatch & Gate Hardening

> **目標 (Goal)**: 
> 1. **統一工具調度**：移除 `AgentService` 中 30 行硬編碼的 `if/elif` 原生工具判斷，實現配置驅動的調用映射。
> 2. **身分數據對齊**：修正 Poisson Gate 的統計查詢身分，將傳遞參數從「顯示名稱」對齊為「實體 ID (Slug)」。
> 3. **解釋性攔截訊息**：讓 Poisson Gate 的攔截結果包含等級導引，協助 LLM 理解等級門檻。

## 1. 物理稽核與目標分析 (Audit & Mission)

| 項目 | 現狀 (Current) | 4.6.23 目標 (Target) | 物理理由 |
| :--- | :--- | :--- | :--- |
| **工具分發** | `_handle_tool_calls` 寫死 `if func == "apply_mod"` 等邏輯。 | 建立 `self.native_tool_map` 進行動態 dispatch。 | 提高系統擴展性，移除重複的錯誤處理。 |
| **門禁身分** | 傳遞 `display_name` (如 "Archon DevBot") 給統計服務。 | 改傳 `agent_id` (如 "ai-dev-bot")。 | 資料庫 `agent_xp` 紀錄是綁定在 ID 而非 Human Name。 |
| **攔截回饋** | 僅回饋 `"Poisson Security Block"`。 | 回饋 `"Blocked: Your Level X < Required Level Y"`。 | 提供物理性推理線索，防止 LLM 在權限不足時盲目重試。 |

## 2. 實體修改路徑 (Implementation Checklist)

### 2.1 修改 `python/src/server/services/agent_service.py`
- [x] **定義原生工具映射**：
    - 在 `__init__` 中建立映射表：`self._tools = {"apply_modification": self._exec_mod, ...}`。
- [x] **重構 `_handle_tool_calls`**：
    - 統一身分識別：`is_trusted = await self._check_poisson_gate(agent_id=agent_id, ...)` (使用 slug)。
    - 動態調用邏輯：`if func in self._tools: result = await self._tools[func](...)`。
- [x] **強化門禁訊息構造**：
    - 實作解釋性字串，包含當前等級與需求等級。
- [x] **補齊工具視野**：手動注入 `apply_modification` 與 `perform_web_crawl` 的 Schema (修復 0326 遺漏)。

### 2.3 物理審計補充任務 (Final Hardening)
- [ ] **移除專案硬編碼**: 
    - 修改 `python/src/server/services/projects/task_service.py`，將 `"field_ops_001"` 改為動態從 `archon_settings` 讀取。
- [ ] **補全部門隔離邏輯**: 
    - 修改 `python/src/server/services/propose_change_service.py`，實作 Service 層的經理部門檢查。
- [ ] **實體化幾何繪圖外掛**: 
    - 建立 `python/src/server/services/marketing/logo_tool.py`，實作 PRP 承諾的 SVG 物理生成邏輯。
- [ ] **修正環境變數混合**: 
    - 更新 `.env.test`，物理隔離生產環境 URL，防止 `FORCE_PROD_TEST` 誤傷。

## 3. 物理驗證計畫 (Verification)

- [x] **門禁精準測試**：
    - 模擬 `ai-market-bot` 呼叫 `apply_modification`。
    - **斷言**：物理顯示正確 ID 與等級對比訊息。
- [x] **回歸測試**：
    - 執行 `make test-be`：物理證實 553 通過。
- [x] **型別掃描**：
    - 執行 `uv run mypy src/server`：物理證實 **Zero Errors**。
- [ ] **負面測試驗證 (New)**：
    - 模擬 Manager A 查看 Manager B 的提案，斷言觸發 403。
- [ ] **動態專案驗證 (New)**：
    - 修改 `archon_settings` 後，斷言語音工單流向正確變更。

## 4. 4xx/5xx 錯誤碼專項審查結論 (Zero Fantasy)

| 狀態碼 | 查核結論 (Audit Result) | 剩餘動作 |
| :--- | :--- | :--- |
| **401** | ✅ Settings API 已加固。 | 監控前端 Silent Refresh 延遲。 |
| **403** | ⚠️ API 層已封鎖，Service 層缺失部門檢查。 | 執行 2.3 中的部門隔離修正。 |
| **404** | ⚠️ 存在語音任務轉發至寫死 ID 的風險。 | 執行 2.3 中的專案硬編碼修正。 |
| **500** | ✅ `safe_json_loads` 已覆蓋主要 API。 | 建立 Storage 權限的防禦性捕捉。 |
