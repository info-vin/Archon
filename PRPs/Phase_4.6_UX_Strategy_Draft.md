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

### B. Charlie (Manager) - Tablet First
*   **Context**: 會議室、移動辦公、數據監控。
*   **Issues**: Dashboard 缺乏 "Man-Machine Collaboration" 可視化；管理介面密度不適合觸控。
*   **Proposal**:
    4.  **Touch-Friendly Density**: 調整按鈕與列表間距，適合手指點擊 (Touch Targets > 44px)。
    5.  **HR/AI Dashboard Widget**: 新增 "AI Human Collaboration Ratio" 圖表 (Pie/Stack Chart)，顯示 AI 與人類工時/任務佔比。
    6.  **Drag & Drop Kanban**: 優化平板上的拖拉體驗 (Team Task Management)。

### C. Consistency Policy (一致性策略)
*   **Principle**: Data Parity, UI Divergence. (資料一致，介面分歧)
    7.  **Unified Content**: Admin 與 User 看到的數據 (Leads, Tasks) 來源一致，僅受 RBAC 過濾。
    8.  **Adaptive UI**: 根據 `window.matchMedia` 或 User Agent 自動切換 Mobile/Desktop 佈局，而非維護兩套網址。

## 2. Field Operations & Logging (外勤與紀錄)

### A. Audit & Privacy
*   **Concern**: 手機外勤的隱私與安全。
*   **Proposal**:
    9.  **Enhanced Logs**: 擴充 `audit_logs` Schema，紀錄 `ip_address`, `device_type`, `gps_coordinates` (需 User Consent)。
    10. **Privacy Toggle**: 在 Settings 允許使用者開啟/關閉 "High Precision Location" (僅在 Clock-in 時強制開啟)。
    11. **Session Management**: Mobile 端支援 "Remember Me" 但需定期 (如 7 天) 強制 Re-login。

### B. Clock-In Experience
    12. **Mobile Widget**: 在 Dashboard 頂部新增 "Clock In / Out" 大按鈕。
    13. **Geo-Fencing**: (Future) 偵測是否在客戶地點附近自動提示打卡。

## 3. Task Management (任務管理)

### A. Dashboard Evolution
*   **Issue**: "How to plan my day?" vs "What's next?"
*   **Proposal**:
    14. **Morning Briefing Mode (Desktop/Tablet)**: 顯示 Calendar View / Timeline，方便拖拉排程。
    15. **Field Mode (Mobile)**: 顯示 "Today's Agenda" (List View)，隱藏未來任務，專注當下。
    16. **Visual Cues**: 使用更鮮明的顏色標記 Priority (戶外陽光下可視性)。

### B. Task Card Refinement
    17. **Refine with AI (Localization)**: 
        *   **Auto-TC**: 後端檢測若輸入為繁體中文，Prompt 強制加入 "Output in Traditional Chinese"。
        *   **Show Prompt in TC**: 前端顯示的 "Refined logic" 提示語也需繁體化。
    18. **Mobile Date Picker**: 捨棄 Custom Component，改用 Native Mobile Date Picker (iOS/Android 原生體驗)。
    19. **Due Time**: 增加具體 "Time" 選擇 (不僅是 Date)，以利安排拜訪行程。

## 4. Sales Intel on the Go (行動銷售情報)

### A. Leads "Shopping Cart"
*   **Concept**: 類似購物車的篩選體驗。
*   **Proposal**:
    20. **Tinder-Style Triage**: 在手機上對 Raw Leads 進行 "Swipe Left (Ignore) / Swipe Right (Save to List)"。
    21. **Cart View**: "My Selected Leads" 頁面，可批次 "Confirm Validity" 或 "Export"。

### B. Job Search & Pitch
    22. **Mobile Job Card**: Job Search 結果以卡片呈現，點擊展開詳情。
    23. **One-Handed Pitch**: "Generate Pitch" 後直接全螢幕顯示結果，並提供 "Copy to Clipboard" 或 "Share to Line/Slack" 按鈕。

## 5. Customer Management (客戶管理 - Future Planning)

### A. Customer Table Planning
    24. **Customer Micro-Page**: 手機版極簡頁面 (Name, Map Link, Last Interaction Note)。
    25. **Visit Log Integration**: 拜訪後透過 "Voice Input" 快速轉文字存入 Visit Logs。
