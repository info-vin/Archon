# Phase 5.11.21: Oracle Payload Optimization (SSOT & DRY Governance)

## 📌 Context (背景與動機)
在 2026/09/20 的維運中，發現 `NexusOracleAgent` (由 `ReportEnrichmentService` 呼叫) 引發了大量的 `429 API Rate Limit / Overloaded` 錯誤。
經鑑識確認，該 Agent 使用了懶惰查詢 (Lazy Query: `select("*")`) 來獲取 `blog_posts`。因為 8 月 29 日實施了「假資料真實化」，部落格文章被替換為動輒萬字的真實內容，導致 Agent 的單次輸入 Payload 爆增至超過 2.6 萬字元，擊穿了 Gemini API Free Tier 的 Token 限制，造成系統排程崩潰。

## 🎯 Architectural Evolution (架構演進)

為了解決此問題，我們不僅修復了 Bug，更透過 **SSOT (單一事實來源)** 與 **DRY (不重複自己)** 原則償還了 6 月份的技術債：

### 1. 職責對齊 (Role Alignment)
`NexusOracleAgent` 的職責是「Strategic Dashboard Orchestrator」，它只需要盤點「有多少任務等待審核」，而不需要「逐字審閱文章內容」。移除 `content` 等無意義巨型欄位，反而能提升 LLM 的聚焦度，確保討論內容與品質精準契合其業務目標。

### 2. SSOT (Single Source of Truth) - 魔術數字消滅
將 Agent 內部寫死的魔法數字 (`30` 天分析週期、`1000` 字元防禦截斷)，全部抽離至系統的設定中心 `python/src/server/schemas/settings.py` (`OracleConfig`)。
- `ORACLE_TELEMETRY_DAYS`: 決定 Oracle 拉取歷史遙測資料的時間窗（預設 7 天）。
- `ORACLE_MAX_PAYLOAD_LENGTH`: 決定遞迴防禦性截斷的字元上限（預設 1000）。

### 3. DRY (Don't Repeat Yourself) - 封裝資料邏輯
廢除了 Agent 直接裸寫 `supabase.table().select()` 的不良實踐。將精準投影 (Field Projection) 的資料庫語法正確封裝在領域服務層：
- `blog_service.py` -> `get_pending_reviews_metadata()`
- `log_service.py` -> `get_recent_alerts()`

此舉確保了所有跨系統的欄位瘦身邏輯能在 Service 層統一控管。

## 🛡️ Defensive Mechanisms (防禦機制)
- **JSON 遞迴截斷 (Recursive Truncation)**：在向 LLM 發送 Context 之前，動態掃描並截斷所有超過 `ORACLE_MAX_PAYLOAD_LENGTH` 的字串節點，徹底消除未來因為新功能引進巨大字串而導致的 OOM / 429 風險。

## ✅ Verification (零盲猜公證)
- **物理探針 (`scripts.verify_oracle_payload3`)**：已透過探針實體驗證 `BlogService` 與 `LogService` 成功移除了 `content` 等巨型欄位，且 Token 體積縮減率高達 97%。
- **端到端公證 (`make test-be`)**：後端單元測試已公證該變更未破壞任何既有功能。
