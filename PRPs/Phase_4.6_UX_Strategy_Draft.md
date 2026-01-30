# Phase 4.6: UX Strategy & Mobile-First Adaptation (Discussion Draft)

> **核心目標**: 針對不同角色 (Persona) 與裝置情境 (Device Context) 優化 5173 前端體驗。
> **現狀**: 功能完備但 UX 通用化，缺乏針對 Mobile (Alice) 與 Tablet (Charlie) 的優化。

## 1. Role & Device Optimization (角色與裝置優化)

### A. Alice (Sales Rep) - Mobile First & Field Ops
*   **Context**: 通勤中、客戶現場、單手操作 (One-Thumb Interaction)。
*   **Issues**: 目前 Sales Hub 為 Desktop 設計，表格在手機上難以閱讀；缺乏快速紀錄拜訪結果的機制。
*   **Proposal - Core Mobile Experience**:
    1.  **Mobile Layout**: 隱藏側邊欄，改用底部導覽列 (Bottom Navigation: Dashboard, Leads, Tasks, Customers)。
    2.  **Card-Based Leads (Tinder-Style)**:
        *   **Interaction**: 將寬表格轉換為 "Card Stack"。
        *   **Gesture**: 左滑忽略 (Archive)，右滑加入 "My Cart" (Shortlist)，上滑顯示詳情。
    3.  **One-Tap Actions**: 針對客戶卡片增加 Floating Action Button (FAB) -> 導航 (Map)、生成話術 (Pitch)。(移除撥號功能)

*   **Proposal - The "Commute" Workflow (Sales Intel)**:
    4.  **Sales Shopping Cart**: "My Selected Leads" 頁面。Alice 在捷運上滑完 Leads 後，在此頁面進行批次操作。
    5.  **Job Search Cards**:
        *   **Clean UI**: 移除 "View Link" 按鈕，點擊卡片即展開摘要。
        *   **Action**: 若感興趣直接 "Add to Leads"，進入 Leads 後系統自動抓取完整 JD。
    6.  **One-Handed Pitch**: 生成 Pitch 後全螢幕顯示，字體放大，並提供對比色強烈的 "Copy" 與 "Line Share" 按鈕，方便在陽光下操作。

*   **Proposal - Lead Follow-up & Enrichment**:
    7.  **Lead Follow-up UI**: 新增 "Leads Timeline" 視圖，顯示 Lead 從 New -> Contacted -> Meeting -> Deal 的狀態進展。
    8.  **Automated Enrichment Loop**:
        *   **Strategy**:
            *   Lead 進入 List 後，狀態標記為 `enriching`。
            *   Agent 嘗試從 104 爬取。若失敗，啟動 **Plan B** (Google Search API / Official Website Crawler)。
            *   若 Agent 填補資料 >= 80%，狀態轉為 `review_needed` 通知 Alice。
        *   **Auto-Prune**: 若建立超過 3 天仍無法補全資料 (資料殘缺)，系統自動轉為 `archived` (Reason: Stale Data)，並記錄 Audit Log。
        *   **Human Review**: Alice 審閱 Agent 填寫的資料，確認無誤後點擊 "Verify"，Lead 正式進入漏斗。

*   **Proposal - Customer Management (Future)**:
    9.  **Customer Micro-Page**: 手機版極簡頁面，僅顯示關鍵資訊 (Name, Map Link, Last Interaction Note, Next Action)。
    10. **Voice-to-Text Visit Logs**: 拜訪結束後，透過手機麥克風口述 "Visit Summary"，利用 **Gemini Audio Capability (Multimodal)** 轉為文字並提取關鍵 Insight 存入 Log。
    11. **Desktop-Mobile Handoff**:
        *   **Scenario**: 在辦公室電腦 (Desktop) 規劃好 "Today's Route"。
        *   **Sync**: 手機端 Dashboard 自動置頂 "Today's Route" (地圖模式)，無需重新搜尋。

## 6. Data Architecture Impact (資料庫擴充需求)

> 針對 Phase 4.6 的 UX/Feature 需求，現有 Schema 需進行以下擴充：

*   **`visit_logs` (New Table)**:
    *   用於儲存 Alice 的拜訪紀錄。
    *   Fields: `id`, `lead_id`, `user_id`, `visit_date`, `gps_location`, `voice_note_url`, `transcript`, `summary_tags`.
*   **`leads` (Expansion)**:
    *   新增欄位支援 Enrichment Loop: `enrichment_status` (pending/success/failed), `enrichment_score` (0-100), `data_last_verified_at`, `auto_archived_reason`.
*   **`audit_logs` (Expansion)**:
    *   新增硬體環境欄位: `device_type` (mobile/desktop), `ip_address`, `gps_lat`, `gps_long` (Nullable, for high precision mode).
*   **`marketing_trends` (New Analysis Table)**:
    *   用於快取 Bob 的市場週報數據，避免每次即時運算。
    *   Fields: `report_date`, `keyword`, `count`, `industry_distribution` (JSON), `growth_rate`.
*   **`subscriptions` (New Table)**:
    *   用於管理 `/blog` 訂閱會員。
    *   Fields: `id`, `email`, `name`, `subscribed_at`, `converted_to_lead_id` (Link to CRM).

### B. Charlie (Manager) - Tablet First
*   **Context**: 會議室、移動辦公、數據監控。
*   **Issues**: Dashboard 缺乏 "Man-Machine Collaboration" 可視化；管理介面密度不適合觸控。
*   **Proposal**:
    7.  **Touch-Friendly Density**: 調整按鈕與列表間距，適合手指點擊 (Touch Targets > 44px)。
    8.  **HR/AI Dashboard Widget**: 新增 "AI Human Collaboration Ratio" 圖表，顯示 AI 與人類工時/任務佔比。
    9.  **Drag & Drop Kanban**: 優化平板上的拖拉體驗。

### C. Bob (Marketing) - Content Engine (New Revisions)
*   **Context**: 創意發想、內容生產、媒體資產管理。
*   **Issues**: AI 工具分散，缺乏工作流整合 (Time/Token tracking)。
*   **Proposal - Asset Generation**:
    10. **Nana Banana Integration**:
        *   **Governance**: API Key 由 **System Admin** 統一管理 (建議存於 `.env` 或加密的 System Secrets 表)，Bob/Charlie 無需也無法自行設定 Key。
        *   **Admin UI (3737)**: 僅提供 "Service Status" 檢查 (如 OpenAI/Gemini)，不暴露明碼 Key。
    11. **Abstracted Prompting**: Bob 不需要看到底層 System Prompt，僅需操作風格參數 (Style Keywords)。
    12. **UI Consistency**: Icon Generation 介面需與 Admin/Charlie 統一，但功能參數依 RBAC 區分。

*   **Proposal - Magic Draft & Blog**:
    13. **Unified Modal Style**: "Magic Draft" 介面應與 "Refine with AI" 風格一致 (Violet Glassmorphism)。
    14. **Smart Image Picker**:
        *   **Auto-Fetch**: 根據文章關鍵字自動爬取/生成預覽圖。
        *   **Preview First**: 不需點擊即可看到縮圖。
        *   **Retry Limit**: 提供 "Regenerate/Swap" 按鈕 (Max 3 times) 以快速篩選。
    15. **RAG Transparency**: 新增 "Knowledge Usage" 指標，顯示內容有多少比例引用自知識庫 (Reference Links/Highlights)。
    16. **Task-Linked Workflow**:
        *   **State Logging**: 嚴格紀錄 `Draft -> Review -> Public` 的時間戳記。
        *   **Metrics**: 連結至 Task 系統，統計該篇文章耗費的 "Human Time" vs "AI Tokens"，解決工時難以估算問題。
    17. **Growth Loop (Subscription)**:
        *   **Member Button**: `/blog` 新增 "Subscribe/Become Member" CTA。
        *   **Lead Generation**: 訂閱者自動轉為 CRM Leads (Alice 可見)。
        *   **Knowledge Graph**: 讓 Bob 能透過訂閱資料理解 Industry/Vendor/Customer 關聯，反哺內容策略。

### D. Bob (Marketing) - Market Intelligence 2.0 (New Revisions)
*   **Context**: 趨勢分析、策略制定、機會識別。
*   **Issues**: 目前 "Market Specs" 僅為靜態計次，缺乏時間維度與關聯性洞察。
*   **Proposal**:
    28. **Trend Visualization (Time Series)**:
        *   **Line Chart**: 顯示關鍵字 (e.g., "AI", "ESG") 在 Leads 中出現頻率的月度趨勢，幫助 Bob 識別 "Rising Topics"。
        *   **Seasonality**: 標示行銷活動與 Lead 增長的關聯點。
        *   **Status**: Phase 4.6.5 執行 (Frontend Implementation Pending).
    29. **Relationship Mapping (Knowledge Graph)**:
        *   **Sankey Diagram**: 視覺化流向 `Industry (from Lead) -> Identified Need -> Potential Vendor Solution`.
        *   **Network View**: 顯示 Industry, Customer, Vendor 三者之間的關聯節點，讓 Bob 理解 "哪些產業正在尋求哪類解決方案"。
        *   **Status**: Phase 4.6.5 執行 (Frontend Implementation Pending).
    30. **Smart Filtering & Clustering**:
        *   **Semantic Clustering**: 捨棄硬編碼關鍵字，改用 LLM 將 Leads 自動分群 (e.g., "Digital Transformation", "Compliance").
        *   **Drill-down Filters**: 允許 Bob 依據 Region, Time Range, Industry 篩選 Dashboard 數據。

## 2. Field Operations & Logging (外勤與紀錄)

### A. Audit & Privacy
*   **Concern**: 手機外勤的隱私與安全。
*   **Proposal**:
    18. **Enhanced Logs**: 記錄 `ip_address`, `device_type`, GPS (需 User Consent)。
    19. **Privacy Toggle**: Settings 允許開關 "High Precision Location" (Clock-in 強制)。

### B. Clock-In Experience
    20. **Mobile Widget**: Dashboard 頂部大按鈕 "Clock In/Out".

## 3. Task Management (任務管理)

### A. Dashboard Evolution
    21. **Mode Switching**: Morning Briefing (Desktop/Timeline) vs Field Mode (Mobile/List).
    22. **Visual Cues**: 高對比度 Priority 標示。

### B. Task Card Refinement
    23. **Localization**: 自動偵測繁體中文輸入，強制輸出繁體中文結果。
    24. **Native Mobile Picker**: 使用 iOS/Android 原生日期選擇器。
    25. **Due Time**: 增加時間選擇功能。

## 4. UI Consistency Policy
*   **Principle**: Data Parity, UI Divergence.
    26. **Adaptive UI**: 單一 URL，根據 Device 自動切換 Layout。
    27. **Shared Components**: Admin/Marketing 共用 Asset Generator 元件，僅更換 Config/Permissions。

## 5. Cognitive Infrastructure (認知基礎設施)

> **核心目標**: 實作 "The Soul of the Machine" (Clockwork L5)，讓系統具備基於數據的自我觀察與優化能力。

### A. Data Foundation (資料基石)
*   **Contextual Logging (`archon_logs` 2.0)**:
    *   **Before/After Snapshot**: 當 Alice 修改 AI 生成的內容時，記錄 `original_text` 與 `final_text` 的差異 (Diff)，作為 "Human Correction Rate" 的計算基礎。
    *   **Business Context**: 記錄操作當下的業務變數（如：客戶產業、Lead 分數），以便分析 "什麼情況下 AI 表現最差"。
*   **Event Sourcing Integration**:
    *   將 `LeadStatusChanged`, `DraftRevised` 等關鍵動作視為事件，而非單純的資料庫更新，以建立完整的行為時間軸。

### B. Clockwork L5 Evolution (流程教練)
*   **Pattern Recognition (模式識別)**:
    *   **Workflow Analyzer**: 定期 (Weekly) 分析 Log，識別重複的人類介入模式（例如：Bob 總是在生成草稿後手動刪除某個特定段落）。
    *   **Bottleneck Detection**: 找出 "Human Time" 消耗最高的 AI 任務環節。
*   **Proactive Optimization (主動優化)**:
    *   **Prompt Tuning Proposal**: Clockwork 自動生成 `proposed_changes`，建議 Admin 修改 System Prompt（例如："建議在 MarketBot Prompt 加入 'Tone: Formal' 以減少 Alice 的修改率"）。
    *   **Macro Suggestion**: 建議將連續的高頻操作（如：搜尋 -> 篩選 -> 生成）打包為自動化 Macro。

### C. Feedback Loop UX (閉環體驗)
*   **Admin/Charlie**:
    *   **Optimization Dashboard**: 新增 "System Insights" 面板，顯示 "Prompt Efficiency Score" (Prompt 效率分) 與 "Human Correction Rate" (人類修正率)。
    *   **One-Click Apply**: 針對 Clockwork 的優化建議，提供 "Approve & Apply" 按鈕，一鍵更新 System Prompt。