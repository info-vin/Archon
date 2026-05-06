# Phase 4.6.51: 全域網路檢索增強與 Google GenAI 硬化 (Universal Web Grounding & Google GenAI Hardening)

> **目標 (Goal)**: 
> 1. **SDK 物理一致性**: 將系統中所有 `google-genai` 調用統一為非同步 (`client.aio`) 模式，消除 FastAPI 事件循環阻塞風險。
> 2. **網路檢索增強 (Web Grounding Expansion)**: 將 Google Search Grounding 整合至行銷部落格與市場洞察工作流，確保 AI 生成內容具備即時性。
> 3. **系統穩定性硬化**: 強化針對 Gemini 429 (Rate Limit) 與 503 (Overloaded) 的自癒重試機制。

---

## 1. 物理對帳與風險評估 (Physical Audit & Risk Assessment)

基於 Phase 4.6.50 的稽核，我們發現 `google-genai` SDK (v0.3.0+) 在以下服務中存在調用不一致與效能隱患：

| 服務名稱 | 檔案路徑 | 目前狀態 | 風險 |
| :--- | :--- | :--- | :--- |
| `WebResearcher` | `web_researcher.py` | ⚠️ **同步** (`client.models`) | 阻塞 API 回應，導致 504 Timeout。 |
| `ContentHandler` | `content_handler.py` | ❌ **混合** (Pitch 為 async, Blog/Logo 為 sync) | 邏輯不對稱，維護成本高。 |
| `RAGService` | `rag_service.py` | 🟢 已封裝 | 僅作為 Coordinator 轉發。 |
| `LibrarianService` | `librarian_service.py` | ⚠️ 內嵌調用 | 缺乏統一的 Token 統計監控。 |

---

## 2. 執行任務 (Implementation Tasks)

### 🧱 基礎建設：Async SDK 歸一化
- [x] **Task 1.1**: 修改 `WebResearcher.py`，將 `client.models.generate_content` 遷移至 `client.aio.models.generate_content`。
- [x] **Task 1.2**: 修改 `ContentHandler.py`，將 `draft_blog` 與 `generate_visual_asset` (Native 路徑) 統一為非同步調用。
- [x] **Task 1.3**: 在 `ContentHandler` 中引入對 `GenerateContentConfig` 的物理驗證，確保 `google_search` 參數傳遞正確。

### 🌐 功能擴展：行銷情報即時化
- [x] **Task 2.1**: 在 `ContentHandler.draft_blog` 中注入 `google_search` 工具，允許 AI 在撰寫部落格時參考最新市場趨勢。
- [ ] **Task 2.2**: 建立 `MarketingGroundingService` 封裝特定的 Web Grounding 策略（如：搜尋特定產業的新聞）。

### 🛡️ 防禦加固：自癒與監控
- [x] **Task 3.1**: 在所有 `google-genai` 調用處實施指數退避 (Exponential Backoff) 重試邏輯。
- [ ] **Task 3.2**: 確保所有非同步任務皆正確掛載 `TokenUsageService.log_usage`，消除漏報風險。

---

## 3. 驗證標準 (Definition of Done)

- [ ] **物理公證**: 使用 `grep` 檢查 `python/src/` 下不再存在 `client.models.generate_content` (應全為 `client.aio.models`)。
- [ ] **功能驗證**: 執行 `WebResearcher` 測試，確認 Google Search Grounding 成功回傳內容且不阻塞。
- [ ] **壓力測試**: 模擬 429 錯誤，驗證重試機制是否能在 15s 內自癒。
- [ ] **Persona 審計**: `make persona-audit` 5/5 全綠。
