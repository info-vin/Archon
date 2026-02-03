# Phase 4.6.5 缺陷與缺口追蹤表 (Bug & Gap Tracking Report)

> **文件狀態**: 驗證中 (Under Verification)
> **涵蓋角色**: Alice (Sales), Bob (Marketing), Charlie (Manager), Admin
> **最後更新**: 2026-02-03

---

## 📊 摘要儀表板 (Summary Dashboard)

|指標 (Metric)|數量 (Count)|詳細資訊 (Details)|
|:---|:---|:---|
|**總議題數**|22|涵蓋 UX 流程、資料一致性、系統重置可靠性與開發者體驗 (DX)。|
|**修復待驗收**|6|密碼、導覽列恢復、Reset 腳本、Seed 資料。|
|**重啟調查**|2|Alice 任務可見性 (BUG-027)、狀態顏色失效 (BUG-030)。|
|**待處理**|14|Bob 編輯器斷點、樣式統一、假資料注入。|

---

## 🔍 缺陷與缺口追蹤詳表 (Defect & Gap Tracking Table)

| ID | 類型 (Type) | 角色 | 模組 | 問題描述 | 嚴重度 | 狀態 |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **BUG-027** | 🐛 Bug | **Charlie** | **Team** | Charlie 在 Team Management 面板看不到 Alice 自己開的單。原因待查。 | High | 🔴 重啟調查 |
| **BUG-030** | 🐛 Bug | **All** | **Color** | Dashboard 狀態與優先級燈色失效。修改 LOW->HIGH 後顏色無變化 (維持綠色)。 | Medium | 🔴 重啟調查 |
| **BUG-033** | 🐛 Bug | **All** | **UI/Nav** | 導覽列消失。已修正前端大小寫判斷與 DB ID 同步。 | Critical | 🟡 待驗收 |
| **DX-001** | 🛠️ DX | **All** | **Auth/PW** | 密碼重置為 `qwer45tyuiop`。已實作強制重置邏輯。 | Medium | 🟡 待驗收 |
| **UX-011** | 🎨 Style | **All** | **UI/Set** | 5173 `/settings` 移至使用者區塊。 | Medium | 🟡 待驗收 |
| **BUG-031** | 🐛 Bug | **System** | **DB/Reset**| `make db-reset` 失敗。原因：`RESET_DB.sql` 遺漏新表。 | High | 🟡 待驗收 |
| **BUG-032** | 🐛 Bug | **System** | **DB/Seed** | `seed_mock_data.sql` 報錯。原因：`leads` 插入不存在欄位。 | High | 🟡 待驗收 |
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

*   **2026-02-03 (Round 3: 回歸確認)**:
    *   **BUG-027**: 確認 Charlie 在 Team Management 看不到 Alice 的單。
    *   **BUG-030**: 確認 Dashboard 優先級/狀態顏色修復失敗 (維持綠色)。
*   **2026-02-03 (Round 2)**:
    *   **BUG-033**: 修復導覽列。
    *   **UX-011**: 搬移設定入口。
*   **2026-02-03 (Round 1)**:
    *   **DX-001**: 密碼重置。
