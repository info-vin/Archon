# Phase 4.6.6：人機協作專家演進 (Expertise Loop Realization)

> **狀態**: 規劃中 (PLANNING)
> **目標**: 實作專家矩陣，將人類行為轉化為系統知識資產。

## 1. 落地實作路徑 (Implementation Paths)

### 1.1 Alice：失敗教材收割 (Expertise from Failure)
*   **目標**: 將「丟單」轉化為「避雷指南」。
*   **實作**: 
    *   擴充 `LeadUpdate` 模型，加入 `lost_reason` 欄位。
    *   在 `PATCH /leads/{id}` 邏輯中，偵測狀態變更。
    *   當轉為 `LOST` 時，由 `LibrarianService` 執行 `archive_failure_case`，將失敗原因向量化存入 `knowledge_items`。

### 1.2 Bob：審核意見強化 (Reinforcement from Feedback)
*   **目標**: 讓 Agent 學會 Charlie 經理的品味。
*   **實作**:
    *   修改 `process_approval`。
    *   將 `review_notes` 內容提取關鍵詞（例如：太口語、數據不足）。
    *   自動將這些約束寫入向量庫的 `brand_voice` 分類。
    *   **MarketBot** 在執行 RAG 時，強制檢索該分類以獲得「寫作禁忌清單」。

### 1.3 DevBot：整合創意引擎 (Creative Design Hardening)
*   **目標**: 整合 `logo_tool` 與 **Nana Banana**。
*   **實作**:
    *   重構 `LogoRequest` 以支援 `mode: 'vector' | 'creative'`。
    *   `vector` 模式：維持目前的 SVG 生成（適合開發）。
    *   `creative` 模式：呼叫 `imagen-3.0` 或 `gemini-2.0-flash-exp` 生成高品質品牌圖。
    *   統一由 DevBot 作為單一入口進行資源調度。

### 1.4 RAG：知識實時感知 (Live Knowledge Injection)
*   **狀態**: 已完成 (COMPLETED)
*   **實作**: 
    *   在 `RAGService.perform_rag_query` 中加入 `filter` 參數與 `min_score`。
    *   Bob 的 `draft_blog_post` 已帶入 `min_score=0.25` 篩選，優先命中 `knowledge_api` 產出的 `technical` 與 `market_intel` 標籤。
### 1.5 DevBot：規範驅動自癒 (SOP-Driven Self-Healing)
*   **狀態**: 已完成 (COMPLETED)
*   **實作**: 
    *   `AgentService` 現在具備「規範先行」修復鏈，修復前自動檢索 Librarian 中的 SOP。
    *   **治理機制**: 引入了基於 Poisson 分佈的 **「成功驅動晉升模型」**。Agent（DevBot, MarketBot）必須累積足夠的成功紀錄（如 L1 > 500 次）才能解鎖更高風險的重構權限。
    *   **全量驗證**: 自癒迴圈現在強制包含 FE/BE 雙端靜態掃描與單元測試核對。

### 1.6 Charlie：治理與政策注入 (Governance & Policy Injection)
*   **目標**: 透過經理權限，注入高階開發規範與技術底座知識。
*   **實作**:
    *   **配置化爬蟲**: Charlie 透過 `crawler_rbac_settings` 管理全系統的技術掃描任務，將外部 SDK 文檔自動轉化為 RAG 知識。
    *   **政策定錨**: 所有經由經理上傳的文件（如 `CONTRIBUTING.md`, `SECURITY.md`）自動獲得 `authority_level: high` 標籤。
    *   **聯動價值**: 當 DevBot 在進行自癒時，會優先權衡 Charlie 注入的「專案政策」，確保修復路徑符合公司規範。

### 1.7 遞迴進化：從重構到規範生成 (Meta-Evolution)
*   **目標**: 讓系統具備「自我診斷重構需求」與「自動總結成功經驗」的能力。
*   **落地細節**:
    1.  **重構等級自動判定 (Refactor Severity Grading)**:
        *   DevBot 具備掃描代碼庫的診斷技能，根據以下指標自動判定技術債等級：
            *   **🟢 Level 1 (Minor)**: 僅 Lint 錯誤。處置：就地修復。
            *   **🟡 Level 2 (Moderate)**: 檔案行數 300-500 行，邏輯耦合。處置：提議抽離 Helper。
            *   **🔴 Level 3 (Critical)**: 檔案 > 500 行 (如 `stats_api`), 包含複雜 SQL。處置：**強制 Service 層剝離**。
    2.  **5173 觸發路徑 (Trigger Paths)**:
        *   **主動指派**: Charlie 在 5173 的「任務管理」建立優化任務，指派給 `ai-dev-bot`。
        *   **自動偵測**: `make lint` 失敗時，Clockwork 自動派工。
        *   **對話式觸發**: 在 5173 的 Agent Chat 輸入：「檢查 `projects_api.py` 的健康度」，觸發診斷。
    3.  **治理與審核**: DevBot 產出 `Proposed Change`。管理員在 5173 的 `/approvals` 頁面審核 Diff 後執行。
    4.  **規範回饋**: 成功後自動更新 `PRPs/ai_docs/SOP_Refactoring_Methodology.md`。
*   **核心價值**: 實現「AI 越修越聰明，規範越補越齊全」的正向循環。

## 2. 數據流矩陣 (Data Flow Matrix)

| 來源 (Source) | 觸發動作 (Trigger) | 處置邏輯 (Logic) | 儲存目標 (Target) |
| :--- | :--- | :--- | :--- |
| **Visit Logs** | 文字輸入/錄音 | 提取關鍵需求與情緒 | `visit_logs` + `archon_tasks` |
| **Leads (LOST)** | 狀態更新 | 提取失敗原因標籤 | `knowledge_items` (Outcome: Fail) |
| **Approvals** | 填寫 review_notes | 轉化為品牌風格約束 | `knowledge_items` (Category: Voice) |
| **Lint / WC** | 指令失敗/行數過多 | **判定重構等級 (L1-L3)** | `proposed_changes` (Refactor) |
| **DevBot Success**| 重構任務完成 | 總結技術細節與封裝模式 | `PRPs/ai_docs/SOP_*.md` |
| **Alice Crawler**| 業務掃描任務 | 提取市場動態與痛點 | `knowledge_items` (Type: Market) |
| **Charlie Crawler**| 技術掃描任務 | 提取 SDK 文檔與架構圖 | `knowledge_items` (Type: Technical) |
| **Docs (MD)** | 文件上傳 | 轉化為開發規範/SOP | `knowledge_items` (Type: SOP) |

## 3. 執行檢查清單 (Actionable Checklist)

1.  [x] **Schema**: 增加 `leads.lost_reason` 與 `leads.lost_competitor` 欄位。
2.  [x] **Librarian**: 擴充 `LibrarianService` 支援 `outcome` 標籤存檔。
3.  [x] **DevBot**: 實作 `NanaBanana` 三層保底路徑 (Native -> Fallback -> Picsum)。
4.  [ ] **DevBot (Self-Healing)**: 在 `AgentService` 中植入 RAG 規範檢索邏輯。
5.  [ ] **UI**: 在 `AdminPage` 實作 Prompt 預覽實驗室。
6.  [ ] **RBAC**: 在 `RBAC_Collaboration_Matrix.md` 加入 `expert_knowledge` 的管理規範。
