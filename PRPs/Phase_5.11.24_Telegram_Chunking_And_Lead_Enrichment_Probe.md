# Phase 5.11.24: Telegram 長訊息智慧分段發送 (防啞巴) 與真實潛客官網探針 (零虛假開發)

## 📌 背景與動機 (Context & Motivation)

在近期系統運行與週期性週報檢視中，發現了兩大嚴重阻礙商業閉環與使用者體驗的架構缺陷：
1. **Telegram 長訊息截斷與啞巴降級 (Truncation & Silent Mute)**：
   Telegram API 對單則訊息有 4,096 字元硬上限。目前系統僅將文字粗暴截斷至 150 字或直接發送導致長報告（如週報、日報、系統架構稽核）在使用者端「看到一半中斷」，或因 400 錯誤被拋棄造成「系統自以為送出、實際上使用者收不到的啞巴狀態」。
2. **潛客聯絡資訊虛假殘留與 Outreach 斷鏈 (Fake Enrichment & Broken Funnel)**：
   目前資料庫中積累了 44 筆客製化「喚醒潛客方案」，但 `leads` 資料庫內的 `contact_email` 全數為 `None`。過去的代碼（`enrichment_service.py`）充斥著 `mock_email = contact@company.com` 的「虛假開發」殘留。系統空有方案卻無處可寄，導致線索轉換率永遠停留在 0%。

本階段核心目標：
- **徹底修復 Telegram 訊息智慧分段（Auto-chunking 4096-limit）**：以段落為邊界切割、帶有分頁標記與速率間隔，嚴禁虛假 Fallback 與靜默吞噬。
- **以輕量真實探針驗證官網/Email 探測可行性**：遵循《探針先行與零虛假開發》鐵律，拒絕 FSW（Full-Scale Workflow 龐大失控腳本），用最簡探針實體驗證真實企業公開聯絡資訊獲取流程。

---

## 🎯 核心實作目標與防線 (Core Objectives)

### 1. Telegram 長訊息智慧分段發送器 (Chunking without Silent Mute)
- **實作檔案**：`python/src/server/services/system/telegram_service.py`
- **架構規範**：
  1. **段落安全切割 (`split_message_chunks`)**：
     - 上限設定為 **3,800 字元**（預留 296 字元防止 Unicode/Emoji 與 Markdown 格式長度膨脹）。
     - 優先在雙換行 (`\n\n`) 或單換行 (`\n`) 切割，絕不粗暴在字詞或標籤中間硬切。
     - 當訊息被拆分成多段時，自動追加頁碼標題（如 `📄 [1/3]`、`📄 [2/3]`）。
  2. **防啞巴與防刷頻發送邏輯**：
     - 分段訊息依序發送，每段間隔 `0.5s`（`await asyncio.sleep(0.5)`），防止觸發 Telegram 頻率限制。
     - 若其中任一段失敗，**嚴禁返回 True 假裝成功**，必須如實拋出異常、重試或寫入失敗持久化佇列 (`archon_tasks`)。

### 2. 潛客官網/Email 真實探針 (< 30 行輕量探針，拒絕 FSW)
- **實作檔案**：`scratch/probe_real_lead_website.py`
- **架構規範**：
  1. 挑選 1 筆真實線索（例如「台北數位集團」）。
  2. 透過合法的搜尋/公開工商資料端點，查詢其公開官網網址。
  3. 讀取該官網公開首頁/聯絡頁 HTML，以正規表達式探測其公開聯絡信箱。
  4. 輸出真實獲取的 `website` 與 `email`，**不寫入主庫、不修改業務代碼、拒絕龐大失控邏輯**，僅作為可行性實體證據。

---

## 🛡️ 物理公證防線 (Zero Fake Verification)

1. **Telegram 分段實體單元測試**：
   - 於 `python/tests/services/test_telegram_persistence.py`（或新建 `test_telegram_chunking.py`）中：
     - 測試超過 8,000 字元的超長 Markdown 文本。
     - 實體驗證切割後產生的 chunks 數量與字數皆 `<= 3800`。
     - 驗證頁碼標籤與 HTTP 呼叫次數完全吻合。
     - 驗證當第一段成功、第二段 502 失敗時，系統**不會靜默吞噬**，能正確觸發佇列或日誌。
2. **全域門禁公證**：
   - `make lint-be`: 393 source files 100% 通過（Ruff + MyPy 零錯誤）。
   - `make test-be`: 769+ passed 全部綠燈。
   - `make phase-audit`: Step 1 ~ Step 11 全綠。
