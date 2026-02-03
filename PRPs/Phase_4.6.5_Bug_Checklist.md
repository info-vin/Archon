# Phase 4.6.5 缺陷與缺口追蹤表 (Bug & Gap Tracking Report)

> **文件目的**: 集中管理 Phase 4.6.5 (跨角色 UX 優化與系統補強) 的修復進度。
> **涵蓋角色**: Alice (Sales), Bob (Marketing), Charlie (Manager), Admin
> **參考標準**: 遵循 Phase 4.6.1 格式。

---

## 📊 摘要儀表板 (Summary Dashboard)

|指標 (Metric)|數量 (Count)|詳細資訊 (Details)|
|:---|:---|:---|
|**總議題數**|22|涵蓋 UX 流程、資料一致性、系統重置可靠性與開發者體驗 (DX)。|
|**已修復**|5|完成密碼重置邏輯、任務可見性、Dashboard 顏色與 Reset 腳本補強。|
|**待處理**|17|新增 Critical 導覽列消失問題。|

---

## 🔍 缺陷與缺口追蹤詳表 (Defect & Gap Tracking Table)

| ID | 類型 (Type) | 角色 (Persona) | 功能模組 (Function) | 問題描述 (Description) | 嚴重度 (Severity) | 狀態 (Status) |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **BUG-033** | 🐛 Bug | **All** | **UI/Nav** | 登入後所有角色的導覽列 (Sidebar) 都消失。疑為前端權限判斷與後端回傳的角色大小寫不匹配。 | Critical | 🔴 待處理 |
| **DX-001** | 🛠️ DX | **All** | **Auth/Password** | 開發環境密碼不統一。需重置為 `qwer45tyuiop` 並加入更新邏輯。 | Medium | 🟢 已修復 |
| **BUG-027** | 🐛 Bug | **Charlie** | **Task Board** | Alice 開的任務未出現。原因：後端大小寫敏感且未處理 `project_id=all`。 | High | 🟢 已修復 |
| **BUG-030** | 🐛 Bug | **All** | **UI/Color** | Dashboard 狀態燈色失效。原因：`statusIndicator` 未做小寫化。 | Medium | 🟢 已修復 |
| **BUG-031** | 🐛 Bug | **System** | **DB/Reset** | `make db-reset` 失敗。原因：`RESET_DB.sql` 遺漏 Phase 4.6 新增的資料表。 | High | 🟢 已修復 |
| **BUG-032** | 🐛 Bug | **System** | **DB/Seed** | `seed_mock_data.sql` 報錯。原因：`leads` 表插入了不存在的 `email` 欄位。 | High | 🟢 已修復 |
| **UX-011** | 🎨 Style | **All** | **UI/Settings** | 5173 `/settings` 頁面需整併至 Profile Modal (Read-only)。 | Medium | 🔴 待處理 |
| **UX-012** | 🎨 Style | **All** | **UI/Buttons** | 5173 按鈕風格對齊 3737 Style Guide。 | Low | 🔴 待處理 |
| **BUG-028** | 🐛 Bug | **Bob** | **Magic Draft** | 生成內容未貼入編輯器，且切換分頁後遺失。 | High | 🔴 待處理 |
| **BUG-029** | 🐛 Bug | **Bob** | **Image Gen** | 圖片生成後無預覽/URL，亦未插入文章。 | High | 🔴 待處理 |
| **GAP-012** | 🔧 Gap | **Bob** | **Market Intel** | 頁面空白且配色太深。需填充資料並改為淡色系。 | Medium | 🔴 待處理 |
| **GAP-013** | 🔧 Gap | **Charlie** | **Playground** | 指揮中心無資料。需注入 Pending Blogs, Logs, Stale Leads。 | Medium | 🔴 待處理 |
| **GAP-014** | 🔧 Gap | **Admin** | **Playground** | 缺少 RBAC 練習案例。需注入多樣化 User Data。 | Low | 🔴 待處理 |
| **GAP-015** | 🔧 Gap | **Tech** | **Logic/Score** | Alice 的 Enrichment Score 計算規則需實作。 | Low | 🔴 待處理 |
| **GAP-016** | 🔧 Gap | **Tech** | **Logic/Token** | Token Usage 真實寫入與可視化確認。 | Low | 🔴 待處理 |
| **GAP-009** | 🔧 Gap | **Alice** | **Voice** | 語音日誌自動轉工單功能尚未實作。 | Medium | 🔴 待處理 |
| **GAP-003** | 🔧 Gap | **Alice** | **Swipe** | 滑動誤觸復原功能待驗收。 | Low | 🔴 待處理 |
| **GAP-010** | 🔧 Gap | **Alice** | **GPS** | On-Demand GPS 待驗收。 | Low | 🔴 待處理 |
| **GAP-011** | 🔧 Gap | **Alice** | **Prune** | 自動歸檔邏輯待驗收。 | Low | 🔴 待處理 |
| **ALERT-01**| 🔧 Gap | **Charlie** | **Sentinel** | 警示資料準確性待驗收。 | Low | 🔴 待處理 |
| **TECH-001**| 🏗️ Debt | **Tech** | **RAGSettings** | `RAGSettings.tsx` 重構拆分。 | Medium | 🔴 待處理 |
| **TECH-002**| 🏗️ Debt | **Tech** | **ProjectAPI** | `projects_api.py` 商業邏輯抽離。 | Medium | 🔴 待處理 |

---

## 🛠 修復紀錄 (Fix Log)

*   **2026-02-03 (Round 1)**:
    *   **DX-001**: 更新 `init_db.py` 將預設密碼改為 `qwer45tyuiop` 並加入 `update_user_by_id` 邏輯。
    *   **BUG-027**: 修改 `projects_api.py`，將角色判斷轉為小寫並支援 `project_id='all'`。
    *   **BUG-030**: 修改 `DashboardPage.tsx`，為狀態與優先級燈色加入 `.toLowerCase()`。
    *   **BUG-031/032**: 補全 `RESET_DB.sql` 並校準 `seed_mock_data.sql` 的欄位定義。
    *   **BUG-033**: 發現導覽列消失的嚴重回歸 (Regression)，已登錄追蹤。
