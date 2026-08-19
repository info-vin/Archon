# Phase 5.10.24: 修復 Refactoring 斷層與 SSOT 硬編碼清理

## 1. 目標 (Goal)
基於近期 3 天內的 `git log` 分析，修正先前在 `stats_api.py` 與 `hybrid_router.py` 重構時遺漏的技術債（斷層）。
同時，根據最新網路查詢結果，將系統中缺失的 `gemini-3.5-flash` / `gemini-3.5-flash-lite` 模型真實費率補齊，以符合營運與 ROI 追蹤的正確性。

## 2. 背景事實 (Facts from Git Log & Codebase)
*   `python/src/server/api_routes/stats_api.py` 在之前的幾次 Commit (`f2523311`, `4c3726f6`, `99abe364`) 漸進式地補上了 Pydantic `response_model`，但是遺漏了 `/sla-reliability`, `/business-risks`, `/health-trend`, `/overview`, `/ai-usage`, 與 `/consolidated` 共 5 個端點，導致同一個 API Router 內出現強弱型別混雜的斷層。
*   `python/src/server/services/llm/hybrid_router.py` 在 `aff54678` 進行 SSOT (單一事實來源) 清理與 `6133db7a` 加上稽核豁免標籤後，`is_query_simple_and_offline` 函式中依然殘留「50 字上限」以及「online_keywords」陣列的硬編碼 (Hardcoding)，且無豁免標籤。
*   網路搜尋 (2026/08) 確認了 Google 官方的 3.5 費率，必須在 `config.py` 補上。

## 3. 預計修改內容 (Proposed Changes)

### 3.1 補齊模型真實費率
#### [MODIFY] `python/src/server/config/config.py`
在 `default_pricing` 字典中新增從網路查核到的正確費率：
*   `"gemini-3.5-flash"`: `{"input": 1.50, "output": 9.00}`
*   `"gemini-3.5-flash-lite"`: `{"input": 0.30, "output": 2.50}`

### 3.2 補足資料表初始種子 (Database Migration)
#### [NEW] `migration/20260819_add_hybrid_router_settings.sql`
為了避免 `init_db.py` 潛在的資料庫清空風險，改採用標準的 SQL 擴充腳本寫入這兩項設定。建立新的 Migration 腳本，透過 `INSERT ... ON CONFLICT (key) DO NOTHING` 確保冪等性：
*   寫入 `key = 'offline_word_limit'`, `value = '50'`, `category = 'system'`
*   寫入 `key = 'online_keywords'`, `value = '["crawl", "search", "fetch", "live", "latest", "realtime", "google", "news", "code", "寫程式", "程式碼"]'`, `category = 'system'`

### 3.2 補齊強型別斷層 (DRY & Type Safety)
#### [MODIFY] `python/src/server/api_routes/stats_api.py`
為遺漏的端點定義 Pydantic Models，並掛載至 `@router.get(response_model=...)`，徹底消滅 `dict[str, Any]` 與 `Any`：
*   新增 `SLAReliabilityResponse`
*   新增 `BusinessRiskDTO`
*   新增 `HealthTrendResponse`
*   新增 `AIUsageResponse`
*   新增 `ConsolidatedStatsResponse`
並在發生 Exception 時回傳包含 `error` 欄位的實體化 Model，避免造成前端 UI 解構錯誤 (TypeError)。

### 3.3 拔除硬編碼與落實 SSOT
#### [MODIFY] `python/src/server/services/llm/hybrid_router.py`
*   將 `if len(words) >= 50:` 替換為 `if len(words) >= int(self._get_setting_cached("offline_word_limit", "50")):`
*   將 `online_keywords` 的寫死清單替換為透過 `SettingsService` 解析 JSON：
    `keywords_str = self._get_setting_cached("online_keywords", '["crawl", "search", "fetch", "live", "latest", "realtime", "google", "news", "code", "寫程式", "程式碼"]')`
    `online_keywords = json.loads(keywords_str)`
這將確保這兩項規則可以被管理者在 `archon_settings` 資料表中動態調整，徹底符合 SSOT 精神。

## 4. 自動化驗證計畫 (Automated Verification)
修改完成後，將會自動執行以下指令以確保不產生新的斷層與報錯：
1. **Linter / Type Checking**: 執行 `make lint` 確保 Pydantic 的型別轉換正確，無 Mypy `[override]` 或變數未定義錯誤。
2. **單元測試公證**: 執行 `make test-be` (或 `pytest python/tests/server/api_routes/test_stats_api.py`) 確認強型別的修正沒有破壞現有的測試斷言。
