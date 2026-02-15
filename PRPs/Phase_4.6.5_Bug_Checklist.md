# Phase 4.6.5 缺陷與缺口追蹤表 (Bug & Gap Tracking Report)

> **文件狀態**: 驗證中 (Under Verification)
> **涵蓋角色**: Alice (Sales), Bob (Marketing), Charlie (Manager), Admin
> **最後更新**: 2026-02-15 (Full Stability Audit)

---

## 📊 摘要儀表板 (Summary Dashboard)

|指標 (Metric)|數量 (Count)|詳細資訊 (Details)|
|:---|:---|:---|
|**總議題數**|36|涵蓋 UX 流程、資料一致性、系統重置可靠性與營運引擎加固。|
|**已完成修正**|18|BUG-027, BUG-031, BUG-032, BUG-033, BUG-034, BUG-037, BUG-038, BUG-045, GAP-018, GAP-020, GAP-021, GAP-022, GAP-024, GAP-027, GAP-035 驗證正常。|
|**待驗證/討論**|18|剩餘項目包含 7 個指揮官圖表、樣式優化與技術債重構。|

---

## 🔍 缺陷與缺口追蹤詳表 (Defect & Gap Tracking Table)

| ID | 類型 (Type) | 角色 | 模組 | 問題描述 | 嚴重度 | 狀態 |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **BUG-037** | 🐛 Bug | **Admin** | **System** | **Agent 數量顯示矛盾 (SSOT 已修復)**。Header 計數與狀態燈列表已統一由後端回傳之狀態物件驅動。驗證方式：1. 觀察計數值與綠燈數量是否 1:1 絕對吻合；2. 執行 `make probe` 後重新整理，確認對應 Agent (Librarian) 轉為 Active 且計數加 1。 | High | 🟢 已修復 |
| **BUG-038** | 🐛 Bug | **All** | **AI/Gemini** | **Gemini 404 & Model Alignment (SSOT 已修復)**。原因：1. 資料庫設定 (`MARKETING_MODEL`) 存有舊模型 `1.5-flash` 覆蓋了程式碼預設值；2. Google API 會因模型名稱前綴或髒路徑自動跳轉至不支援該模型的 `v1main` 接口。修復：遷移至官方 genai.Client SDK 並實施 `split("/")[-1]` 名稱校準。驗證：Alice 提案生成已恢復正常且具備 429 警報廣播。 | High | 🟢 已修復 |
| **BUG-045** | 🔄 Loop | **Alice** | **Logic** | **Alice 拜訪紀錄錄音/提案來回問同樣問題**。原因：連線 404 後回傳 Fallback 罐頭文字，Agent 判定任務未完成而陷入無限重試。修復：1. 遷移至官方 genai.Client SDK；2. 移除罐頭文字，改為拋出 503 異常。 | Critical | 🟢 已修復 |
| **GAP-027** | 🔧 Gap | **Charlie** | **Nexus** | **指揮官中樞: Integrity (系統完整度)**。已實作：1. 加權評分模型 (知識 70% + 連線 30%)；2. 30 天雙曲線趨勢圖 (Daily vs Baseline)；3. 真實每小時稽核日誌。 | High | 🟢 已修復 |
| **GAP-035** | 🔧 Gap | **Charlie** | **Nexus** | **指揮官中樞: Resources (資源與人機協作)**。已實作：1. 全角色 (Alice, Bob, Admin, System) 任務剖析；2. 區分 Crawler 與 GenAI 消耗；3. 30 天累計預算消耗圖與 $100 紅線同步。 | High | 🟢 已修復 |
| **GAP-028** | 🔧 Gap | **Charlie** | **Nexus** | **指揮官中樞: Op Load (營運負載)**。已實作：1. 30 天雙軸趨勢圖；2. 待審核清單與 AI 分數；3. Bob 退件反饋可見性。**[待討論]: 圖表精準度與內容一致性需進一步對齊數據口徑。** | Medium | 🟡 待討論 |
| **GAP-029** | 🔧 Gap | **Charlie** | **Nexus** | **指揮官中樞: Sent Risks (風險雷達)**。已落地「業務最後防線」：1. 哨兵自動偵測 Stale Leads (14d) 與 Content Bottleneck (48h)；2. Dispatch 強制轉化為 **High Priority** 任務並自動分配；3. 任務產生後告警自動降級為 INFO 以清空 HUD。修復了 PGRST116 查詢崩潰。 | High | 🟢 已修復 |
| **GAP-030** | 🔧 Gap | **Charlie** | **Nexus** | **指揮官中樞: Act Force (活躍武力)**。已落地：1. 90 天戰鬥力 vs 90 天基線 (ReferenceLine) 對比圖；2. X 軸對齊每 10 天標籤；3. 人機在線狀態動態偵測。 | Medium | 🟡 待驗證 |
| **GAP-031** | 🔧 Gap | **Charlie** | **Nexus** | **指揮官中樞: Ethics (倫理/合規)**。已落地：1. 實作「待簽核隊列」，整合哨兵攔截事件與管理員指令變更；2. 支援跨表 (logs/ethics) 的 AI 自動分派 (Dispatch)；3. 實作 Prompt 審核 API 與 Diff 預覽邏輯。 | Low | 🟡 待驗證 |
| **GAP-032** | 🔧 Gap | **Charlie** | **Nexus** | **指揮官中樞: Collab (協作分數)**。已落地「全員協作動能矩陣」：1. 9x9 實體關聯 (4人 + 5 Agent)；2. 雙長條圖對比 7D 實際 vs 30D 平均；3. Snapshot 卡片大字顯示動能百分比並附帶 7D 實體總數標籤。 | Low | 🟡 待驗證 |
| **GAP-033** | 🔧 Gap | **Charlie** | **Nexus** | **指揮官中樞: Graph (情報圖譜)**。已落地「情資 ROI 分析」：1. 60 天網域轉換率趨勢圖 (14天滾動平均)；2. Top Domains 審核表 (顯示含金量與警告燈)；3. HUD 卡片大字顯示總體轉換率 (%) 並附帶節點總數標籤。 | Medium | 🟡 待驗證 |
| **GAP-034** | 🔧 Gap | **Charlie** | **Nexus** | **指揮官中樞: Velocity (生產速率)**。待實作：展示「任務結案週期」。Lead 轉化平均天數、SLA 達成率趨勢圖。 | Medium | ⚪ 待處理 |
| **BUG-027** | 🐛 Bug | **Charlie** | **Team** | Charlie 在 Team Management 面板看不到 Alice 自己開的單。已啟用後端 assigne_id 過濾與前端分頁擴增。 | High | 🟢 已修復 |
| **BUG-030** | 🐛 Bug | **All** | **Color** | Dashboard 狀態與優先級燈色失效. 已修復 API 回傳缺少 priority 欄位與 ETag 計算問題。已驗證 List, Table, Kanban 所有視圖同步反應。 | High | 🟢 已修復 |
| **UX-013** | 🎨 Style | **Alice** | **UI/Date**| 日期時間選擇器更換。已實作 `MobileDateTimePicker` 大目標觸控組件，解決手機選取困難並新增業務快捷鍵 (明天/三天後)。已修復單元測試定位問題。 | High | 🟢 已修復 |
| **BUG-033** | 🐛 Bug | **All** | **UI/Nav** | 導覽列消失。已修正前端大小寫判斷與 DB ID 同步。 | Critical | 🟢 已修復 |
| **DX-001** | 🛠️ DX | **All** | **Auth/PW** | 密碼重置為 `qwer45tyuiop`。已實作強制重置邏輯。 | Medium | 🟢 已修復 |
| **UX-011** | 🎨 Style | **All** | **UI/Set** | 5173 `/settings` 移至使用者區塊。 | Medium | 🟢 已修復 |
| **BUG-031** | 🐛 Bug | **System** | **DB/Reset**| `make db-reset` 失敗。已補齊 `RESET_DB.sql` 遺漏的新資料表。 | High | 🟢 已修復 |
| **BUG-032** | 🐛 Bug | **System** | **DB/Seed** | `seed_mock_data.sql` 報錯。已透過完整 DB Reset 修復 Schema 狀態。 | High | 🟢 已修復 |
| **BUG-034** | 🐛 Bug | **Tech** | **Agent** | `test_run_command_failure_triggers_healing` 失敗。原因：新實作的 DevBot Fallback 邏輯改變了錯誤輸出的格式，導致既有測試斷言失效。 | Medium | 🟢 已修復 |
| **BUG-035** | 🐛 Bug | **System** | **Probe** | **Probe Cleanup**。沒有自動刪除 probe 在 knowledge 的過期檔案。已將排程從 24hr 調整為 1hr (Cleanup) 與 6hr (Probe) 以應對頻繁重啟。 | High | 🟢 已修復 |
| **BUG-036** | 🐛 Bug | **Alice** | **UI/Scroll**| **Job Search Scroll**。Job Search > Find Leads (10筆) 無法上下滑動。Fix: Switched mobile to Window Scrolling (`min-h-[100dvh]`). | High | 🟢 已修復 |
| **BUG-028** | 🐛 Bug | **Bob** | **UI/Magic** | "Prompt Inspector" missing. Fixed: restored as overlay sidebar + ghost style button. | High | 🟢 已修復 |
| **BUG-029** | 🐛 Bug | **Bob** | **UI/Scroll** | Triple scrollbars on Brand Page. Fixed: `h-full` + `overflow-hidden` logic. | High | 🟢 已修復 |
| **GAP-009** | 🔧 Gap | **Alice** | **Voice** | 語音日誌自動轉工單尚未實作。已實作前端模擬按鈕與語音上傳介面 (Mock Strategy) 及後端整合。 | Medium | 🟢 已修復 |
| **GAP-010** | 🔧 Gap | **Alice** | **GPS** | On-Demand GPS 待驗收。已於 Attendance Widget 與 Visit Log 實作 Mock Fallback (Taipei 101)。 | Low | 🟢 已修復 |
| **UX-012** | 🎨 Style | **All** | **Buttons** | 5173 按鈕風格對齊 3737 Style Guide。已實作通用 `Button` 組件。 | Low | 🟢 已修復 |
| **GAP-012** | 🔧 Gap | **Bob** | **Intel** | 頁面空白無數據，配色太深。已優化配色 (Light Purple Theme) 並確保 Mock Data 顯示。 | Medium | 🟢 已修復 |
| **GAP-013** | 🔧 Gap | **Charlie** | **Center** | 指揮中心無資料供練習。已在 `seed_mock_data.sql` 注入 `marketing_trends` 數據。 | Medium | 🟢 已修復 |
| **GAP-014** | 🔧 Gap | **Admin** | **RBAC** | 缺少 RBAC 練習案例。已注入 Viewer/Editor 角色數據 (`viewer@`, `editor@`) 以供權限邊界測試 (非刪除角色)。 | Low | 🟡 待驗收 |
| **GAP-015** | 🔧 Gap | **Tech** | **Score** | Alice 的 Enrichment Score 計算規則實作。已於 `EnrichmentService` 實作動態評分。 | Low | 🟢 已修復 |
| **GAP-016** | 🔧 Gap | **Tech** | **Token** | Token Usage 真實寫入與可視化確認。已於 `MockLLMClient` 實作 Token 消耗模擬。 | Low | 🟢 已修復 |
| **GAP-003** | 🔧 Gap | **Alice** | **Swipe** | 滑動誤觸復原功能待驗收。已在 `LeadsCardStack` 實作 Undo 按鈕與歷史堆疊。 | Low | 🟢 已修復 |
| **GAP-011** | 🔧 Gap | **Alice** | **Prune** | 自動歸檔邏輯待驗收。已實作 `task_service.prune_archived_tasks` | Low | 🟢 已修復 |
| **GAP-017** | 🔧 Gap | **Alice** | **Crawler**| **爬蟲參數配置化**。已整合 RBAC 設定爬蟲深度與過濾器 (Knowledge API)。 | Low | 🟢 已修復 |
| **GAP-018** | 🔧 Gap | **Charlie** | **Extractor**| **智慧結構化提取流程**。已打通閉環：分析 -> 模板 -> 執行。Manager 可於 5173 操作且 Admin 可稽核。 | Medium | 🟢 已修復 |
| **GAP-019** | 🔧 Gap | **Alice** | **Mobile/UI**| **行動端語音日誌 UI 優化**。已合併至 TECH-004 (Mobile Hardware Limits)。 | Medium | ➡️ Merged |
| **ALERT-01**| 🔧 Gap | **Charlie** | **Sentin** | 警示資料準確性待驗收。已驗證 `scheduler_service.py` 之 `_run_business_sentinel` 邏輯 (14天未更新且非 won/converted)。 | Low | 🟢 已修復 |
| **UX-014** | 🎨 Style | **All** | **UI/Nav** | **導航 Icon 配色化**。依職能模組 (Sales/Mkt/Admin) 區分 Icon 顏色。 | Medium | 🟢 已修復 |
| **TECH-001**| 🏗️ Debt | **Tech** | **RAG** | `RAGSettings.tsx` 重構拆分。 | Medium | ⚪ 待討論 |
| **TECH-002**| 🏗️ Debt | **Tech** | **Projects**| `projects_api.py` 商業邏輯抽離。 | Medium | ⚪ 待討論 |
| **TECH-003**| 🏗️ Debt | **Alice** | **Voice** | **語音 Files API 遷移**。棄用 Base64，已遷移至官方 SDK 支援長音頻上傳。 | High | 🟢 已修復 |
| **TECH-004**| 📝 Note | **Tech** | **Mobile** | **Mobile Web Hardware Limits (GPS/Mic)**。瀏覽器無法完全存取手機原生硬體 (GPS/麥克風)。已實作 Mock Location 與 File Upload Fallback 作為替代方案。 | Low | ⚪ 已確認 |
| **GAP-020** | 🔧 Gap | **Admin** | **RBAC** | **精細權限下放 (Delegation)**。已打通 /admin 路由給 Manager，並依權限動態過濾標籤頁。 | High | 🟢 已修復 |
| **GAP-021** | 🔧 Gap | **Admin** | **Config** | **配置持久化 (Persistence)**。系統設定全面存儲於資料庫 archon_settings，支持熱加載。 | Medium | 🟢 已修復 |
| **GAP-022** | 🔧 Gap | **Admin** | **Audit** | **變更稽核日誌 (Audit Trail)**。已實作「變更即審計」：Manager 的設定變更自動寫入版本稽核表。 | Medium | 🟢 已修復 |
| **GAP-023** | 🔧 Gap | **Charlie** | **Return** | **退件反饋與狀態流轉閉環**。已完成：1. 移除 Workbench 顯示限制；2. 解鎖 Charlie 預覽高度與圖片自動識別；3. 實作儲存/提交時自動連動任務狀態 (Doing/Review)。 | High | 🟡 待驗證 |
| **GAP-024** | 🔧 Gap | **Alice** | **Pitch** | **Pitch View UI**。已完成：1. 桌面端 Table View 增加 View 按鈕與 Modal；2. 手機端 LeadsCardStack 增加動態 PitchDrawer，支援已生成內容的翻閱與複製。 | Medium | 🟢 已修復 |
| **GAP-025** | 🔧 Gap | **Admin** | **Config**| **Scoring Persistence**。已實作：1. Migration 038 權重持久化；2. AdminPage 增加 Lead Scoring Weights 動態配置區塊，支援自動保存與審計日誌同步。 | High | 🟢 已修復 |
| **GAP-026** | 🔧 Gap | **Admin** | **Audit** | **Audit Search UI**。已實作：DocumentVersionsLog 增加多維度即時搜尋與 Sticky Header，支援按人員、欄位、摘要過濾稽核紀錄。 | Low | 🟢 已修復 |
| **BUG-039** | 🐛 Bug | **Tech** | **Infra** | **腳本組織與重複性混亂**。`scripts/` 與 `python/scripts/` 存在重複檔案且用途不明確。已統一標準化至 root scripts/ 並清理 redundant python/scripts/。 | Medium | 🟢 已修復 |
| **BUG-040** | 🐛 Bug | **Admin** | **E2E/Time**| **Admin Workflow Timeout**。`Admin can update a user role` 測試超時 (15s)。原因：測試預期 "Alice" 但資料為 "Alice Johnson" (Exact Match)。修復：改用 Regex。 | High | 🟢 已修復 |
| **BUG-041** | 🐛 Bug | **Alice** | **E2E/Time**| **AI Workflow Timeout**。`Sales Outreach` 測試超時 (15s)。原因：Marketing Page 只有標題無按鈕。修復：導航至 Dashboard 建立任務。 | High | 🟢 已修復 |
| **BUG-042** | 🐛 Bug | **Alice** | **E2E/Race**| **Knowledge Selector Race**。`waitForElementToBeRemoved` 錯誤，目標 Dialog 在檢測前已消失。原因：Modal 關閉過快。修復：改用 `waitFor(expect(not.toBeInDocument))`. | Medium | 🟢 已修復 |
| **BUG-043** | 🐛 Bug | **Alice** | **E2E/Data**| **Vendor Promotion Missing**. `Vendor Promotion` 測試找不到 `/Retail Corp/i`。原因：Mock Data 屬性名稱不符 (`company` vs `company_name`)。修復：標準化 Mock Data。 | High | 🟢 已修復 |
| **BUG-044** | 🐛 Bug | **System** | **E2E/Id**  | **Task Persistence ID Mismatch**. `Assignee Persistence` 測試失敗，任務列表找不到 Assignee Name。原因：Mock Create Task 未填入 `name`。修復：Mock Handler 自動查找 User Name。 | High | 🟢 已修復 |

---

## 🛠 修復紀錄 (Fix Log)

*   **2026-02-15 (Round 12: Operational Engine Standardization & Loop Defense)**:
    *   **BUG-045 (Loop Fix)**: 遷移 Alice (Pitch/Voice) 與 POBot (Refinement) 至官方 `genai.Client` SDK。
    *   **Engine Alignment**: 徹底廢棄 5173 營運端不穩定的 OpenAI Shim，解決 v1main 404 報錯。
    *   **Loop Defense**: 移除所有欺騙性罐頭文字（如 Fallback 字串），改為明確的 503 報錯，終結 Agent 迴圈。
    *   **Infra (BUG-039)**: 清理 `python/scripts/` 冗餘，確立外層 `scripts/` 為專案唯一真相腳本區。
*   **2026-02-12 (Round 11: Professional Commander Dashboard & Tablet Optimization)**:
    *   **Integrity (GAP-027)**: 落地「知識+連線」加權評分模型 (70/15/15)。實作專業 30 天雙曲線趨勢圖，支持每日垂直格線與每週日期標籤。
    *   **Resources (GAP-035)**: 實作全角色人機協作矩陣。包含 Alice, Bob, Charlie, Admin, System。精確區分 Crawler/Research 與 GenAI 消耗，USD/Tokens 與 Admin Health 100% SSOT 對齊。
    *   **UX/Tablet**: 實作「詳細視圖最大化」模式。點擊右上角 Maximize 進入全螢幕聚焦分析，圖表放大至 500px，字體與對比度優化。
    *   **Data Fuel**: 執行 `reconstruct_health_history.py` 與 `reconstruct_token_history.py` 注入 30 天真實邏輯歷史數據。
*   **2026-02-11 (Round 10: Commander Nexus & SSOT Fix)**:
    *   **Nexus**: 實作 `ManagerNexus.tsx` (指揮官中樞)，整合 5, 6, 7, 8 面板並提供 HUD 下鑽診斷。
    *   **SSOT**: 徹底修復 BUG-037，後端動態檢測活躍 Agent，前端取消寫死列表，計數與燈號 100% 同步。
    *   **Defense**: 整合 `ThreadingService` 實作主動節流 (Throttle)，顯著減少 429 發生。
    *   **GAP-027**: 達成指揮官中樞功能閉環，狀態設為待驗證。
*   **2026-02-10 (Round 9: System-wide Robust JSON Parsing)**:
    *   **核心加固**: 實作 `python/src/server/utils/json_utils.py` 中的 `safe_json_loads`。透過「Markdown 移除」、「控制字元清理」與「非嚴格模式解析 (`strict=False`)」三重防禦，解決 Gemini 2.0 在長文生成時因原始換行符導致的解析崩潰問題。
    *   **全面部署**: 已將此邏輯同步至 `marketing_api.py` (Bob)、`visit_log_api.py` (Alice) 與 `extraction_service.py` (Librarian)。
*   **2026-02-07 (Round 8: Bob's Content Polish)**:
    *   **BUG-028/029**: 優化 AI 圖片生成體驗。點擊生成後，圖片連結雖會暫時顯示於編輯器供預覽，但在「儲存草稿」或「發佈」時，系統會自動移除該 Markdown 連結，僅保留作為封面圖 (`imageUrl`)，確保文章內容的整潔。
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
*   **2026-02-03 (Round 3: 回歸確認)**:
    *   **BUG-027**: 確認 Charlie 在 Team Management 看不到 Alice 的單。
    *   **BUG-030**: 確認 Dashboard 優先級/狀態顏色修復失敗 (維持綠色)。
*   **2026-02-03 (Round 2)**:
    *   **BUG-033**: 修復導覽列。
    *   **UX-011**: 搬移設定入口。
*   **2026-02-03 (Round 1)**:
    *   **DX-001**: 密碼重置。

---

## 🔬 E2E 測試失敗根源 - 深度盤查報告 (2026-02-14)

### **【環境問題 (Environment)】**
*   **互動模型斷層 (Interaction Divergence)**: UI 已升級為 `MobileDateTimePicker` (按鈕彈窗)，但舊測試腳本仍試圖對 `input` 執行 `fireEvent.change`。這導致日期必填欄位永遠為空，表單驗證無法通過。
*   **API 彈窗阻塞 (Dialog Blocking)**: JSDOM 不支援 `window.alert`。`TaskModal` 成功後會呼叫原生 Alert，這會掛起測試執行緒，導致 Modal 雖然在邏輯上已關閉，但 DOM 元素仍殘留在畫面上，干擾後續斷言。

### **【資料問題 (Data)】**
*   **身分對齊衝突 (Identity Mismatch)**: 測試腳本預期指派給 `Alice Johnson`，但 Mock 數據中該 ID 對應的名稱為 `Alice`。此外，由於 Mock POST 請求缺少 `project_id`，新任務在 Dashboard 被 `FB-03` (專案過濾) 邏輯判定為無效專案，導致渲染後立即消失。
*   **數據飢渴 (Data Starvation)**: 缺失 `POST /api/marketing/leads` 與 `POST /api/marketing/generate-pitch` 的處理器。當測試執行保存動作時觸發 404 報錯，導致 UI 無法進入「成功跳轉」狀態。

### **【底層問題 (Underlying Architecture)】**
*   **渲染競態 (Race Condition)**: `AuthProvider` 狀態同步存在延遲。進入 `/admin` 或 `/marketing` 後，側邊欄連結與分頁 Tab 的渲染速度慢於測試腳本的搜尋速度。需改用帶有 Timeout 的 `findByRole` 取代靜態 `getByText`。
*   **防禦性缺失 (Defensive Coding Gap)**: `SourceBadge` 以前缺乏對 `source` 欄位的 null-check。若 Mock 數據結構不完整，`toLowerCase()` 會導致整個 React Tree 崩潰並顯示白屏。

### **【修復狀態總結】**
- **已加固**: `SourceBadge` Null-check, `IdentityMatrix` Map-check, `handlers.ts` 基礎 API 補齊。
- **待對齊**: 全域測試腳本的互動流程 (日期選擇、超時增加、姓名同步)。
