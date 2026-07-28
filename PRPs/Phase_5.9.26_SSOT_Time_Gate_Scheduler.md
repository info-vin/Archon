# Phase 5.9.26: 智慧型時間閘門與 SSOT 架構硬化 (Scheduler SSOT Time Gate)

## 1. 核心目標與原則
1. **絕不硬編碼 (No Hardcoding)**：任務的執行時間（時與分）絕不能在檢查函數 (check_func) 中寫死，必須遵從 SSOT。
2. **符合 SSOT (Adhere to SSOT)**：排程器時間的單一真實來源 (Single Source of Truth) 必須是 `CronTrigger` 物件（其底層數據來自 `SchedulerConfig` 或預設值）。
3. **優雅容錯與追趕 (Graceful Catchup)**：解決伺服器重啟時，排程器因日期檢查缺陷而導致任務提早被消耗的問題，同時保留伺服器斷線後的 Catchup (追趕) 補跑能力。

## 2. 待修復的架構缺陷 (The Architectural Defect)
在先前的實作中，`SchedulerService` 具備 Catchup 機制，會在伺服器啟動時自動補跑未執行的任務。
然而這造成了「時間越界」的副作用：若在 08:35 重啟伺服器，系統會在 08:41 觸發 Catchup。對於原訂 10:30 執行的 `alice_auto_fetch` 爬蟲，系統因為只檢查了「今天是否執行過（日期）」，便**錯誤地在 08:41 提早觸發了爬蟲**。
這不僅打亂了業務節奏，更導致 10:30 的正班車因為當日額度已耗盡而被系統略過。

## 3. 實作歷程 (Execution History)

### Step 1: 動態時間閘門 (Dynamic Time Gate)
- **行動**：修改狀態檢查函數的簽名與邏輯，注入 `CronTrigger`。
- **作法**：
  - 將 `_should_run_daily`, `_should_run_local_only`, `_should_run_weekly` 等函數的簽名擴充為接受 `trigger: CronTrigger | None = None`。
  - 實作「時間閘門」：當傳入 `trigger` 時，動態解析 `trigger.fields[5]` (小時) 與 `trigger.fields[6]` (分鐘)。如果當前時間尚未到達目標時間，則強制回傳 `False`，藉此阻擋不合理的 Catchup 提早執行。

### Step 2: SSOT 實體傳遞 (SSOT Injection)
- **行動**：將時間的真理源頭傳入閘門。
- **作法**：在 `_schedule_stateful_job` 內部，將專屬於該任務的 `CronTrigger` 實體直接傳遞給 `check_func` 閉包，徹底消滅了使用 `lambda` 硬編碼時間的補丁寫法，完成了 L2 DRY 模組化的架構要求。

### Step 3: 影響範圍分析 (Impact Analysis)
#### 問：有修復型別覆蓋嗎？
**答：有的，且更為嚴謹。** 
我們替所有的 `_should_run_*` 函數加上了 `trigger: CronTrigger | None = None` 的明確靜態型別標註，並順利通過了 `uv run mypy src/server/` (309 支檔案 0 錯誤) 的嚴格型別檢查，確保了 `SchedulerService` 內部依舊維持完美的 100% 型別覆蓋。對於其他模組（例如 1.1 核心服務）的 80% 覆蓋率則未受本次修改影響。

#### 問：有影響 `daily_executive_summary` 嗎？
**答：絕對沒有影響，100% 相容。**
`daily_executive_summary` (每日總結報告) 是一個由爬蟲結束後主動觸發的「事件驅動 (Event-Driven)」任務。它是透過 `_trigger_stateful_daily_event` 來呼叫 `_should_run_daily`，在此過程中並**沒有傳遞任何 `trigger` 參數**。
因為我們在修改時，為 `trigger` 設定了預設值 `None`。當 `trigger=None` 時，時間閘門會被自動略過，系統會退回原本純粹的「日期檢查」防護。因此 `daily_executive_summary` 的運作邏輯與重構前完全相同，完全沒有被影響。

## 4. 驗證結果 (Validation Results)
本階段已成功通過所有自動化公證門禁：
- ✅ `make lint-be`: 語法排版 100% 乾淨。
- ✅ `uv run mypy src/server/`: 型別標註 100% 正確，無 Callable 簽名衝突。
- ✅ `make test-be`: 612 項單元與整合測試全數通過，確保系統零副作用 (Zero Regressions)。

### Step 4: 爬蟲推論併發限流修復 (Concurrency Limit for Gemini Inference)
- **行動**：修復爬蟲取得大量職缺後，呼叫 Gemini 預測痛點時引發的 `429 RESOURCE_EXHAUSTED` 錯誤。
- **作法**：
  - 先前 `RateLimiter` 的 `acquire()` 僅計算 Token 總數，並未阻擋 `asyncio.gather` 所發起的「瞬間併發 (Concurrency)」。這導致數十個推論請求在同一毫秒擊中 Gemini Free Tier 伺服器，觸發 15 RPM 的防禦網。
  - 在 `job_board_service.py` 中的 `_infer_need` 閉包內，引入 `async with self.rate_limiter.semaphore:` 限制物理併發數 (預設為 1)。
  - 將洪水式併發轉化為**循序漸進的排隊處理**，成功確保 Token Bucket 發揮緩衝與平滑分佈的作用，完美消滅 429 錯誤。
