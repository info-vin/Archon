# Phase 4.6.5 缺陷與缺口追蹤表 (Bug & Gap Tracking Report)

> **文件目的**: 集中管理 Phase 4.6.5 (跨角色 UX 優化與系統補強) 的修復進度。
> **涵蓋角色**: Alice (Sales), Bob (Marketing), Charlie (Manager), Admin
> **最後更新**: 2026-02-03

---

## 📊 摘要儀表板 (Summary Dashboard)

|指標 (Metric)|數量 (Count)|詳細資訊 (Details)|
|:---|:---|:---|
|**總議題數**|22|涵蓋 UX 流程、資料一致性、系統重置可靠性與開發者體驗 (DX)。|
|**已完成修正**|8|完成密碼重置、任務可見性、狀態顏色、導覽列恢復 (ID 同步) 與設定頁面整併。|
|**待處理**|14|重點轉向 Bob 的編輯器功能 (Magic Draft) 與樣式統一。|

---

## 🔍 缺陷與缺口追蹤詳表 (Defect & Gap Tracking Table)

| ID | 類型 (Type) | 角色 | 模組 | 問題描述 | 嚴重度 | 狀態 |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **BUG-033** | 🐛 Bug | **All** | **UI/Nav** | 導覽列消失。原因：ID 不匹配 (UUID vs '4') 導致 Profile 抓取失敗。 | Critical | 🟢 已修復 |
| **DX-001** | 🛠️ DX | **All** | **Auth/PW** | 密碼重置為 `qwer45tyuiop`。已實作強制重置邏輯。 | Medium | 🟢 已修復 |
| **BUG-027** | 🐛 Bug | **Charlie** | **Tasks** | Alice 任務消失。原因：後端大小寫敏感且未處理 `project_id=all`。 | High | 🟢 已修復 |
| **BUG-030** | 🐛 Bug | **All** | **Color** | Dashboard 狀態燈色失效。原因：`statusIndicator` 未小寫化。 | Medium | 🟢 已修復 |
| **UX-011** | 🎨 Style | **All** | **UI/Set** | 5173 `/settings` 移至使用者區塊 (頭像 + Email)。 | Medium | 🟢 已修復 |
| **BUG-031** | 🐛 Bug | **System** | **DB/Reset**| `make db-reset` 失敗。原因：`RESET_DB.sql` 遺漏新表。 | High | 🟢 已修復 |
| **BUG-032** | 🐛 Bug | **System** | **DB/Seed** | `seed_mock_data.sql` 報錯。原因：`leads` 插入不存在欄位。 | High | 🟢 已修復 |
| **UX-012** | 🎨 Style | **All** | **Buttons** | 5173 按鈕風格對齊 3737 Style Guide。 | Low | 🔴 待處理 |
| **BUG-028** | 🐛 Bug | **Bob** | **Magic** | 生成內容未貼入編輯器，且切換分頁後遺失。 | High | 🔴 待處理 |
| **BUG-029** | 🐛 Bug | **Bob** | **Image** | 圖片生成後無預覽/URL。 | High | 🔴 待處理 |
| **GAP-012** | 🔧 Gap | **Bob** | **Intel** | 頁面空白無數據，配色太深。 | Medium | 🔴 待處理 |
| **GAP-013** | 🔧 Gap | **Charlie** | **Center** | 指揮中心無資料供練習。 | Medium | 🔴 待處理 |
| **GAP-014** | 🔧 Gap | **Admin** | **RBAC** | 缺少 RBAC 練習案例與多樣化資料。 | Low | 🔴 待處理 |
| **GAP-015** | 🔧 Gap | **Tech** | **Score** | Alice 的 Enrichment Score 計算規則實作。 | Low | 🔴 待處理 |
| **GAP-016** | 🔧 Gap | **Tech** | **Token** | Token Usage 真實寫入與可視化確認。 | Low | 🔴 待處理 |
| **GAP-009** | 🔧 Gap | **Alice** | **Voice** | 語音日誌自動轉工單尚未實作。 | Medium | 🔴 待處理 |
| **GAP-003** | 🔧 Gap | **Alice** | **Swipe** | 滑動誤觸復原功能待驗收。 | Low | 🔴 待處理 |
| **GAP-010** | 🔧 Gap | **Alice** | **GPS** | On-Demand GPS 待驗收。 | Low | 🔴 待處理 |
| **GAP-011** | 🔧 Gap | **Alice** | **Prune** | 自動歸檔邏輯待驗收。 | Low | 🔴 待處理 |
| **ALERT-01**| 🔧 Gap | **Charlie** | **Sentin** | 警示資料準確性待驗收。 | Low | 🔴 待處理 |
| **TECH-001**| 🏗️ Debt | **Tech** | **RAG** | `RAGSettings.tsx` 重構拆分。 | Medium | 🔴 待處理 |
| **TECH-002**| 🏗️ Debt | **Tech** | **Projects**| `projects_api.py` 商業邏輯抽離。 | Medium | 🔴 待處理 |

---

## 🛠 修復紀錄 (Fix Log)

*   **2026-02-03 (Round 2: 重大修復)**:
    *   **BUG-033 (關鍵)**: 診斷出 `profiles.id` ('4') 與 `auth.users.id` (UUID) 不匹配。已執行修復腳本同步全系統 ID (包含外鍵關聯)。
    *   **UX-011**: 修改 `MainLayout.tsx`，移除舊連結並將 Settings 跳轉入口整合至 Sidebar Footer 的 User Profile 區塊。
    *   **BUG-031/032**: 修正 `RESET_DB.sql` (加入 `archon_ethics_events` 等) 與 `seed_mock_data.sql` (移除 leads 表非法欄位)。
*   **2026-02-03 (Round 1)**:
    *   **DX-001**: 更新 `init_db.py` 並強制執行雲端密碼重置腳本 (`qwer45tyuiop`)。
    *   **BUG-027**: 後端 `projects_api.py` 角色檢查標準化 (小寫) 並修正專案過濾。
    *   **BUG-030**: 前端 `DashboardPage.tsx` 狀態顏色匹配小寫化。