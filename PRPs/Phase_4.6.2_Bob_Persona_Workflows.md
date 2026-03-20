# Phase 4.6.2 實作細節：Bob 的內容生產工作臺 (Content Workbench)

> **狀態**: 已完成 (DONE) - 2026/02/11 (Revised for Accuracy)
> **目標角色**: Bob (內容行銷主管)
> **核心目標**: 將 Bob 的工作流從「被動看報表」轉型為「主動生產內容」，透過 **三代理人協作模型 (3-Agent Collaboration Model)** 打造一個具備任務連動能力的內容工作臺。
> **技術核心**: 
> 1.  **混合模型策略**: 文字生成採用 `gemini-2.0-flash`；視覺資產採用 **MCP SVG Generator** (本地幾何運算，免 Token 成本)。
> 2.  **數據映射 (GAP-023)**: 支援 Pydantic Alias 映射（API: `reviewNotes` -> UI: `review_notes`）。
> 3.  **條件式任務同步**: 提交審核時，僅在通過 AI 自動合規性檢查 (Compliance Check) 後，任務狀態才會流轉至 `Review`。

## 1. 核心哲學：工作臺 (The Workbench)
Bob 不需要更多圓餅圖。他需要的是一個 **內容 IDE (Integrated Development Environment)**。
*   **佈局設計**: 
    *   **左側面板 (Pane A)**: `Victory Feed` (戰果牆) — 顯示高密度的線索列表與關聯任務。
    *   **右側面板 (Pane B)**: `Workbench` — 30/70 分割比例，整合 RAG 脈絡、AI 配置器與 Markdown 編輯器。

---

## 2. 三代理人協作模型 (The 3-Agent Model)

### Agent 1: Librarian (圖書館員 - 研究助手)
*   **職責**: 提供脈絡 (Context Provider)。
*   **任務**: 透過向量檢索 (RAG) 撈取 Alice 的 `visit_logs` 與案例，自動整理為 **參考素材包**。

### Agent 2: MarketBot (主筆 - 撰稿助手)
*   **職責**: 編織故事 (Content Weaver)。
*   **高級配置**: 支援 `Industry`, `Style`, `Length`, `Charts` 多維度參數調節。
*   **透明化**: 支援 `used_prompt` 回傳，前端可點擊 "View AI Prompt" 檢視完整上下文。

### Agent 3: Nana Banana (美術 - 視覺助手)
*   **職責**: 視覺資產 (Vector Asset Creator)。
*   **物理實現**: 定位為「系統外掛工具」，不涉及雲端圖像計費。
*   **核心引擎**: 透過 `logo_tool.py` 物理生成幾何 SVG 向量圖，支援 `Project ECITON` 動態品牌識別。
*   **降級機制**: 具備 Scout 自動化腳本 (`twin_scout_gemini_auth.py`) 與外部 Pollinations 連結之雙軌防禦。

---

## 3. 詳細工作流程 UML (Sequence Diagram)

```mermaid
sequenceDiagram
    autonumber
    actor Bob as 👤 Bob (行銷主管)
    participant UI as 🖥️ 內容工作臺
    participant API as ⚙️ 後端 API (marketing_api)
    participant DB as 🗄️ 資料庫 (Supabase)
    participant TaskSvc as 📋 Task Service

    %% 階段一：任務啟動
    rect rgb(240, 248, 255)
    Note over Bob, TaskSvc: 階段 1：反饋感知
    Bob->>UI: 從看板點擊 "Smart Edit"
    UI->>UI: 自動映射 reviewNotes -> review_notes
    alt 文章曾被退回
        UI-->>Bob: 頂部 Banner 顯示 Charlie 的修改建議
    end
    end

    %% 階段二：狀態同步 (GAP-023)
    rect rgb(240, 255, 240)
    Note over Bob, TaskSvc: 階段 2：儲存連動
    Bob->>UI: 編輯內容並點擊 "💾 Save"
    UI->>API: POST /api/blogs (Status: DRAFT)
    UI->>API: PATCH /api/tasks/{id} (Status: DOING)
    API->>TaskSvc: 更新看板任務狀態為「執行中」
    end

    %% 階段三：提交流程與 AI 審核
    rect rgb(255, 250, 240)
    Note over Bob, TaskSvc: 階段 3：提交流程閉環
    Bob->>UI: 點擊 "🚀 Submit for Review"
    UI->>API: POST /api/marketing/blog/{id}/submit
    API->>API: AI 合規性檢查 (Compliance Check)
    
    alt 檢查通過 (Success)
        API->>DB: blog_posts (Status: REVIEW)
        API->>TaskSvc: tasks (Status: REVIEW)
        UI-->>Bob: 導回 Dashboard -> 任務進入「審核中」
    else 檢查未通過 (Fail)
        API-->>UI: 回傳 AI 修正建議 (Review Notes)
        UI-->>Bob: 彈出視窗顯示理由，任務維持「執行中」
    end
    end
```

---

## 4. 定案政策與規範 (Finalized Policies)

### P6. 內容完整性與清理 (Smart Polish)
*   **圖片分離**: 為了保持文章內文純淨，系統在儲存時會自動執行 `cleanAIImageReference`。這會從 Markdown 中移除圖片語法，僅將 URL 保存在元數據的 `imageUrl` 欄位中，避免內容重複渲染或語法污染。

### P7. 介面佈局規範
*   **高度鎖定**: `/brand` 頁面強制使用 `h-screen overflow-hidden` 佈局。這能消除導覽列、側邊欄與編輯器之間的多重捲動條，提供 IDE 般的沈浸式體驗。

### P8. 跨角色狀態連動 (Task Sync)
*   **儲存連動**: `Save` 操作強制觸發 `TaskStatus.DOING`。
*   **提交連動**: `Submit` 操作成功後觸發 `TaskStatus.REVIEW`。
*   **2026-03-20 物理對齊 (Phase 4.6.15)**: 
    *   **落地實作**: 撰稿功能已對接到 `MarketingService.py:254` (MarketBot)；提交功能已對接到 `MarketingService.py:227` 並補齊路由。
    *   **外掛說明**: Nana Banana 繪圖功能定位為「系統外掛/工具」，採用 MCP 幾何生成 (logo_tool.py)，不涉及 LLM 計費模型呼叫，故其繪圖行為不計入 AI Token 成本。

### P9. 反饋感知透明化 (Feedback Transparency)
*   **映射規範**: 必須優先處理 API 返回的 `reviewNotes` (camelCase) 並將其賦值給 UI 渲染所需的 `review_notes`。

---

## 5. 執行檢查清單 (Actionable Checklist)

1.  [x] **UI**: 實作 30/70 分割視窗、雙重收合側邊欄與 `h-screen` 佈局。
2.  [x] **Sync**: 實作 `Save` 與 `Submit` 對關聯 Task ID 的狀態更新。
3.  [x] **Logic**: 實作 `cleanAIImageReference` 內容清理邏輯。
4.  [x] **Resilience**: 完成 `marketing_api` 的三層圖資降級防禦。
5.  [x] **Visual**: 實作 Prompt Inspector 彈窗與視覺化退件反饋橫幅。
6.  [x] **Data**: 補全 `BlogPost` 介面中的 `authorName` 與 `publishDate`。