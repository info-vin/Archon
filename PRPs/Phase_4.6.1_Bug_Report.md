# Phase 4.6.1 缺陷與缺口追蹤表 (Bug & Gap Tracking Report)

> **文件目的**: 集中管理 Phase 4.6.1 (Alice Workflow) 與相關 UI 回饋的修復進度。
> **參考標準**: 遵循 Phase 4.5 格式。

---

## 📊 摘要儀表板 (Summary Dashboard)

|指標 (Metric)|數量 (Count)|詳細資訊 (Details)|
|:---|:---|:---|
|**總議題數**|13|8 項發現 + 2 個嚴重錯誤 + 3 項使用者回饋。|
|**已修復**|13|所有嚴重錯誤、缺口與 UI 回饋皆已解決。|
|**待處理**|0|待驗收 (Ready for Verification)。|

---

## 🔍 缺陷與缺口追蹤詳表 (Defect & Gap Tracking Table)

| ID | 類型 (Type) | 功能模組 (Function) | 問題描述 (Description) | 嚴重度 (Severity) | 狀態 (Status) | 相關檔案 (Trace) |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **BUG-031** | 🐛 Bug | **Gemini/Refine** | `Gemini-1.5-flash` 404 錯誤 (找不到模型/API 不匹配)。 | Critical | 🟢 已解決 | `task_service.py` (降版回 1.5-flash) |
| **BUG-032** | 🐛 Bug | **Leads/API** | "Failed to add lead" 錯誤 (模擬資料的後端驗證失敗)。 | Critical | 🟢 已解決 | `marketing_api.py` (新增 Schema & 日誌) |
| **GAP-001** | 🔧 Gap | **Auto-Archive** | 寫死的 3 天門檻阻礙測試。需要可配置的環境變數。 | High | 🟢 已解決 | `enrichment_service.py` (新增 `PRUNING_THRESHOLD_MINUTES`) |
| **GAP-002** | 🔧 Gap | **Mobile/Clock-in** | 每次渲染都重新抓取 GPS 效率低落。需要快取。 | Medium | 🟢 已解決 | `ClockInWidget.tsx` (使用現有 State) |
| **GAP-003** | 🔧 Gap | **Mobile/Swipe** | 缺少誤滑的「復原」功能。 | Medium | 🟢 已解決 | `LeadsCardStack.tsx` (實作 Undo Stack) |
| **GAP-004** | 🔧 Gap | **UI/Desktop** | 儀表板與 Leads 表格缺少細節 (職位摘要、頭像、後續追蹤)。 | High | 🟢 已解決 | `DashboardPage.tsx`, `MarketingPage.tsx` |
| **GAP-005** | 🔧 Gap | **UI/UX** | 頭像樣式不一致 (綠色圓圈) & 購物車數量 Bug。 | Low | 🟢 已解決 | `UserAvatar.tsx` (角色顏色), `MainLayout.tsx` (購物車輪詢) |
| **GAP-006** | 🔧 Gap | **Mobile/Pitch** | Pitch Drawer 分隔線顯示問題。 | Low | 🟢 已解決 | `LeadsCardStack.tsx` (新增把手) |
| **GAP-007** | 🔧 Gap | **Desktop/Pitch** | 桌面版 "Generate Pitch" 按鈕顯示問題。 | Medium | 🟢 已解決 | `MarketingPage.tsx` (新增操作按鈕) |
| **GAP-008** | 🔧 Gap | **Workflow/Tea Time** | UI 缺少 "Review Needed" 過濾器。 | Medium | 🟢 已解決 | `MarketingPage.tsx` (新增過濾模式) |

---

## 🛠 修復紀錄 (Fix Log)

*   **2026-02-01**:
    *   **初始化 (Initialization)**: 建立追蹤報告。
    *   **規劃中 (Planned)**: 啟動後端修復 (BUG-031, BUG-032, GAP-001)。
    *   **回歸修復 (Regression Fixes)**:
        *   **Fixed**: `LeadsCardStack.tsx` 遺失 `RefreshCwIcon` import。
        *   **Fixed**: `UserAvatar` 顏色邏輯 (在 `DashboardPage` 加入 `userMap` 以解析角色)。
        *   **Fixed**: POBot Gemini 設定 (預設 `gemini-2.0-flash` & 繁中 System Prompt)。
    *   **UI/UX 優化 (UI/UX Polish)**:
        *   **行動佈局**: 優化 `LeadsCardStack` 在「中型手機」螢幕的縮放 (減少容器高度)。
        *   **卡片設計**: 微調排版 (公司名稱大小、段落間距) 並簡化頁腳。
        *   **銷售購物車**: 將 Pitch `alert()` 替換為專屬的 `PitchModal` 實作。
        *   **購物車徽章**: 在 `MainLayout` 實作動態數量輪詢。
        *   **開發工具**: 新增「清除歷史」按鈕與端點 (`marketing_api.py`)。
    *   **第二輪使用者回饋 (User Feedback Round 2)**:
        *   **儀表板優先級**: 修復優先級判斷的大小寫問題，解決黑點顯示錯誤 (`DashboardPage.tsx`)。
        *   **Leads 卡片佈局**: 調整 `LeadsCardStack` 以縮減標題高度 (<25%) 並最大化內容空間。
        *   **行銷工作流**: 移除新增 Lead 後自動切換至 "Leads" 分頁的行為，允許連續搜尋。
