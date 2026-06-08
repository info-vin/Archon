# Phase 5.5.10 Clockwork & Hugging Face Synchronization Strategy

## 背景與目標 (Background & Objectives)

在 Phase 5.5.9 導入了 3-Tier 容災降階架構 (Gemini -> Hugging Face -> Ollama) 之後，我們需要解決後端 Clockwork 任務排程引擎與 Hugging Face (HF) Space 開關機時間表的同步問題。

目前 Clockwork 的狀態化每日作業 (Stateful Daily Jobs) 採用的是基於 UTC 換日 (台灣時間 08:00) 的隱性觸發機制。這會導致每天台灣時間早上 08:00 出現「晨間風暴」，所有龐大的資料抓取與總結作業瞬間併發，產生極大的 API Rate Limit 壓力。

本階段的目標是：
1. **消除晨間風暴**：將 `IntervalTrigger` 改為精確的 `CronTrigger`，將作業時間錯開，分散高負載。
2. **提前作業時程**：將每日高負載作業提前至台灣時間 07:00 開始，以更貼近人類高管晨間查閱報表的需求。
3. **引入節律感知 (Circadian Rhythm)**：讓 Clockwork 具備 HF 睡眠時間的感知能力，避免在 HF 關機期間 (台灣 00:18 ~ 06:41) 因模型驗證失敗而引發錯誤的系統警報。

## 系統作息時間軸 (System Circadian Rhythm)

| 台灣時間 (CST) | UTC 時間 | 系統狀態區間 | HF Space 狀態 | 預期活動與負載分析 |
| :--- | :--- | :--- | :--- | :--- |
| **00:18 ~ 06:41** | 16:18 ~ 22:41 | 💤 **深度休眠期** | **暫停 (Paused)** | **絕對低峰。** 僅背景高頻探針運行。Clockwork 應啟用「睡眠感知」，略過對 Tier 2 (HF) 的非緊急健康檢查。 |
| **06:42** | 22:42 | 🌅 **HF 喚醒期** | **重啟 (Restart)** | GitHub Actions 自動喚醒 HF 伺服器。 |
| **06:42 ~ 06:59** | 22:42 ~ 22:59 | 🌅 **暖機完成** | **上線 (Online)** | HF 準備就緒。 |
| **07:00 ~ 08:30** | 23:00 ~ 00:30 | 🚀 **晨間管線執行** | **上線 (Online)** | **依序排程 (CronTrigger)** 的每日高負載作業開始執行 (詳見下節)。 |
| **09:00 ~ 18:00** | 01:00 ~ 10:00 | 🏢 **正常營業期** | **上線 (Online)** | 系統負載取決於人類使用者活動。 |
| **18:00 ~ 00:17** | 10:00 ~ 16:17 | 🌆 **晚間收尾期** | **上線 (Online)** | 人類活動減少，系統回歸低峰。 |

## 實作計畫 (Implementation Plan)

### 1. 改造排程觸發器 (CronTrigger Conversion)

在 `python/src/server/services/scheduler_service.py` 中，將 `_schedule_stateful_daily` 中使用的 `IntervalTrigger(hours=1)` 取代為精確的 `CronTrigger`。

**新的每日管線排程 (晨間 07:00 ~ 08:00 CST，間隔 20 分鐘)：**

*   **07:00 CST (UTC 23:00)**：Alice 開始抓取潛在客戶 (`alice_auto_fetch`)。確保新資料準備就緒。
*   **07:20 CST (UTC 23:20)**：執行系統清理作業。包含清理過期潛在客戶 (`prune_stale_leads`) 與清理過期探針日誌 (`system_probe_cleanup`)。
*   **07:40 CST (UTC 23:40)**：Bob 根據 Alice 抓回來的最新資料，生成每日行銷報告 (`bob_market_report`)。
*   **08:00 CST (UTC 00:00)**：生成高階主管總結 (`daily_executive_summary`)。此時所有部門的最新數據皆已齊備。
*   **08:20 CST (UTC 00:20)**：執行 Token 用量分析 (`token_analysis`)。在晨間大量 API 呼叫結束後，進行 24 小時成本結算與異常突增 (Cost Spike) 防護警報。
*   **08:40 CST (UTC 00:40)**：執行商業哨兵監控 (`business_sentinel`)。掃描過期的潛在客戶與卡關的部落格文章，並自動指派逾期追蹤任務，確保人員上班時待辦清單已準備就緒。

**週末與月度延伸管線 (Extended Pipeline)：**
針對中長期的報表與巡檢，改為在低峰或週末特定時間點精確觸發：
*   **每週一 06:00 CST (UTC 22:00)**：執行每週高階主管總結 (`weekly_executive_summary`)。
*   **每月 1 號 06:30 CST (UTC 22:30)**：執行每月高階主管總結 (`monthly_executive_summary`)。
*   **每週六 08:00 CST (UTC 00:00)**：執行 API 棄用掃描 (`api_deprecation_scan`)。
*   **每週日 08:00 CST (UTC 00:00)**：執行技術債巡檢 (`tech_debt_audit`)。

### 2. David (POBot) 的持續性監督 (Continuous Oversight)

如系統設計所述，排程優化不應只是靜態設定。應該在系統初始化 (`init_db.py`) 時，為 David (POBot) 建立一個隸屬於「內部架構專案 (Internal Architecture)」的預設**長效型任務 (Ongoing Task)**。
*   **目標**：David 需定期（或透過探針觸發）檢視 Clockwork 的執行日誌與 HF 的上線狀態。
*   **職責**：若發現 07:00 ~ 09:00 之間仍出現 API Rate Limit (429) 或排程碰撞，David 應主動提出「Clockwork 排程微調建議 (基於當前日期)」，實現 AI 系統對自身效能的閉環優化。

### 2. 實作 HF 節律感知 (HF Sleep Awareness)

在 `scheduler_service.py` 中新增時間判定邏輯：

```python
from datetime import datetime, timezone, timedelta, time

def is_hf_awake() -> bool:
    """
    判斷當前時間是否在 HF 的上線視窗內。
    HF Space 睡眠時間為台灣 00:18 ~ 06:41 (CST)。
    """
    # 取得 CST (UTC+8) 時間
    cst_now = datetime.now(timezone.utc).astimezone(timezone(timedelta(hours=8)))
    current_time = cst_now.time()
    
    sleep_start = time(0, 18)
    sleep_end = time(6, 41)
    
    if sleep_start <= current_time <= sleep_end:
        return False
    return True
```

**應用場景：**
在 `patrol.py` 中的 `run_model_verification` (模型驗證探針) 內整合此邏輯。當 `is_hf_awake()` 為 `False` 時，探針應跳過對 Tier 2 (Hugging Face) 的連線測試，並在日誌中註記為 `[Sleep Mode]`，以防產生誤報並派發無效的自動修復任務給 DevBot。

## 成功標準與自動化驗證 (Acceptance Criteria & Automated Verification)

**【絕對鐵律】：拒絕樂觀路徑，所有排程邏輯與節律感知必須由 Pytest 物理斷言把關。**

### 1. 單元測試：HF 節律邊界測試 (Unit Test)
*   **目標檔案**：`python/tests/unit/services/test_scheduler_service.py` (需新建)
*   **斷言目標**：使用 `unittest.mock.patch` 模擬 `datetime.now(timezone.utc)`。
    *   模擬 CST 00:18 -> 斷言 `is_hf_awake()` 為 `False`。
    *   模擬 CST 06:41 -> 斷言 `is_hf_awake()` 為 `False`。
    *   模擬 CST 06:42 -> 斷言 `is_hf_awake()` 為 `True`。
    *   模擬 CST 00:17 -> 斷言 `is_hf_awake()` 為 `True`。

### 2. 整合測試：休眠模式攔截 (Integration Test)
*   **目標檔案**：`python/tests/integration/services/test_phase49_clockwork_patrol.py`
*   **斷言目標**：新增 `test_model_verification_sleep_mode()`。
    *   `patch` `is_hf_awake` 強制回傳 `False`。
    *   執行 `run_model_verification()`。
    *   **物理斷言**：檢查 `get_supabase_client().table("archon_logs").insert` 的呼叫參數，必須包含 `[Sleep Mode]` 字樣，並且 **嚴格斷言** 沒有拋出任何 Exception，也沒有發生 `ERROR` 級別的日誌寫入。

### 3. 排程器組態驗證 (Scheduler Config Test)
*   **目標檔案**：`python/tests/unit/services/test_scheduler_service.py`
*   **斷言目標**：呼叫 `scheduler_service._schedule_jobs()` (不啟動 event loop)。
    *   透過 `scheduler_service._scheduler.get_jobs()` 提取所有已註冊的任務。
    *   **物理斷言**：`alice_auto_fetch` 的 Trigger 類型必須是 `CronTrigger`，且其 `hour` 屬性為 23，`minute` 屬性為 0。
    *   **物理斷言**：`token_analysis` 的 Trigger 必須是 `CronTrigger`，且 `hour`=0, `minute`=20。確保 20 分鐘的間隔被物理寫入設定。
