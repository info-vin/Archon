# Phase 5.1.14: Clockwork 排程器最佳化與時間表重塑 (Clockwork Optimization)

## 背景與痛點 (Background)
Archon 系統中的背景排程器 (SchedulerService/Clockwork) 隨著各個階段的開發累積了 **13 項週期性任務**（包含此前遺漏的 Agent 派單作業 `task_dispatcher` 與日誌清理作業）。
目前這些任務依賴脆弱的「絕對時間 (Absolute Time, 如 06:00)」或「死板的間隔 (Interval)」。在您每天僅手動開關 Docker 兩次的實際使用情境下，絕對時間經常被錯過，導致開機時觸發「雷鳴群效應 (Thundering Herd)」或引發 API 429 錯誤。

## 本階段目標 (Goals)
徹底捨棄絕對時間思維！建立一套**「Docker 生命週期與狀態驅動 (Lifecycle & State-Driven)」**的一致性排程架構。

### 1. 任務統一分類與相對觸發策略 (Unified Delay Strategy)
我們將 13 項任務分為三大類，全部綁定於 Docker 的開機生命週期，並利用 `archon_settings` 作為狀態鎖 (State Lock)，確保一致性：

#### 第一類：無狀態高頻巡邏 (Stateless Patrols)
*條件：不查資料庫，Docker 開機健康檢查通過後即刻開始循環。*
1. **`system_probe` (系統心跳探針)**: 開機後 **1 分鐘**首發，之後每 15 分鐘循環。
2. **`log_patrol` (日誌掃描)**: 開機後 **2 分鐘**首發，之後每 30 分鐘循環。
3. **`task_dispatcher` (Agent 自動派單與殭屍任務回收)**: 開機後 **3 分鐘**首發，之後每 30 分鐘循環（解決 Agent 任務卡死）。
4. **`model_verification` (模型狀態驗證)**: 開機後 **4 分鐘**首發，之後每 2 小時循環。

#### 第二類：有狀態每日業務 (Stateful Daily Jobs)
*條件：Docker 開機後，系統檢查 `archon_settings`。**若今天（UTC 日期）尚未執行過，則依序排入相對延遲佇列執行；若已執行過則直接跳過。***
5. **`system_probe_cleanup` (日誌清理)**: 開機後 **5 分鐘**執行（輕量級 DB 操作）。
6. **`alice_auto_fetch` (Alice 拓客抓取)**: 開機後 **6 分鐘**執行（高 AI 消耗）。
7. **`bob_market_report` (Bob 市場報表)**: 開機後 **10 分鐘**執行（高 AI 消耗）。
8. **`prune_stale_leads` (停滯潛在客戶清理)**: 開機後 **15 分鐘**執行（中度 DB 操作）。
9. **`token_analysis` (Token ROI 分析)**: 開機後 **20 分鐘**執行（大數據統計）。
10. **`business_sentinel` (商業警戒哨兵)**: 開機後 **25 分鐘**執行（中度 AI 消耗）。
11. **`daily_executive_summary` (主管戰情摘要)**: 開機後 **35 分鐘**執行（需等待前述報表完成，作為每日壓軸）。

#### 第三類：有狀態雙週維護 (Stateful Bi-weekly Maintenance)
*條件：Docker 開機後，系統檢查 `archon_settings`。**若距離上次執行超過 14 天，則排入相對延遲佇列。***
12. **`tech_debt_audit` (技術債稽核)**: 開機後 **45 分鐘**執行（掃描過期代碼）。
13. **`api_deprecation_scan` (API 棄用掃描)**: 開機後 **50 分鐘**執行（當日高峰任務皆已結束後進行系統健檢）。

### 2. 架構實作細節 (Implementation Details)
* **狀態鎖 (Idempotency Lock)**: 在 `scheduler_service.py` 實作 `@daily_once` 與 `@biweekly_once` 裝飾器或包裝函式，封裝對 `archon_settings` 的檢查邏輯。
* **相對延遲佇列 (Jitter/Delay Queue)**: 使用 `asyncio.sleep()` 或 Scheduler 的 `date` trigger 搭配 `run_date=now + timedelta(minutes=X)`，徹底取代原有的 `IntervalTrigger` 與死板補跑邏輯。

### 3. API Webhook 監控
* 強化 `trigger_cron_jobs` (ops.py / system_api.py)，讓 David (Admin) 能在前端 UI 真實看到這 13 項任務的「上次執行時間」與「下次預定時間」。

## 驗收標準 (Acceptance Criteria)
1. [x] 修改 `scheduler_service.py` 及其子模組，套用全新的一致性相對延遲架構。
2. [x] 證明即使 Docker 在同一天內重啟 5 次，第二類的任務（5~11）當天只會成功執行 1 次。
3. [x] 通過修改後的 `make audit-qa` (包含 Persona Audit)。