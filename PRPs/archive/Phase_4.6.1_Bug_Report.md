# Phase 4.6.1 缺陷與缺口追蹤表 (Bug & Gap Tracking Report)

> **文件目的**: 集中管理 Phase 4.6.1 (Alice Workflow) 與相關 UI 回饋的修復進度。
> **參考標準**: 遵循 Phase 4.5 格式。

---

## 📊 摘要儀表板 (Summary Dashboard)

|指標 (Metric)|數量 (Count)|詳細資訊 (Details)|
|:---|:---|:---|
|**總議題數**|18|11 項發現 + 2 個嚴重錯誤 + 5 項待實作/重構。|
|**已修復**|13|Phase 4.6.1 核心功能已就緒。|
|**待處理**|5|3 項 Alice 業務功能 (待實作) + 2 項技術債 (待規劃)。|

---

## 🔍 缺陷與缺口追蹤詳表 (Defect & Gap Tracking Table)

| ID | 類型 (Type) | 功能模組 (Function) | 問題描述 (Description) | 嚴重度 (Severity) | 狀態 (Status) | 相關檔案 (Trace) |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **BUG-031** | 🐛 Bug | **Gemini/Refine** | `Gemini-1.5-flash` 404 錯誤 (找不到模型/API 不匹配)。 | Critical | 🟢 已解決 | `task_service.py` |
| **BUG-032** | 🐛 Bug | **Leads/API** | "Failed to add lead" 錯誤 (模擬資料的後端驗證失敗)。 | Critical | 🟢 已解決 | `marketing_api.py` |
| **GAP-001** | 🔧 Gap | **Auto-Archive** | 寫死的 3 天門檻阻礙測試。需要配置環境變數。 | High | 🟢 已解決 | `enrichment_service.py` |
| **GAP-002** | 🔧 Gap | **Mobile/Clock-in** | 每次渲染都重新抓取 GPS 效率低落。需要快取。 | Medium | 🟢 已解決 | `ClockInWidget.tsx` |
| **GAP-003** | 🔧 Gap | **Mobile/Swipe** | 缺少誤滑的「復原」功能。 | Medium | 🟢 已解決 | `LeadsCardStack.tsx` |
| **GAP-004** | 🔧 Gap | **UI/Desktop** | 儀表板與 Leads 表格缺少細節 (職位摘要、頭像、後續追蹤)。 | High | 🟢 已解決 | `DashboardPage.tsx` |
| **GAP-005** | 🔧 Gap | **UI/UX** | 頭像樣式不一致 (綠色圓圈) & 購物車數量 Bug。 | Low | 🟢 已解決 | `UserAvatar.tsx` |
| **GAP-006** | 🔧 Gap | **Mobile/Pitch** | Pitch Drawer 分隔線顯示問題。 | Low | 🟢 已解決 | `LeadsCardStack.tsx` |
| **GAP-007** | 🔧 Gap | **Desktop/Pitch** | 桌面版 "Generate Pitch" 按鈕顯示問題。 | Medium | 🟢 已解決 | `MarketingPage.tsx` |
| **GAP-008** | 🔧 Gap | **Workflow/Tea Time** | UI 缺少 "Review Needed" 過濾器。 | Medium | 🟢 已解決 | `MarketingPage.tsx` |
| **GAP-009** | 🔧 Gap | **Mobile/Voice** | 吵雜環境識別。決策：**Voice-to-Task** (Field Ops 專案)。 | Medium | 🔵 待實作 | `visit_log_api.py` |
| **GAP-010** | 🔧 Gap | **Mobile/GPS** | 電力與隱私。決策：**按需取值 (On-Demand)**。 | Low | 🔵 待實作 | `ClockInWidget.tsx` |
| **GAP-011** | 🔧 Gap | **Workflow/Prune** | 歸檔機制。決策：**Score < 40 + 回收站 (Archived View)**。 | Medium | 🔵 待實作 | `enrichment_service.py` |
| **TECH-001** | 🏗️ Debt | **UI/RAG** | `RAGSettings.tsx` 超過 2000 行，增加修改風險與 Token 消耗。 | Critical | ⚪ 待規劃 | `CONTRIBUTING_tw.md` |
| **TECH-002** | 🏗️ Debt | **API/Lean** | `projects_api.py` 邏輯過重，需抽離至 Service 層。 | High | ⚪ 待規劃 | `CONTRIBUTING_tw.md` |

---

## 🛠 修復紀錄 (Fix Log)

*   **2026-02-02**:
    *   **業務定案 (Policies Locked)**:
        *   **GAP-009 (Voice)**: 確認採用 "Field Ops" 專案自動建單模式。
        *   **GAP-010 (GPS)**: 確認採用 On-Demand 觸發模式。
        *   **GAP-011 (Prune)**: 確認採用 "Enrichment Score < 40" 且提供 "Archived View" 撈回機制。
    *   **技術債識別**: 標記 TECH-001 (RAGSettings 拆分) 與 TECH-002 (API Service 化) 為關鍵任務。
*   **2026-02-01**:
    *   **初始化**: 建立追蹤報告與初步修復。