# Phase 4.6: UX Strategy & Mobile-First Adaptation (Discussion Draft)

> **核心目標**: 針對不同角色 (Persona) 與裝置情境 (Device Context) 優化 5173 前端體驗。
> **現狀**: 功能完備但 UX 通用化，缺乏針對 Mobile (Alice) 與 Tablet (Charlie) 的優化。

## 1. Role & Device Optimization (角色與裝置優化)

### A. Alice (Sales Rep) - Mobile First
*   **Context**: 通勤中、客戶現場、單手操作。
*   **Issues**: 目前 Sales Hub 為 Desktop 設計，表格在手機上難以閱讀。
*   **Proposal**:
    1.  **Mobile Layout**: 隱藏側邊欄，改用底部導覽列 (Bottom Navigation)。
    2.  **Card-Based Leads**: 將寬表格轉換為 "Card Stack" 視圖，適合單手滑動。
    3.  **One-Tap Actions**: 增加快速按鈕 (Call, Map, Pitch) 於顯眼位置。
    4.  **Sales Shopping Cart**: (New) "Tinder-style" 左滑忽略/右滑收藏 Leads，並在 "My Cart" 頁面批次處理。
    5.  **Job Search Cards**: Job Search 結果卡片化，點擊展開。
    6.  **One-Handed Pitch**: 生成 pitch 後全螢幕顯示，提供 "Copy/Share" 大按鈕。

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
    10. **Nana Banana Integration**: 整合 "Nana Banana" 圖像生成模型 (Mock/API)。
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
