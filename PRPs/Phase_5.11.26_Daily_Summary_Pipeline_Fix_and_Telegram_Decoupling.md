# Phase 5.11.26: 系統日報流水線解耦與 Telegram 作答推播治理 (Daily Summary Pipeline Fix & Telegram Decoupling)

## 📌 背景與動機 (Context & Motivation)

在 2026-10-19 16:18 系統例行執行「每日執行摘要 (Daily Executive Summary)」時，Telegram 推播了大量包含 429、400 錯誤代碼與 JSON Stacktrace 的混亂訊息。

經排查資料庫日誌與任務執行歷史，鑑識出核心架構問題：
1. **考卷題目誤當作成果推播**：
   - [report_service.py](file:///Users/vincenta/GoogleKwok022/Archon/python/src/server/services/report_service.py) 在派發 Daily Summary 任務時，將內含 8 則歷史異常日誌（昨天除錯產生的舊日誌）的原始 Prompt 上下文（`task_desc`）直接組裝為 Telegram 訊息送出。
2. **非同步競態導致提早交卷**：
   - 程式在派發 Agent 後（`dispatch_agent=True`），未等待 Agent 執行，下一行立即發送 Telegram，並宣稱「星環 Daily 已產出」。
3. **Agent 成果遭遺忘**：
   - Supervisor Agent（Charlie）在派發 19 秒後即精準將 8 則日誌歸納為 2 項重點並存入 `attachments`，但因系統在第 0 秒已提早交卷，Agent 實際的分析結果**從未推播給 Telegram**。
4. **Markdown 實體解析崩潰與連鎖警報**：
   - 原始堆疊中的特殊字元引發 Telegram `400 Bad Request: can't parse entities`，觸發 Plain Text 降級，並在 7 分鐘後被巡檢員誤判為系統故障，引發 `Auto-Repair` 假警報工單。

---

## 🎯 核心實作目標與防線 (Core Objectives)

### 1. Daily Summary 執行流水線對齊 (`report_service.py`)
- **實作規範**：
  1. **禁止在任務派發前推播假完成訊息**：當 `dispatch_agent=True` 時，`_create_summary_task_and_log` 絕不發送「星環 Daily 已產出」的 Telegram 通知。
  2. **端到端直接生成模式 (Direct Summary Generation)**：
     - 比照 Weekly/Monthly Summary 的模式，在派發與推播前，調用 Supervisor Agent / LLM 獲取真正的 `summary_output`。
     - 或在 Agent 完成任務（`save_agent_output`）時，透過回呼勾點（Hook）將最終結構化作答（`output["content"]`）推播至 Telegram。
  3. 確保推播至 Telegram 的內容 100% 為 **Agent 的總結作答**，絕不包含「請啟動星環群聊...」等 Prompt 題目與原始未脫敏日誌。

### 2. 日誌上下文脫敏與結構化防護 (`report_service.py`)
- **實作規範**：
  1. 在 `_get_logs_context` 中，針對 `ALERT` 與 `ERROR` 進行摘要脫敏：
     - 截斷過長且包含特殊符號的 URL / JSON 請求體。
     - 訊息一律包裹於行內代碼塊（`` ` ``）或進行 Markdown 轉義，防止未成對的底線 `_` 炸裂 Telegram 解析器。
     - 若為重複性錯誤（如連續 429），進行次數聚合（例：`RateLimitHit x5`），避免日誌膨脹。

### 3. Telegram 推播實體轉義硬化 (`telegram_service.py`)
- **實作規範**：
  1. 在發送 `parse_mode="Markdown"` 前，對常見破壞 Markdown 樹狀結構的字元進行防禦性安全檢查。
  2. 若遇到 400 回退至 Plain Text，記錄 WARNING 而非 ERROR，避免引發 Clockwork 的 `error_patrol` 誤報自癒死循環。

---

## 🛡️ 物理公證防線 (Zero Fake Verification)

1. **單元測試全綠覆蓋**：
   - 驗證 Daily Summary 任務建立時不提早發送未作答的 Prompt。
   - 驗證 Agent 作答成果正確作為 Telegram 訊息內文推播。
   - 驗證 `_get_logs_context` 脫敏後的格式不包含破壞性 Markdown 符號。
2. **三向品質門禁**：
   - `make lint-be`: 393 source files 100% 通過。
   - `make test-be`: 780+ passed 全數通過。
   - `make phase-audit`: Step 1 ~ Step 11 全綠。
