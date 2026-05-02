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

### 技術債分拆地圖 (Responsibility-Based Refactoring Roadmap)

我們採用「梯隊 (Tier)」作為重構順序的決策依據，確保資源投入與系統健康度、業務職責緊密對齊。

| 梯隊 | 檔案路徑 | 行數 | 職責領域 (Duty Area) |
| :--- | :--- | :--- | :--- |
| **一** | ~~`python/src/server/services/threading_service.py`~~ | ✅ 471 | 核心併發與任務調度 |
| **一** | ~~`python/src/server/services/search/rag_service.py`~~ | ✅ 425 | 檢索增強生成 (RAG) 核心邏輯 |
| **一** | ~~`python/src/server/services/search/agentic_rag_strategy.py`~~ | ✅ 409 | 代理人 RAG 策略與決策鏈 |
| **二** | `enduser-ui-fe/src/features/admin/components/IdentityMatrix.tsx` | 453 | 管理員 RBAC UI 權限矩陣 |
| **二** | `python/src/server/services/credentials/manager.py` | 447 | 金鑰安全管理 |
| **二** | `enduser-ui-fe/src/features/marketing/components/LeadsCardStack.tsx` | 368 | 行銷 Leads 轉化視覺呈現 |
| **二** | `enduser-ui-fe/src/pages/TeamManagementPage.tsx` | 367 | 團隊職責管理與狀態 |
| **二** | `enduser-ui-fe/src/features/admin/components/SystemHealthDashboard.tsx` | 312 | 系統物理健康指標面板 |
| **三** | ~~`python/src/server/services/search/keyword_extractor.py`~~ | ✅ 447 | 文字探勘與特徵詞提取 |
| **三** | `python/src/server/services/storage/document_storage_service.py` | 395 | 檔案儲存層與索引 |
| **三** | `python/src/server/services/embeddings/embedding_service.py` | 366 | 向量轉換與空間對應 |
| **三** | `python/src/server/services/crawling/document_storage_operations.py` | 358 | 爬蟲儲存與物理路徑對齊 |
| **三** | `python/src/server/services/stats/metrics.py` | 371 | 效能統計 |
| **三** | `python/src/server/services/storage/code/extraction.py` | 322 | 程式碼片段自動化提取 |
| **三** | `python/src/server/services/knowledge/knowledge_summary_service.py` | 310 | 知識庫摘要邏輯 |
| **三** | `enduser-ui-fe/src/features/manager/components/OpLoadPanel.tsx` | 318 | 營運負載動態監控 |
| **四** | `python/src/server/services/ollama/model_discovery_service.py` | 465 | Ollama 模型探索 |
| **四** | `python/src/server/services/ollama/embedding_router.py` | 438 | Ollama 向量路由 |
| **四** | `python/src/server/services/ollama/discovery/capabilities.py` | 386 | Ollama 能力偵測 |

---

## 4. 功能斷層與未來功能 (Identified Feature Gaps)

在盤點 `task_service.py` 與 RBAC 架構時，我們發現了一個關鍵的業務斷層，需在後續階段補齊：

- **Agent 協作功能 (Collaborative Agent Assignment)**:
  - **現況**: 目前的任務所有權是「互斥的」，單一任務只能指派給人類 (如 Bob) **或**單一 AI Agent。
  - **目標**: 實作主副負責人 (或協作者) 機制。允許任務的主負責人為人類，但同時能指定 AI Agent (如 MarketBot) 作為「協作者 (Collaborators)」自動介入提供協助。
  - **影響範圍**: 屬於跨全端的大型 Feature，需修改資料庫 (`archon_tasks` 擴充 `collaborator_agent_ids` 欄位)、後端 (`ops.py`, `task_service.py`) 以及前端 (`TaskModal.tsx` 新增獨立的 AI Assistant 選擇器)。