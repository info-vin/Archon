# Phase 5.9.14: 雲端原生驗屍報告與架構重構計畫 (Cloud Native Autopsy & Refactoring)

> **目標**: 針對 Hugging Face 正式環境部署所暴露的 7 項系統性致命錯誤進行徹底修復，包含架構死鎖、排程器飢餓、路徑斷層、與 API 併發風暴。

## 🧠 核心架構瓶頸剖析 (The Root Architectural Bottleneck)

這 7 個看似不相關的問題，其實都指向了同一個深層架構瓶頸：**「將『本地單機思維』強行部署到『分散式雲端原生環境』所引發的系統性排斥反應。」**

具體來說，系統在三個維度上遭遇了嚴重的瓶頸：

1. **網路狀態的烏托邦幻想 (The Fallacy of Reliable Networks)**
   - **問題關聯**: #2 (Worker 死鎖), #6 (WAF 封鎖)
   - **瓶頸分析**: 在本地開發時，網路是穩定且被信任的。但到了雲端 (Hugging Face)，IP 會被 104 WAF 視為惡意機器人 (#6)，LLM 網路節點也可能瞬斷不回傳。目前的程式碼完全沒有「網路不可信」的防禦機制 (Defensive Programming)。一旦發生瞬斷，沒有 Timeout 機制的 `await client.create` 就會變成無限期的阻塞 (Blocking)，直接將整個 Worker 執行緒卡死 (#2)。
2. **事件迴圈的資源擠兌與無背壓 (Event Loop Contention & Lack of Backpressure)**
   - **問題關聯**: #3 (Misfire), #4 (併發風暴)
   - **瓶頸分析**: Python 的 `asyncio` 是單執行緒的協程。在本地只有 1~2 個任務時一切正常。但當排程器啟動，瞬間湧入大量商機時，`sentinel_patrol` 像無底洞一樣使用 `create_task` (#4)，導致數十個 HTTP 請求瞬間霸佔了 Event Loop。這引發了嚴重的「資源擠兌 (Resource Starvation)」，導致 APScheduler 的心跳 (Tick) 延遲超過 1 秒，直接判定其他排程任務 Misfire 被丟棄 (#3)。系統缺乏了至關重要的「背壓 (Backpressure)」機制與併發閥門 (Semaphore)。
3. **違反 12-Factor App 的環境耦合 (Violation of Environment Isolation)**
   - **問題關聯**: #1 (排程鎖毒性共用), #5 (路徑斷層), #7 (硬編碼)
   - **瓶頸分析**: 系統沒有徹底實現「狀態與環境分離」。開發者在本地測試時的狀態，直接污染了雲端的生產資料庫 (#1)；程式碼天真地假設了容器內的資料夾結構與本地一致 (`../AGENTS.md`) (#5)；甚至為了求快，把 RAG 數量寫死在業務邏輯裡 (#7)。這些都是將環境上下文 (Context) 與代碼 (Code) 高度耦合的技術債。

**總結**：要徹底解決這 7 件事，不能只是「修 Bug (改代碼)」，而是必須在架構層面上引入 **防禦性超時 (Defensive Timeout)、併發背壓 (Backpressure)、以及環境變數隔離 (Environment Isolation)**。

---

## 📊 災難重要性與嚴重度分析 (Severity & Impact Analysis)

| 排名 | 問題點 | 嚴重度 | 發生頻率 | 影響範圍 | 根本原因與追查結果 (RCA) |
| :--- | :--- | :---: | :---: | :--- | :--- |
| **#1** | **排程鎖毒性共用 (Shared State Toxicity)** | **CRITICAL** (10/10) | 100% | **全系統癱瘓**。正式環境的所有週期任務皆被跳過。 | 缺乏環境變數隔離。開發者本地測試寫入的 DB `LAST_RUN`，直接毒殺了生產環境的排程狀態。 |
| **#2** | **Worker 死鎖 (Agent Deadlock)** | **CRITICAL** (9/10) | 高 | **資源枯竭**。Agent 卡死後不釋放資源，癱瘓 `worker_service`。 | **經查證，此 Bug 與昨日 (Phase 5.9.13) 的 HITL 無關。** MarketBot 走的是 `DefaultLLMStrategy`，死鎖純粹是因為底層 LLM SDK 缺乏 Timeout 參數。 |
| **#3** | **Event Loop 飢餓與 Misfire** | **HIGH** (8/10) | 尖峰時段 | **事件遺失**。下游報表任務無法產出。 | `apscheduler` 容錯期僅 1 秒。同步阻塞或高併發導致 Event Loop 延遲。 |
| **#4** | **API 併發風暴 (Concurrency Storm)** | **HIGH** (8/10) | 100% | **API 額度鎖死**。瞬間 16 個 RAG 查詢塞爆 Free Tier 限額。 | `sentinel_patrol` 在迴圈中無腦使用 `asyncio.create_task`，缺乏 Semaphore 控制。 |
| **#5** | **Docker 容器路徑斷層 (`AGENTS.md`)** | **HIGH** (7/10) | 100% | **觸發 Fallback 機制**。 | 寫死了 `../AGENTS.md`。系統確實有 Fallback 機制，但錯誤的路徑仍需修復以恢復精準度。 |
| **#6** | **Hugging Face IP 遭 104 WAF 封殺** | **MEDIUM** (6/10) | 幾乎 100% | **商機漏斗斷水**。 | `curl_cffi` 雖能繞過 TLS 指紋檢查，但 **無法繞過 IP 信譽檢查**。 |
| **#7** | **虛假的 RAG 搜尋結果 (全回傳 2 筆)** | **MEDIUM** (5/10) | 100% | **AI 幻覺與資訊失真**。 | 經查證，`ai_operations.py` 中將 RAG 的 `match_count=2` **寫死 (Hardcoded)**，導致所有結果皆固定回傳 2 筆，這違反了 SSOT 原則。 |

---

## 🛠️ 具體修復計畫與 SSOT 守則 (Proposed Solutions)

### [Component: 排程器與狀態鎖 (Scheduler & State)]
#### [MODIFY] `scheduler_service.py`
- **修復邏輯 (#1)**：為避免引發正式環境的「大補跑」，透過讀取環境變數 `os.environ.get("ARCHON_ENV", "")` 作為前綴 (`ENV_PREFIX`)。本地端開發時設定為 `DEV_`，正式機為空字串。
- **修復 Misfire (#3)**：加入 `job_defaults={'misfire_grace_time': 60}`，給予 Event Loop 充裕的緩衝時間。

### [Component: Agent 執行緒 (Agent Worker)]
#### [MODIFY] `dispatcher.py`
- **修復死鎖 (#2)**：在 `DefaultLLMStrategy` 中，將 API 呼叫加上嚴格的非同步超時機制 `asyncio.wait_for(..., timeout=300)`。

### [Component: 巡檢員併發控制 (Sentinel Patrol)]
#### [MODIFY] `sentinel_patrol.py`
- **修復併發風暴 (#4)**：引入 `asyncio.Semaphore(3)` 限制最高併發數為 3，並改用 `asyncio.gather` 取代無控的 `create_task`。

### [Component: 檔案系統路徑 (Filesystem Paths)]
#### [MODIFY] `job_board_service.py`
- **修復硬編碼路徑 (#5)**：**絕不硬編碼！** 改用動態模組路徑定位法：`PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent.parent`。

### [Component: 爬蟲與 WAF (Crawling & WAF)]
#### [MODIFY] `job104_client.py`
- **真實世界解法 (#6)**：引入環境變數 `CRAWLER_PROXY_URL` 作為 SSOT 防禦。當 WAF 阻擋時自動切換 Proxy 請求。

### [Component: AI 操作與 RAG (AI Operations & RAG)]
#### [MODIFY] `ai_operations.py`
- **修復虛假搜尋與硬編碼 (#7)**：移除 `match_count=2` 的硬編碼，改為從資料庫讀取 SSOT 設定：`int(SettingsService().get_setting("SENTINEL_RAG_MATCH_COUNT", "2"))`。

---

## 🧪 物理公證與驗證計畫 (Verification Plan)

拒絕虛假開發，我們將透過以下具體測試確保每一項修復都產生真實的物理改變：

1. **驗證 #1 (排程鎖)**: 啟動本地伺服器，查詢 Supabase `archon_settings` 資料表，確認成功寫入 `DEV_LAST_RUN...`。
2. **驗證 #2 (Worker 死鎖)**: 使用 Mock 卡死 LLM 回應 (如 `asyncio.sleep(301)`)，斷言系統能拋出 `TimeoutError`。
3. **驗證 #3 (Misfire)**: 在任務執行前手動 `time.sleep(2)` 模擬阻塞，確認事件在 60 秒寬限期內仍會成功發動。
4. **驗證 #4 (併發風暴)**: 從日誌的時間戳 (Timestamp) 物理確認 RAG 查詢是「一次 3 筆」的批次進行。
5. **驗證 #5 (路徑斷層)**: 使用 Docker 啟動服務，執行 `make audit-qa` 確保沒有拋出 `[Errno 2]` 錯誤。
6. **驗證 #7 (RAG 硬編碼)**: 進入資料庫將 `SENTINEL_RAG_MATCH_COUNT` 改為 `4`，斷言系統精準回傳 4 筆結果。

---

## 🟢 執行結果與進度更新 (Status & Progress Update)
- **Status**: **COMPLETED (2026-07-23)**
- **Notes**: 
  - 所有的 7 項修復已全數實作，並透過 `make test-be` (612 項測試全數通過) 進行物理公證。
  - Pydantic SSOT 原則已被嚴格落實，`ai_operations.py` 已改用 `RagConfig.model_validate()` 取代字串 Key 硬編碼。
  - 整合測試 `test_agent_timeout.py` 成功證明 `asyncio.wait_for` 攔截了死鎖情境。
  - 程式碼已成功推送至 `feat/twins` 分支。
