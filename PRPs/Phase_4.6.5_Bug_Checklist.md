# Phase 4.6.5 缺陷與缺口追蹤表 (Bug & Gap Tracking Report)

> **文件狀態**: 驗證中 (Under Verification)
> **涵蓋角色**: Alice (Sales), Bob (Marketing), Charlie (Manager), Admin
> **最後更新**: 2026-02-03

---

## 📊 摘要儀表板 (Summary Dashboard)

|指標 (Metric)|數量 (Count)|詳細資訊 (Details)|
|:---|:---|:---|
|**總議題數**|25|涵蓋 UX 流程、資料一致性、系統重置可靠性與開發者體驗 (DX)。|
|**已完成修正**|4|BUG-027, BUG-031, BUG-032, BUG-033 驗證正常。|
|**待討論**|21|其餘項目包含功能缺口、樣式優化與技術債重構。|

---

## 🔍 缺陷與缺口追蹤詳表 (Defect & Gap Tracking Table)

| ID | 類型 (Type) | 角色 | 模組 | 問題描述 | 嚴重度 | 狀態 |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **BUG-027** | 🐛 Bug | **Charlie** | **Team** | Charlie 在 Team Management 面板看不到 Alice 自己開的單。已啟用後端 assigne_id 過濾與前端分頁擴增。 | High | 🟢 已修復 |
| **BUG-030** | 🐛 Bug | **All** | **Color** | Dashboard 狀態與優先級燈色失效。已修復 API 回傳缺少 priority 欄位與 ETag 計算問題。需確保 List, Table, Kanban, Gantt 所有視圖同步反應。 | High | 🟡 驗證中 |
| **UX-013** | 🎨 Style | **Alice** | **UI/Date**| 日期時間選擇器更換。Alice 手機無法設定時間，需更換為手機/平板/電腦通用的 UI 組件。 | High | 🔴 待處理 |
| **BUG-033** | 🐛 Bug | **All** | **UI/Nav** | 導覽列消失。已修正前端大小寫判斷與 DB ID 同步。 | Critical | 🟢 已修復 |
| **DX-001** | 🛠️ DX | **All** | **Auth/PW** | 密碼重置為 `qwer45tyuiop`。已實作強制重置邏輯。 | Medium | 🟢 已修復 |
| **UX-011** | 🎨 Style | **All** | **UI/Set** | 5173 `/settings` 移至使用者區塊。 | Medium | 🟢 已修復 |
| **BUG-031** | 🐛 Bug | **System** | **DB/Reset**| `make db-reset` 失敗。已補齊 `RESET_DB.sql` 遺漏的新資料表。 | High | 🟢 已修復 |
| **BUG-032** | 🐛 Bug | **System** | **DB/Seed** | `seed_mock_data.sql` 報錯。已透過完整 DB Reset 修復 Schema 狀態。 | High | 🟢 已修復 |
| **BUG-034** | 🐛 Bug | **Tech** | **Agent** | `test_run_command_failure_triggers_healing` 失敗。原因：新實作的 DevBot Fallback 邏輯改變了錯誤輸出的格式，導致既有測試斷言失效。 | Medium | 🟢 已修復 |
| **BUG-028** | 🐛 Bug | **Bob** | **Magic** | 生成失敗 (404)。已強制 v1beta 端點並實作 API 層 Mock Fallback。 | High | 🔵 待驗收 |
| **BUG-029** | 🐛 Bug | **Bob** | **Image** | 圖片失敗。已實作針對 403/429 錯誤的自動 Fallback 邏輯與系統警報日誌。 | High | 🔵 待驗收 |
| **GAP-009** | 🔧 Gap | **Alice** | **Voice** | 語音日誌自動轉工單尚未實作。已實作前端模擬按鈕與語音上傳介面 (Mock Strategy)。 | Medium | 🟡 待驗收 (Mock) |
| **GAP-010** | 🔧 Gap | **Alice** | **GPS** | On-Demand GPS 待驗收。已於 Attendance Widget 與 Visit Log 實作 Mock Fallback。 | Low | 🟡 待驗收 (Mock) |
| **UX-012** | 🎨 Style | **All** | **Buttons** | 5173 按鈕風格對齊 3737 Style Guide。已實作通用 `Button` 組件。 | Low | 🟢 已修復 |
| **GAP-012** | 🔧 Gap | **Bob** | **Intel** | 頁面空白無數據，配色太深。已優化配色並確保 Mock Data 顯示。 | Medium | ⚪ 待討論 |
| **GAP-013** | 🔧 Gap | **Charlie** | **Center** | 指揮中心無資料供練習。已在 `seed_mock_data.sql` 注入 `marketing_trends` 數據。 | Medium | ⚪ 待討論 |
| **GAP-014** | 🔧 Gap | **Admin** | **RBAC** | 缺少 RBAC 練習案例與多樣化資料。已注入 Viewer/Editor 角色數據。 | Low | ⚪ 待討論 |
| **GAP-015** | 🔧 Gap | **Tech** | **Score** | Alice 的 Enrichment Score 計算規則實作。已於 `EnrichmentService` 實作動態評分。 | Low | ⚪ 待討論 |
| **GAP-016** | 🔧 Gap | **Tech** | **Token** | Token Usage 真實寫入與可視化確認。已於 `MockLLMClient` 實作 Token 消耗模擬。 | Low | ⚪ 待討論 |
| **GAP-003** | 🔧 Gap | **Alice** | **Swipe** | 滑動誤觸復原功能待驗收。 | Low | ⚪ 待討論 |
| **GAP-011** | 🔧 Gap | **Alice** | **Prune** | 自動歸檔邏輯待驗收。已實作 `prune_archived_tasks` 服務方法。 | Low | ⚪ 待討論 |
| **GAP-017** | 🔧 Gap | **Alice** | **Crawler**| **爬蟲參數配置化**。需整合 RBAC 設定爬蟲深度與過濾器。 | Low | ⚪ 待討論 |
| **GAP-018** | 🔧 Gap | **Charlie** | **Extractor**| **智慧結構化提取流程**。實作 DevBot 分析結構 -> Charlie 勾選欄位 -> Librarian 執行提取的 No-Code 流程。 | Medium | ⚪ 待討論 |
| **GAP-019** | 🔧 Gap | **Alice** | **Mobile/UI**| **行動端語音日誌 UI 優化**。目前介面偏向桌面端，需實作符合手機操作的「錄音 -> 暫存 -> 一鍵提交」閉環流程。 | Medium | 🟡 驗證中 |
| **ALERT-01**| 🔧 Gap | **Charlie** | **Sentin** | 警示資料準確性待驗收。 | Low | ⚪ 待討論 |
| **UX-014** | 🎨 Style | **All** | **UI/Nav** | **導航 Icon 配色化**。依職能模組 (Sales/Mkt/Admin) 區分 Icon 顏色。 | Medium | ⚪ 待討論 |
| **TECH-001**| 🏗️ Debt | **Tech** | **RAG** | `RAGSettings.tsx` 重構拆分。 | Medium | ⚪ 待討論 |
| **TECH-002**| 🏗️ Debt | **Tech** | **Projects**| `projects_api.py` 商業邏輯抽離。 | Medium | ⚪ 待討論 |
| **TECH-003**| 🏗️ Debt | **Alice** | **Voice** | **語音 Files API 遷移**。棄用 Base64，改用 Google Files API 以支援長音頻。 | High | 🟡 驗證中 |
| **GAP-020** | 🔧 Gap | **Admin** | **RBAC** | **精細權限覆寫 (Permission Override)**。目前權限表寫死於前端 `ROLE_PERMISSIONS_MAP`，需改為後端動態提供以支援單一權限開關。 | High | ⚪ 待討論 |
| **GAP-021** | 🔧 Gap | **Admin** | **Config** | **配置持久化 (Config Persistence)**。`Scoring Logic` 等規則目前僅存於前端 State，需實作 `system_configs` 表進行持久化。 | Medium | ⚪ 待討論 |
| **GAP-022** | 🔧 Gap | **Admin** | **Audit** | **稽核日誌檢視器 (Audit Log Viewer)**。Admin 無法在 UI 上直接搜尋與過濾 `archon_logs` (Audit Trail)。 | Medium | ⚪ 待討論 |

---

## 🛠 修復紀錄 (Fix Log)

*   **2026-02-04 (Round 7: Bob's Resilience)**:
    *   **BUG-028/029**: 實作了「金鑰解耦 (Key Decoupling)」與「Imagen 自動降級」。現在 Bob 的功能優先使用 `GEMINI_API_KEY`，且在外部 API 失敗時會自動切換至 Mock 模式並記錄系統警報。
    *   **TC-Marketing**: 新增 `test_marketing_api_mock.py` 驗證 Bob 的 Fallback 邏輯，達成 100% 覆蓋率。
*   **2026-02-03 (Round 6: Final Clean-up)**:
    *   **UX-012**: 實作 `enduser-ui-fe/src/components/Button.tsx`，對齊 Archon UI 設計規範。
    *   **GAP-011/015/016**: 實作後端自動歸檔、Enrichment 評分演算法及 Token Usage 模擬記錄。
    *   **GAP-013/014**: 更新 `seed_mock_data.sql` 注入戰情中心與 RBAC 測試資料。
*   **2026-02-03 (Round 5: Mock Strategy)**:
    *   **BUG-028/029**: 實作 Backend Mock Fallback。當檢測不到 API Key 時，自動回傳模擬內容與圖片，確保功能流程暢通。
    *   **GAP-009**: 實作「模擬錄音」功能，點擊按鈕直接填入轉錄文字。
    *   **GAP-010**: 實作「模擬定位」功能，當無 GPS 訊號時使用預設座標。
*   **2026-02-03 (Round 4: 核心缺陷修復)**:
    *   **BUG-027**: 修復 Team Management 任務可見性問題。後端 `projects_api.py` 新增 `assignee_id` 過濾支援，前端 `TeamManagementPage.tsx` 改用 Server-Side Filter 並增加分頁上限至 100。
    *   **BUG-030**: 修復 Dashboard 優先級顏色失效。後端 `task_service.py` 補回 API 回傳中遺漏的 `priority` 欄位。
    *   **BUG-031**: 更新 `RESET_DB.sql`，加入 `marketing_trends`, `visit_logs` 等新表的刪除語句。
    *   **BUG-032**: 確認 Schema 與 Seed 一致性，透過完整 Reset 解決潛在狀態不一致。
*   **2026-02-03 (Round 3: 回歸確認)**:
    *   **BUG-027**: 確認 Charlie 在 Team Management 看不到 Alice 的單。
    *   **BUG-030**: 確認 Dashboard 優先級/狀態顏色修復失敗 (維持綠色)。
*   **2026-02-03 (Round 2)**:
    *   **BUG-033**: 修復導覽列。
    *   **UX-011**: 搬移設定入口。
*   **2026-02-03 (Round 1)**:
    *   **DX-001**: 密碼重置。
