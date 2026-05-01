# Phase 4.6.50: 技術債盤點與巨型檔案拆分計畫 (Technical Debt & God Objects Liquidation)

> **目標 (Goal)**: 
> 1. **清除微型死碼**: 安全刪除系統中已經廢棄、不再被引入的過渡期程式碼。
> 2. **建立巨型檔案拆分藍圖**: 針對超過 300 行的「全能型檔案 (God Objects)」建立系統性的拆分指引，降低後續開發的「改 A 壞 B」風險，提升系統可維護性。

---

## 1. 已完成的死碼清理 (Completed Dead Code Cleanup)

基於物理稽核，我們已安全刪除了以下無用或過度封裝的微型檔案，並通過了 559 項測試的相依性驗證：
- [x] ⚛️ `enduser-ui-fe/src/services/api/mockData.ts` (0行，Mock 時期殘留)
- [x] 🐍 `python/src/server/services/provider_discovery_service.py` (5行，舊架構遺留)
- [x] 🐍 `python/src/server/services/stats_service.py` (5行，過度封裝)

*(註：`Skeleton.tsx` 雖小，但由於在 ManagerNexus 中仍有依賴，予以保留。)*

---

## 2. 巨型檔案清單與拆分診斷 (God Objects Audit)

透過 `wc -l` 針對前後端源碼進行行數掃描，我們識別出目前系統中最肥大的 Top 20 檔案。這些檔案是下一階段架構重構的首要目標。

### 🚨 第一梯隊：核心業務巨獸 (> 450 行)
這類檔案承擔了過多職責，違反單一職責原則 (SRP)，是系統中最脆弱的節點。

| 檔案路徑 | 行數 | 職責與拆分建議 |
| :--- | :--- | :--- |
| `librarian_service.py` | 478 | **RAG 處理中樞**。<br>建議將「文件切片 (Chunking)」與「向量庫讀寫 (Vector DB)」拆分為獨立的 Repository。 |
| `agent_service.py` | 476 | **Agent 執行核心**。<br>包含過多 Tool Calls 處理與歷史記錄邏輯，應將工具執行器 (Tool Executor) 抽離。 |
| `projects/task_service.py` | 475 | **任務管理核心**。<br>POBot 相關邏輯雖已拆分，但狀態機與權限校驗仍過於龐大。 |
| `threading_service.py` | 471 | **背景任務管理**。<br>應將 `archon_operations` 的狀態追蹤與更新邏輯獨立。 |
| `ollama/model_discovery_service.py` | 465 | **Ollama 特化**。<br>邏輯獨立但龐大，可進一步細分為網路探測與資料解析子模組。 |
| `main.py` | 464 | **FastAPI 入口**。<br>應將生命週期 (Lifespan) 與 Exception Handlers 拆分到 `core/` 下的獨立檔案。 |
| `admin/IdentityMatrix.tsx` | 453 | **權限管理 UI**。<br>巨大的表格渲染，應將單列 (Row) 抽離成獨立的 `<IdentityMatrixRow />` 元件。 |

### ⚠️ 第二梯隊：複雜業務邏輯與元件 (400 ~ 449 行)

| 檔案路徑 | 行數 | 職責與拆分建議 |
| :--- | :--- | :--- |
| `TaskModal.tsx` | 449 | 前端最複雜 Modal。塞了建任務、改任務、Agent 指派等。應依 Tab 拆分。 |
| `keyword_extractor.py` | 447 | NLP 邏輯。屬於純函式，相對穩定，可考慮依語系拆分。 |
| `credentials/manager.py` | 447 | 金鑰管理。資料庫讀取與加解密混雜，應拆分 DB 存取層。 |
| `ollama/embedding_router.py` | 438 | 路由邏輯。 |
| `search/rag_service.py` | 425 | RAG 整合入口。 |
| `search/agentic_rag_strategy.py` | 409 | 進階 RAG 策略。 |

### 🟡 第三梯隊：前端頁面與次要服務 (300 ~ 399 行)

| 檔案路徑 | 行數 | 職責與拆分建議 |
| :--- | :--- | :--- |
| `storage/document_storage_service.py` | 395 | |
| `ollama/discovery/capabilities.py` | 379 | |
| `stats/metrics.py` | 371 | SQL 聚合邏輯集中地。可考慮依 Domain (Sales, Dev, HR) 拆分。 |
| `LeadsCardStack.tsx` | 368 | 行動版滑動卡片。手勢邏輯應抽成 Custom Hook (`useSwipe.ts`)。 |
| `TeamManagementPage.tsx` | 367 | 團隊管理頁面。人員列表與統計區塊應拆分為獨立組件。 |
| `embeddings/embedding_service.py` | 366 | |
| `Icons.tsx` | 354 | SVG 圖示集中檔。若未來圖示增加，應考慮改用 icon library 或動態引入。 |

---

## 3. 執行策略 (Execution Strategy)

**Phase 4.6.50 不應一次性完成所有拆分**，而是作為一個「還債地圖」。未來的任何 Feature PR (Pull Request) 若涉及到上述檔案，都必須順手進行「童子軍清掃 (Boy Scout Rule)」，將相關的一小塊邏輯剝離出去，逐步降低檔案行數。

### 優先處置目標 (High Priority Targets)
1. **`main.py`**: 作為全系統入口，將 Error Handlers 與 Middleware 抽離，是提高穩定性的第一步。
2. **`TaskModal.tsx`**: 前端最容易產生 Merge Conflict 的地方，必須優先組件化。
3. **`librarian_service.py`**: RAG 系統的心臟，降低耦合度有助於未來串接更多外部知識庫。