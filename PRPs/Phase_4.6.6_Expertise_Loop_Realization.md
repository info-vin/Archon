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
*   **目標**: 確保 Bob 的生成器能「看到」Alice 剛剛爬回來的數據。
*   **實作**:
    *   在 `RAGService.perform_rag_query` 中加入 `filter` 參數。
    *   Bob 的 `draft_blog_post` 將預設帶入 `min_score` 篩選，優先命中 `knowledge_api` 產出的 `technical` 與 `market_intel` 標籤。

## 2. 數據流矩陣 (Data Flow Matrix)

| 來源 (Source) | 觸發動作 (Trigger) | 處置邏輯 (Logic) | 儲存目標 (Target) |
| :--- | :--- | :--- | :--- |
| **Visit Logs** | 文字輸入/錄音 | 提取關鍵需求與情緒 | `visit_logs` + `archon_tasks` |
| **Leads (LOST)** | 狀態更新 | 提取失敗原因標籤 | `knowledge_items` (Outcome: Fail) |
| **Approvals** | 填寫 review_notes | 轉化為品牌風格約束 | `knowledge_items` (Category: Voice) |
| **Crawler** | 成功抓取網頁 | 自動分段與向量化 | `knowledge_items` (Type: Market) |

## 3. 執行檢查清單 (Actionable Checklist)

1.  [ ] **Schema**: 增加 `leads.lost_reason` 與 `leads.lost_competitor` 欄位。
2.  [ ] **Librarian**: 擴充 `LibrarianService` 支援 `outcome` 標籤存檔。
3.  [ ] **DevBot**: 重構 `logo_tool` 支援 `NanaBanana` 創意模組。
4.  [ ] **UI**: 在 `AdminPage` 實作 Prompt 預覽實驗室。
5.  [ ] **RBAC**: 在 `RBAC_Collaboration_Matrix.md` 加入 `expert_knowledge` 的管理規範。
