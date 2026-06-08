# Phase 5.5.10 Clockwork & Hugging Face Synchronization Strategy

## 背景與目標 (Background & Objectives)

在 Phase 5.5.9 導入了 3-Tier 容災降階架構 (Gemini -> Hugging Face -> Ollama) 之後，我們需要解決後端 Clockwork 任務排程引擎與 Hugging Face (HF) Space 開關機時間表的同步問題。

目前 Clockwork 的狀態化每日作業 (Stateful Daily Jobs) 採用的是基於 UTC 換日 (台灣時間 08:00) 的隱性觸發機制。這會導致每天台灣時間早上 08:00 出現「晨間風暴」，所有龐大的資料抓取與總結作業瞬間併發，產生極大的 API Rate Limit 壓力。

本階段的目標是：
1. **消除晨間風暴**：將 `IntervalTrigger` 改為精確的 `CronTrigger`，將作業時間錯開，分散高負載。
2. **提前作業時程**：將每日高負載作業提前至台灣時間 07:00 開始，以更貼近人類高管晨間查閱報表的需求。
3. **引入節律感知 (Circadian Rhythm)**：讓 Clockwork 具備 HF 睡眠時間的感知能力，避免在 HF 關機期間 (台灣 01:00 ~ 06:00) 因模型驗證失敗而引發錯誤的系統警報。

## 系統作息時間軸 (System Circadian Rhythm)

| 台灣時間 (CST) | UTC 時間 | 系統狀態區間 | HF Space 狀態 | 預期活動與負載分析 |
| :--- | :--- | :--- | :--- | :--- |
| **01:00 ~ 05:59** | 17:00 ~ 21:59 | 💤 **深度休眠期** | **暫停 (Paused)** | **絕對低峰。** 僅背景高頻探針運行。Clockwork 應啟用「睡眠感知」，略過對 Tier 2 (HF) 的非緊急健康檢查。 |
| **06:00** | 22:00 | 🌅 **HF 喚醒期** | **重啟 (Restart)** | GitHub Actions 自動喚醒 HF 伺服器。 |
| **06:00 ~ 06:59** | 22:00 ~ 22:59 | 🌅 **暖機完成** | **上線 (Online)** | HF 準備就緒。 |
| **07:00 ~ 08:30** | 23:00 ~ 00:30 | 🚀 **晨間管線執行** | **上線 (Online)** | **依序排程 (CronTrigger)** 的每日高負載作業開始執行 (詳見下節)。 |
| **09:00 ~ 18:00** | 01:00 ~ 10:00 | 🏢 **正常營業期** | **上線 (Online)** | 系統負載取決於人類使用者活動。 |
| **18:00 ~ 00:59** | 10:00 ~ 16:59 | 🌆 **晚間收尾期** | **上線 (Online)** | 人類活動減少，系統回歸低峰。 |

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

### 2. 實作 HF 節律感知 (HF Sleep Awareness)

在 `scheduler_service.py` 中新增時間判定邏輯：

```python
from datetime import datetime, UTC

def is_hf_awake() -> bool:
    """
    判斷當前 UTC 時間是否在 HF 的上線視窗內。
    HF Space 睡眠時間為台灣 01:00 ~ 06:00 (UTC 17:00 ~ 21:59)。
    """
    current_hour = datetime.now(UTC).hour
    if 17 <= current_hour < 22:
        return False
    return True
```

**應用場景：**
在 `patrol.py` 中的 `run_model_verification` (模型驗證探針) 內整合此邏輯。當 `is_hf_awake()` 為 `False` 時，探針應跳過對 Tier 2 (Hugging Face) 的連線測試，並在日誌中註記為 `[Sleep Mode]`，以防產生誤報並派發無效的自動修復任務給 DevBot。

## 成功標準 (Acceptance Criteria)

1.  確認 `scheduler_service.py` 中的每日任務已從隱性輪詢改為精確的 `CronTrigger`。
2.  確認排程時間嚴格遵守 07:00 ~ 08:00 CST 的 20 分鐘間隔流水線。
3.  確認 `model_verification` 在台灣時間 01:00 ~ 06:00 之間不會因為 HF 離線而產生錯誤日誌 (`archon_logs` 不會新增 ERROR 等級的 HF 連線失敗紀錄)。
