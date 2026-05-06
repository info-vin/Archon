# Phase 4.6.6：人機協作專家演進 (Expertise Loop Realization)

> **狀態**: 已完成 (COMPLETED)
> **目標**: 實作專家矩陣，將人類行為轉化為系統知識資產。

## 1. 落地實作路徑 (Implementation Paths)

### 1.1 Alice：失敗教材收割 (Expertise from Failure)
*   **狀態**: 已完成 (COMPLETED)
*   **實作**: 
    *   擴充 `leads` 表，加入 `lost_reason` 欄位 (Migration 034)。
    *   在 `PATCH /leads/{id}` 邏輯中，自動偵測 `LOST` 狀態。
    *   由 `LibrarianService.archive_failure_case` 執行非同步向量化存檔。

### 1.2 Bob：審核意見強化 (Reinforcement from Feedback)
*   **狀態**: 已完成 (COMPLETED)
*   **實作**:
    *   修改 `process_approval` 邏輯，當退件時自動觸發學習。
    *   由 `LibrarianService.archive_style_critique` 提取品牌風格約束並標記為 `brand_voice`。
    *   **MarketBot** 已具備 RAG 感知能力，檢索時自動加權這些約束。

### 1.3 DevBot：創意引擎保底 (Creative Resilience)
*   **狀態**: 已完成 (COMPLETED)
*   **實作**:
    *   重構 `nana_banana_proxy`，實作 `Native (Imagen) -> Fallback (Bob) -> Picsum (Emergency)` 三層降級路徑。
    *   解決了因 API Quota 或網路問題導致的圖片生成中斷。

### 1.4 RAG：知識實時感知 (Live Knowledge Injection)
*   **狀態**: 已完成 (COMPLETED)
*   **實作**: 
    *   升級 RAG 引擎，支援 `min_score` 參數傳遞。
    *   Bob 呼叫檢索時已注入 `min_score=0.25`，確保優先命中 Alice 爬回的高質量數據。

### 1.5 DevBot：規範驅動自癒 (SOP-Driven Self-Healing)
*   **狀態**: 已完成 (COMPLETED)
*   **物理演進史**: 
    *   **2026-02-17 (Initial Gate)**: 實作 Poisson 閘門，基於日誌字串模糊匹配 (ilike %Succeeded%) 限制 L2 修復權限。
    *   **2026-02-27 (XP Injection)**: 注入 `_award_agent_xp` 獎勵邏輯，物理化 Agent 行為價值。
    *   **2026-03-20 (Governance Closure)**: 物理連結閘門與 XP API。權限判斷正式升級為 **「XP 等級鎖定」** (Level 1+ 始獲物理寫入權限)，達成行為資歷化治理。


### 1.6 Charlie & David：治理與物理隔離 (Governance Hardening)
*   **狀態**: 已完成 (COMPLETED)
*   **實作**:
    *   **身份落地**: 更名 Admin 為 **David Howard**，建立營運管理權威感。
    *   **物理隔離**: 建立 `archon_crawler_targets` 表，並將 URI 與 Token 物理分流，確保 3737 設定面板潔淨。
    *   **政策定錨**: 檔案存檔已支援 `policy` 標籤注入與 RAG 評分加權 (Boosting)。

### 1.7 David 的技術顧問與規範自動硬化 (David's Refactoring Advisory)
*   **狀態**: 已完成 (COMPLETED)
*   **實作**:
    *   **技術債門診**: 在 5173 實作 Admin 專屬診斷面板，David 可針對檔案進行 L1-L3 等級判定。
    *   **後端實體**: `AgentService.diagnose_file_health` 實作實體行數與 SQL 偵測。
    *   **規範硬化**: AI 診斷結果已與 1.4/1.5/1.6 標準完全對齊。

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
4.  [x] **DevBot (Self-Healing)**: 在 `AgentService` 中植入 RAG 規範檢索與 Poisson 門檻。
5.  [x] **UI**: 在 `ManagerDashboard` 實作 David 專屬的技術診斷與指標說明面板。
6.  [x] **RBAC**: 完成 David Howard 身份落地與物理設定隔離。
