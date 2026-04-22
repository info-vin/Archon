# Phase 4.6.23 實作計畫 (Implementation Plan) - Unified Tool Dispatch & Gate Hardening

> **目標 (Goal)**: 
> 1. **統一工具調度**：移除 `AgentService` 中 30 行硬編碼的 `if/elif` 原生工具判斷，實現配置驅動的調用映射。
> 2. **身分數據對齊**：修正 Poisson Gate 的統計查詢身分，將傳遞參數從「顯示名稱」對齊為「實體 ID (Slug)」。
> 3. **解釋性攔截訊息**：讓 Poisson Gate 的攔截結果包含等級導引，協助 LLM 理解等級門檻。

## 1. 物理稽核與目標分析 (Audit & Mission)

| 項目 | 現狀 (Current) | 4.6.23 目標 (Target) | 物理理由 |
| :--- | :--- | :--- | :--- |
| **工具分發** | ✅ 已重構 | 建立 `self.native_tool_map` 進行動態 dispatch。 | 提高系統擴展性，移除重複的錯誤處理。 |
| **門禁身分** | ✅ 已對齊 | 改傳 `agent_id` (如 "ai-dev-bot")。 | 資料庫 `agent_xp` 紀錄是綁定在 ID 而非 Human Name。 |
| **攔截回饋** | ✅ 已強化 | 回饋 `"Blocked: Your Level X < Required Level Y"`。 | 提供物理性推理線索，防止 LLM 在權限不足時盲目重試。 |

## 2. 實體修改路徑 (Implementation Checklist)

### 2.1 修改 `python/src/server/services/agent_service.py`
- [x] **定義原生工具映射**：
    - 已在 `__init__` 中建立映射表。
- [x] **重構 `_handle_tool_calls`**：
    - 統一身分識別：使用 slug 進行 XP 查詢。
    - 動態調用邏輯：移除硬編碼 if/elif。
- [x] **強化門禁訊息構造**：
    - 已實作包含等級門檻的錯誤回饋。

### 2.3 物理審計與遺產恢復任務 (Final Hardening & Recovery)
- [x] **移除專案硬編碼**: 
    - 已修改 `task_service.py`，實現動態專案獲取。
- [x] **補全部門隔離邏輯**: 
    - 已在 `propose_change_service.py` 實作 JSONB 篩選。
- [x] **實體化幾何繪圖外掛**: 
    - 已建立 `logo_tool.py` 並補完 Bob 繪圖外掛。
- [x] **找回丟失的 Token 成本組件**: 
    - 已從 Git 歷史恢復 `TokenUsageTable.tsx` 並掛載至 Admin UI。
- [x] **實體化智慧提取功能**: 
    - 補完 `extraction_api.py` 的 PATCH 接口，並實體化 `/run` 背景任務。
- [x] **修正環境變數物理混合**: 
    - 已更新 `.env.test`，指向獨立測試專案。

## 3. 物理驗證計畫 (Verification)

- [x] **門禁精準測試**：模擬 `ai-market-bot` 呼叫工具並驗證攔截。
- [x] **回歸測試**：執行 `make test-be` (555 passed)。
- [x] **負面安全性驗證 (New)**：
    - 已建立並執行 `test_security_isolation.py` (PASSED)。
- [x] **提取閉環驗證 (New)**：
    - 已建立並執行 `test_extraction_realization.py` (PASSED)。

## 4. 4xx/5xx 錯誤碼專項審查結論 (Zero Fantasy)

| 狀態碼 | 查核結論 (Audit Result) | 現狀 |
| :--- | :--- | :--- |
| **401** | ✅ Settings API 已加固。 | 已落地 |
| **403** | ✅ Service 層已補全部門檢查。 | 已落地 |
| **404** | ✅ 解決了 8181/8052 探針與專案硬編碼問題。 | 已落地 |
| **500** | ✅ `storage_service.py` 已實作精確錯誤識別。 | 已落地 |
