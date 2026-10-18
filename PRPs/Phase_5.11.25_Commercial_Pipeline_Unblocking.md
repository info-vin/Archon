# Phase 5.11.25: 商業漏斗全線通管 (Alice 痛點評分、Sentinel 429 防爆、Bob 自動發布與 Telegram 精準交付)

## 📌 背景與動機 (Context & Motivation)

在歷經深度系統現況鑑識後，確認了目前系統存在的「假象繁榮、實則卡死」之四大連鎖痛點：
1. **上游 (Alice)**：算出了 RAG 相似度，存檔時卻丟棄分數，全數硬編碼成 `new`，導致 `leads` 庫內 188 筆資料的分數全為 `0.00`，下游無法識別優質名單。
2. **中游 (Sentinel)**：14 天休眠巡檢瞬間將數十筆休眠線索並發丟給 Gemini 撰寫萬字喚醒方案，衝破 250,000 Token 上限，引發 429/503 死亡循環並產出 500+ 筆無人認領的吃灰工單。
3. **下游 (Bob)**：產出的市場情報文章永遠停留在 `review`/`draft`，導致 Sentinel 狂噴 `Content Bottleneck` 警報洗板。
4. **終端 (Delivery)**：未將高意向合格名單（Qualified Leads）透過 Telegram 推播給人類業務，導致轉換率永久為 0%。

本階段核心目標：**執行「全線通管四部曲」，一次性理順端到端業務流水線，徹底根除 429 死亡循環與內容發布死鎖。**

---

## 🎯 核心實作目標與防線 (Core Objectives)

### 1. Alice 痛點分數真實沉澱 (`job_board_service.py`)
- **實作規範**：
  1. 將 RAG Cosine 相似度轉換為 0~100 整數分數（`int(sim * 100)`），真實寫入 `leads.enrichment_score`。
  2. 若分數 `>= 75` 且通過 `llm_judge`，狀態標記為 `qualified`（高意向合格名單）；分數 `< 75` 者直接標記為 `archived`，不再混為一團。
  3. `enrichment_status` 同步更新為 `completed`。

### 2. Business Sentinel 防爆與限流 (`sentinel_patrol.py`)
- **實作規範**：
  1. 嚴格限制單次巡檢喚醒上限：每天最多僅處理 **Top 3 筆** 高分（`order('enrichment_score', desc=True)`）的休眠線索。
  2. 停止自動產生無負責人的垃圾 Todo 工單，改為直接記錄結構化戰略日誌至 `archon_logs`。

### 3. Bob 自動發布與瓶頸解鎖 (`sentinel_patrol.py` / `blog_service.py`)
- **實作規範**：
  1. 解除 `review` 卡滯：在 `sentinel_patrol.py` 的 Content Bottlenecks 巡檢中，針對處於 `review` 超過 24 小時、`ai_score >= 80` 且無違規的合法文章，自動更新狀態為 `published` 並寫入 `publish_at`。
  2. 徹底消滅 `Content Bottleneck` 報警洗板。

### 4. Telegram 高意向名單戰鬥簡報交付 (`leads_patrol.py` / `telegram_service.py`)
- **實作規範**：
  1. 每週日/每日排程產出 Market Intelligence 時，篩選出當期 `qualified` 名單（附 104 職缺原始連結與痛點分析）。
  2. 調用已上線的 `telegram_service.send_message` 智慧分段推播，將戰鬥簡報完整交付給人類指揮官/業務。

---

## 🛡️ 物理公證防線 (Zero Fake Verification)

1. **單元測試全綠覆蓋**：
   - 針對 Alice 分數計算與狀態寫入撰寫單元測試。
   - 針對 Sentinel Top 3 限制與 Bob 自動發布撰寫單元測試。
   - 針對 Telegram 推播組裝撰寫單元測試。
2. **三向品質門禁**：
   - `make lint-be`: 393 source files 100% 通過（Ruff + MyPy 零錯誤）。
   - `make test-be`: 774+ passed 全數通過。
   - `make phase-audit`: Step 1 ~ Step 11 全綠。
