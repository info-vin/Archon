# Phase 5.9.9: 事件驅動排程器 (Event-Driven Scheduler) 重構

> **狀態**：Approved (準備執行)
> **目標**：解決排程器遇錯「射後不理」的脆弱性，將原本死板的 Cron 定時器重構為「資料驅動」的串接架構，杜絕上游重試時下游提早空轉的斷層。

## 1. 歷史考古與根本原因分析 (Why Time-Driven?)
經過對 `git log` (包含 `e9474827`, `51a49b94`, `3193b280`) 與 `GEMINI.md` 的深度追溯，我發現系統之所以被設計為「定時驅動 (Time-Driven)」，有其深刻的演進歷史與不得已的技術包袱：

1. **Phase 5.1.14 (Thundering Herd 危機)**: 最初系統為了防範每天手動開關 Docker 造成的瞬間併發危機（雷鳴群效應），設計了「Docker 生命週期驅動」。透過計算開機後的**相對延遲時間**（例如開機後 6 分鐘跑 A、開機後 10 分鐘跑 B）來強行錯開任務。
2. **Phase 5.5.10 (Hugging Face 雲端化)**: 當系統遷移至 Hugging Face Space (24/7 運行) 時，失去了每天「Docker 開機」這個唯一的觸發點。為了解決不關機就不會跑的問題，架構師硬生生將「相對延遲」轉換成了**「絕對定時 (Cron)」**（07:00 跑 A, 07:20 跑 B, 07:40 跑 C）。這也就是目前架構中 `_schedule_stateful_daily` 等方法的由來。
3. **Phase 5.9.8 (Tenacity 災難)**: 為了抵抗 104 WAF，我們在剛剛加入了長達數小時的 `tenacity` 彈性退避重試。這徹底摧毀了 Phase 5.5.10 寫死的定時鎖鏈。當 A 任務（07:00）因為 WAF 延遲到 10:00 才成功時，B 任務（07:40）與 C 任務（08:00）早就對著空資料庫空轉結束了。

**結論**：我們正處於新舊架構的摩擦期。系統具備了雲端等級的單點容錯 (`tenacity`)，卻依然使用著石器時代的定時鏈條 (`Cron`)。

## 2. L2 重構計畫：從定時 (Cron) 走向資料流 (Data-Driven)

為徹底解決資料競態問題，我們需要導入「微型事件/任務相依 (Mini-DAG)」架構，解除業務模組與時間的強耦合。

### A. 剝離下游任務的 Cron 排程
- **目標檔案**: `scheduler_service.py`
- **行動**: 將 `bob_market_report`, `daily_executive_summary` 從每日固定時間 (07:40, 08:00) 的 CronTrigger 註冊中移除。
- **保留**: 只保留最源頭的觸發點 `alice_auto_fetch` 於 07:00 觸發，以及與爬蟲無直接依賴的 `business_sentinel` 和 `token_analysis` 等任務保持 Cron。

### B. 實作事件串接 (Event Chaining)
- **行動**: 將下游任務的呼叫，直接掛載至上游任務的**尾端**。
- **具體流程**:
  1. `run_auto_fetch_leads()` 成功寫入資料庫後 ➡️ 主動呼叫 `await self._run_daily_market_report()`
  2. `run_daily_market_report()` 成功產出報告後 ➡️ 主動呼叫 `await self._run_daily_executive_summary()`
  3. 若 `alice_auto_fetch` 遭遇 WAF 進入 `tenacity` 重試，整個鏈條會自動暫停，直到爬蟲成功，後續的報告才會依序生成。
- **業務邏輯相容**: 根據使用者指示：「如果今天都沒有104, 應該隔一天的日報會說明沒有新資料」。若 `alice_auto_fetch` 5 次重試皆失敗拋錯，鏈條會中斷，當天將不會產出無用的日報。隔天 07:00 重新觸發後，若成功則會一併統整。

### C. 保留手動觸發相容性與狀態鎖
- **防禦機制**: 由於我們仍然保留 `scheduler_service._run_daily_market_report` 等方法，前端/後端 API（如 `admin_api.py` / `internal_api.py` 的手動觸發 endpoint）**依然可以單獨調用這些功能，完全不受影響**。
- **防禦機制 2**: 由於依然使用 `LAST_RUN` DB 鎖 (`_should_run_daily`)，即使 Docker 重啟觸發了 Catch-up 機制，或是 `alice_auto_fetch` 在同一天內被外部手動重複觸發，下游任務若今天已經完成過，就會被 DB 狀態鎖安全擋下，保證每日只發送一次報告。

## 3. 自動化驗證計畫 (避免改 A 壞 B)
- **安全重構**: 不修改 `leads_patrol.py` 等業務檔案內部的商業邏輯，僅修改 `scheduler_service.py` 中的調用順序與裝飾器綁定。
- **執行 `make test-be`**: 確保拔除定時器後沒有破壞現有的單元測試（包含 API 端點與舊有的排程測試）。
