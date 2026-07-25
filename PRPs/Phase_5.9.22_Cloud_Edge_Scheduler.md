# Phase 5.9.22: Cloud-Edge Scheduler Architecture

## 1. 核心問題 (Problem Statement)
目前 `alice_auto_fetch` (104 爬蟲任務) 每天 07:00 執行。
由於專案部署於 Hugging Face (HF)，其 Data Center IP 會被 104 的 Cloudflare WAF 100% 阻擋，導致每次爬蟲皆回報 0 筆資料 (0 leads)，徒增伺服器資源浪費與無效的錯誤日誌。
此外，使用者週末通常不會開機，導致本機端 (Local) 的排程與補跑機制 (Catch-up) 無法有效發揮作用，進而引發資料斷層。

## 2. 架構設計 (Architectural Solution)
為了解決此問題，我們正式導入 **雲地分工架構 (Cloud-Edge Architecture)**，讓不同的執行環境各司其職：

### 2.1 HF 專注於大腦運算 (Cloud for AI/Processing)
*   **機制**：排程器將偵測環境變數 `SPACE_ID`。若偵測到執行環境為 Hugging Face，將直接跳過 `alice_auto_fetch` 任務，**且不更新資料庫的 `LAST_RUN` 狀態**。
*   **效益**：避免去撞 WAF，並將當天的「爬蟲執行票券」保留給本機端。
*   **注意**：此限制**僅適用於** `alice_auto_fetch`。其他無 WAF 限制的 AI 任務 (如 `token_analysis`, `weekly_executive_summary` 等) 仍會在 HF 上如常運作。

### 2.2 本機專注於資料獲取 (Edge for Data Fetching)
*   **機制**：排程時間延後至每天 **10:30**。本機端 (無 `SPACE_ID`) 擁有乾淨的家用 IP，能順利繞過 WAF。
*   **彈性補跑 (Catch-up)**：
    *   平日：使用者開機後，若已過 10:30，系統會自動觸發 Catch-up 將今天的資料補齊。
    *   週末：系統維持「每日 (Daily)」排程。若使用者週末沒開機，系統採 **Skip and Wait** 策略自然放水流 (不觸發、無錯誤通知)；若使用者週末碰巧開機，系統依然能透過 Catch-up 自動執行爬蟲。

## 3. 效能與參數調整 (Performance & Settings)
不再為了 HF 的 WAF 而妥協，將本機的爬蟲效能最大化：

1.  **動態調整抓取數量限制 (`CRAWLER_JOB_LIMIT`)**
    *   考量週末可能因未開機而產生資料空窗，我們必須在平日「多存糧」。
    *   將 `settings.py` 中的預設值 (原為 4) 依照 1.5 倍的策略提升至 **6**。*(註：此數值由設定檔動態管理，非硬編碼於邏輯中)*。
2.  **解除 WAF 延遲封印 (`CRAWLER_WAF_DELAY_MIN` / `MAX`)**
    *   將針對 WAF 的長時間延遲 (60~90秒) 恢復至流暢的 **3.0 ~ 7.0 秒**。

## 4. 預期效益 (Expected Outcomes)
*   **零無效日誌**：徹底消除 `archon_logs` 中每日一筆的 WAF Block 警告。
*   **無感容錯**：週末不開機也不會導致系統報錯，下游報告任務會優雅靜默。
*   **資料充裕**：平日的高吞吐量 (1.5x) 能確保 HF 在週末生成 AI 摘要時有豐富的養分。
