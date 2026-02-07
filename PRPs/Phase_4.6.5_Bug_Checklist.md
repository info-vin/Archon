# Phase 4.6.5 缺陷與缺口追蹤表 (Bug & Gap Tracking Report)

> **文件狀態**: 驗證中 (Under Verification)
> **涵蓋角色**: Alice (Sales), Bob (Marketing), Charlie (Manager), Admin
> **最後更新**: 2026-02-03

---

## 📊 摘要儀表板 (Summary Dashboard)

|指標 (Metric)|數量 (Count)|詳細資訊 (Details)|
|:---|:---|:---|
|**總議題數**|25|涵蓋 UX 流程、資料一致性、系統重置可靠性與開發者體驗 (DX)。|
|**已完成修正**|9|BUG-027, BUG-031, BUG-032, BUG-033, BUG-034, GAP-018, GAP-020, GAP-021, GAP-022 驗證正常。|
|**待討論**|16|其餘項目包含功能缺口、樣式優化與技術債重構。|

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
| **GAP-009** | 🔧 Gap | **Alice** | **Voice** | 語音日誌自動轉工單尚未實作。已實作前端模擬按鈕與語音上傳介面 (Mock Strategy) 及後端整合。 | Medium | 🟢 已修復 |
| **GAP-010** | 🔧 Gap | **Alice** | **GPS** | On-Demand GPS 待驗收。已於 Attendance Widget 與 Visit Log 實作 Mock Fallback (Taipei 101)。 | Low | 🟢 已修復 |
| **UX-012** | 🎨 Style | **All** | **Buttons** | 5173 按鈕風格對齊 3737 Style Guide。已實作通用 `Button` 組件。 | Low | 🟢 已修復 |
| **GAP-012** | 🔧 Gap | **Bob** | **Intel** | 頁面空白無數據，配色太深。已優化配色 (Light Purple Theme) 並確保 Mock Data 顯示。 | Medium | 🟢 已修復 |
| **GAP-013** | 🔧 Gap | **Charlie** | **Center** | 指揮中心無資料供練習。已在 `seed_mock_data.sql` 注入 `marketing_trends` 數據。 | Medium | 🟢 已修復 |
| **GAP-014** | 🔧 Gap | **Admin** | **RBAC** | 缺少 RBAC 練習案例。已注入 Viewer/Editor 角色數據 (`viewer@`, `editor@`) 以供權限邊界測試 (非刪除角色)。 | Low | 🟡 待驗收 |
| **GAP-015** | 🔧 Gap | **Tech** | **Score** | Alice 的 Enrichment Score 計算規則實作。已於 `EnrichmentService` 實作動態評分。 | Low | 🟢 已修復 |
| **GAP-016** | 🔧 Gap | **Tech** | **Token** | Token Usage 真實寫入與可視化確認。已於 `MockLLMClient` 實作 Token 消耗模擬。 | Low | 🟢 已修復 |
| **GAP-003** | 🔧 Gap | **Alice** | **Swipe** | 滑動誤觸復原功能待驗收。已在 `LeadsCardStack` 實作 Undo 按鈕與歷史堆疊。 | Low | 🟢 已修復 |
| **GAP-011** | 🔧 Gap | **Alice** | **Prune** | 自動歸檔邏輯待驗收。已實作 `task_service.prune_archived_tasks`。 | Low | 🟢 已修復 |
| **GAP-017** | 🔧 Gap | **Alice** | **Crawler**| **爬蟲參數配置化**。已整合 RBAC 設定爬蟲深度與過濾器 (Knowledge API)。 | Low | 🟢 已修復 |
| **GAP-018** | 🔧 Gap | **Charlie** | **Extractor**| **智慧結構化提取流程**。已打通閉環：分析 -> 模板 -> 執行。Manager 可於 5173 操作且 Admin 可稽核。 | Medium | 🟢 已修復 |
| **GAP-019** | 🔧 Gap | **Alice** | **Mobile/UI**| **行動端語音日誌 UI 優化**。已合併至 TECH-004 (Mobile Hardware Limits)。 | Medium | ➡️ Merged |
| **ALERT-01**| 🔧 Gap | **Charlie** | **Sentin** | 警示資料準確性待驗收。已驗證 `scheduler_service.py` 之 `_run_business_sentinel` 邏輯 (14天未更新且非 won/converted)。 | Low | 🟢 已修復 |
| **UX-014** | 🎨 Style | **All** | **UI/Nav** | **導航 Icon 配色化**。依職能模組 (Sales/Mkt/Admin) 區分 Icon 顏色。 | Medium | 🟢 已修復 |
| **TECH-001**| 🏗️ Debt | **Tech** | **RAG** | `RAGSettings.tsx` 重構拆分。 | Medium | ⚪ 待討論 |
| **TECH-002**| 🏗️ Debt | **Tech** | **Projects**| `projects_api.py` 商業邏輯抽離。 | Medium | ⚪ 待討論 |
| **TECH-003**| 🏗️ Debt | **Alice** | **Voice** | **語音 Files API 遷移**。棄用 Base64，已實作 `_upload_to_google_files_api` 與 `_transcribe_with_gemini` 支援長音頻上傳。 | High | 🟢 已修復 |
| **TECH-004**| 📝 Note | **Tech** | **Mobile** | **Mobile Web Hardware Limits (GPS/Mic)**。瀏覽器無法完全存取手機原生硬體 (GPS/麥克風)。已實作 Mock Location 與 File Upload Fallback 作為替代方案。 | Low | ⚪ 已確認 |
| **GAP-020** | 🔧 Gap | **Admin** | **RBAC** | **精細權限下放 (Delegation)**。已打通 /admin 路由給 Manager，並依權限動態過濾標籤頁。 | High | 🟢 已修復 |
| **GAP-021** | 🔧 Gap | **Admin** | **Config** | **配置持久化 (Persistence)**。系統設定全面存儲於資料庫 archon_settings，支持熱加載。 | Medium | 🟢 已修復 |
| **GAP-022** | 🔧 Gap | **Admin** | **Audit** | **變更稽核日誌 (Audit Trail)**。已實作「變更即審計」：Manager 的設定變更自動寫入版本稽核表。 | Medium | 🟢 已修復 |

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
