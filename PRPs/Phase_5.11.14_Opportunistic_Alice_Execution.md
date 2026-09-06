# Phase 5.11.14: Opportunistic Alice Execution & DAG Disconnect Analysis

## 1. 目標與當前架構差異 (Goal vs. Current Architecture)

### 當前代碼 (Current Logic - 樂觀路徑)
*   **觸發機制**：依賴 `CronTrigger`，綁死在每週二、三、五的 `10:25`。這是一種「樂觀路徑 (Happy Path)」的設計，假設伺服器在這些特定時間點一定處於啟動狀態。
*   **啟動補跑 (Catchup)**：若伺服器啟動時錯過 `10:25`，雖然有 `delay_mins=6` 的補跑機制，但因為 `_should_run_daily` 的嚴格過濾，如果今天是週一或週四，依舊會被跳過。

### 目標需求 (Target Logic - 務實路徑)
*   **見縫插針 (Opportunistic)**：放棄絕對時間與固定星期的束縛。目標是「每週跑一次」，只要 Docker (`make dev`) 啟動並維持健康運作超過 5 分鐘，就立刻利用空檔執行。

---

## 2. 代碼斷層風險深度剖析 (Disconnect Risk Analysis - 不改A壞B)

將 Alice 從「固定頻率 (Daily-ish)」改為「動態每週一次 (Weekly Opportunistic)」會引發嚴重的 DAG (有向無環圖) 斷層：

1.  **事件鏈的連鎖降級 (Event Chain Degradation)**
    *   **現狀**：Alice 執行完會觸發 `_run_daily_market_report` (Bob)，Bob 執行完會觸發 `_run_daily_executive_summary` (系統總結)。這是一條硬連接的 DAG。
    *   **斷層風險**：如果 Alice 改為每週執行一次，意味著下游的「**日報 (Daily Report)**」與「**系統日結 (Daily Executive Summary)**」也會被迫變成「每週只執行一次」。這在語義上會產生嚴重矛盾 (一個名叫 Daily 的報告每週才發一次)。
2.  **資料收集窗口斷層 (Data Window Miss)**
    *   **現狀**：`bob_market_report` 與 `daily_executive_summary` 的內部邏輯都寫死了擷取 `days=1` (過去 24 小時) 的資料。
    *   **斷層風險**：如果 Alice 成功改為 Opportunistic Weekly，當她執行時，Bob 能成功抓到剛產生的 Leads (因為在 24 小時內)。但 `daily_executive_summary` 卻會漏掉本週前幾天的系統日誌，只總結了這最後的 24 小時。

---

## 3. 解決方案：消除虛假開發與 SSOT/DRY 實踐

為了徹底解決上述斷層，且不引入虛假開發 (Fake Development)，我們需要進行結構性的解耦與重構：

### 方案 A：DAG 脫鉤與動態時間窗 (推薦)
1.  **Alice 升級為 Weekly Opportunistic**:
    *   在 `scheduler_service.py` 實作 `_should_run_weekly_local_only`。
    *   使用 `IntervalTrigger(hours=12)` 取代 `CronTrigger`，並設定 `delay_mins=5`，確保 Docker 存活 5 分鐘後發動。
2.  **Bob 語義與時間窗修正 (SSOT 物理對齊)**:
    *   將 `_run_daily_market_report` 更名為 `_run_market_report`，消除 Daily 語義。
    *   **動態擷取 (Dynamic Fetch)**：不再寫死 `one_day_ago = (datetime.now() - timedelta(hours=24))`，而是透過 `SettingsService` 讀取 `LAST_RUN_BOB_MARKET_REPORT`，精準抓取「上次執行至現在」的所有 Leads，落實 DRY 原則並防止漏件。
3.  **Daily Executive Summary 脫鉤**:
    *   將 `daily_executive_summary` 從 Bob 的觸發鏈中拔除。將其轉移至 Category 2 (獨立的 Daily Stateful Job)，讓系統在啟動時自動補跑昨天的日報，而不是跟隨 Alice 的腳步。

### 驗證計畫 (Verification Plan)
1.  **實體公證**：撰寫 `tests/test_dag_disconnect.py`，模擬 `make dev` 中斷 3 天後重啟的情境。
2.  **斷言條件**：
    *   Alice 是否在 5 分鐘後發動。
    *   Bob 是否精準抓取了這 3 天累積的所有 Leads，而不是只抓最後 24 小時。
    *   Daily Summary 是否獨立執行，未被 Alice 的延遲所干擾。
