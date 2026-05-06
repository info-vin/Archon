# Phase 4.6.49: 智能路由與全域限流防禦 (Smart Routing & Rate Limiting)

> **核心目標**: 徹底解決因 Google Gemini Free Tier 嚴苛限制 (Pro: 2 RPM, Lite: 15 RPM) 所導致的 429 (Resource Exhausted) 與 503 (Unavailable) 錯誤。
> **設計原則**: **「零硬編碼 (Zero Hardcoding)」** 與 **「主動塑形 (Traffic Shaping)」**。系統將根據任務複雜度自動路由至合適的模型，並在送出請求前透過漏桶演算法 (Leaky Bucket) 進行主動排隊，避免撞擊 Google 伺服器的限流牆。

---

## 1. 物理斷層分析與根因 (Root Cause Analysis)

經過深度日誌與代碼分析，系統發生 429/503 的真實原因如下：
1.  **高並發微任務**: 當 Sentinel (哨兵) 一次性發現 3 個 Stale Leads 時，它會同時觸發 3 次 `TaskService.generate_task_from_alert_logic`。
2.  **昂貴模型的濫用**: 該邏輯內部目前**寫死**調用 `SYSTEM_MODELS["DEFAULT_PRO"]`。
3.  **物理撞牆**: `gemini-3.1-pro-preview` 在 Free Tier 僅允許 **2 RPM (每分鐘 2 次)**。當 3 個並發請求瞬間抵達時，第 3 個必定觸發 429，甚至可能因為瞬間 Payload 過大觸發 503 伺服器保護。

---

## 2. 實作藍圖 (Implementation Blueprint)

### 2.1 任務 A：Agent Registry 模型分級 (Model Tiering)
*   **檔案**: `python/src/server/services/agent_registry.py`
*   **動作**: 為 `AGENT_CONFIG` 內的每一個 Agent 賦予 `model_tier` 屬性。
    *   `market-bot` & `librarian` -> `"tier": "lite"` (高頻次、中低邏輯)
    *   `po-bot` & `dev-bot` -> `"tier": "pro"` (低頻次、高邏輯)
*   **目標**: 讓模型的選擇從代碼邏輯中抽離，變為純配置驅動。

### 2.2 任務 B：Agent Service 智能路由 (Smart Routing)
*   **檔案**: `python/src/server/services/agent_service.py`
*   **動作**: 
    *   移除 `_run_general_agent_task` 等處對 `SYSTEM_MODELS["DEFAULT_TEXT"]` 的直接引用。
    *   改為：讀取 Agent 的 `tier`，若為 `pro` 則呼叫 `get_model_path("DEFAULT_PRO")`，否則呼叫 `get_model_path("DEFAULT_TEXT")`。
*   **防呆**: 保留讀取 `archon_settings` 的能力作為最終 Fallback。

### 2.3 任務 C：全域流量塑形器 (Global Rate Limiter)
*   **檔案**: `python/src/server/services/system/rate_limiter.py` (新增)
*   **動作**: 實作一個輕量級的非同步節流閥 (Async Throttler)。
    *   紀錄 `pro` 模型與 `lite` 模型的最後呼叫時間 (`last_call_time`)。
    *   規則：`pro` 模型兩次呼叫間必須間隔 **32 秒**；`lite` 模型必須間隔 **4.5 秒**。
    *   實作 `await GlobalThrottler.wait_for_capacity(tier="pro")`。如果冷卻時間未到，透過 `asyncio.sleep()` 主動等待。

### 2.4 任務 D：限流閥注入 (Throttle Injection)
*   **檔案**: `python/src/server/services/projects/tasks/ai_operations.py` (POBot 任務生成) 與 `agent_service.py`。
*   **動作**: 在執行 `client.models.generate_content` 或 `client.chat.completions.create` 前，先呼叫 `await GlobalThrottler.wait_for_capacity()`。
*   **測試豁免**: 為了不拖慢 `make test-be` 的速度，`GlobalThrottler` 必須偵測 `TESTING=True` 環境變數，若在測試環境中則自動 Bypass 限流機制。

### 2.5 任務 E：Twin Scout 降級對齊
*   **檔案**: `scripts/twin_scout.py`
*   **動作**: 移除 `current_model = "gemini-3.1-flash-lite-preview"` 的硬編碼字串，改為動態載入 `model_ssot.py` 的 `get_model_path("DEFAULT_TEXT")`。

---

## 3. 物理驗證與驗收標準 (Verification Protocols)

### 3.1 驗證一：限流排隊機制 (Throttle Queueing)
*   **操作**: 寫一個簡單的腳本，同時 (`asyncio.gather`) 發起 3 個 `generate_task_from_alert_logic` 請求。
*   **預期 (物理斷言)**:
    *   終端機日誌必須顯示：`Throttler: Pro quota locked. Waiting 32s...`。
    *   三個請求將依序在大約 0s, 32s, 64s 完成，**全數回傳 200 OK，無任何 429 錯誤**。

### 3.2 驗證二：智能路由對齊 (Routing Alignment)
*   **操作**: 分別使用 Alice (Sales) 呼叫 MarketBot，與 Charlie (Manager) 呼叫 DevBot。
*   **預期 (物理斷言)**:
    *   檢查 `archon_logs` 或 Agent 內部日誌，確認 MarketBot 確實被發送至 `flash-lite` 模型，而 DevBot 確實被發送至 `pro` 模型。

### 3.3 驗證三：系統無痛回歸 (Regression)
*   **操作**: 執行 `make lint-be` 與 `make test-be`。
*   **預期 (物理斷言)**:
    *   測試執行時間不應因為 32 秒的限流而暴增（證明測試豁免機制有效）。
    *   500+ 項測試維持綠燈 100% 通過。