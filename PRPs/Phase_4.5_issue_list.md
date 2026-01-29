# Phase 4.5 Issue List & Clarifications

此文件彙整了關於 Phase 4.5 開發過程中的關鍵問題、釐清事項與待辦修復。

## 1. 已釐清項目 (Clarified Items)

| ID | Issue | Status | Description/Resolution |
| :--- | :--- | :--- | :--- |
| **CL-01** | `make db-init` 安全性 | ✅ Resolved | **結論**: `make db-init` 是**增量且安全**的。它**不會**刪除 `knowledge` 或 `archon_service` 資料表內容。它只執行新的 migration 並確保 seed data 存在 (使用 `ON CONFLICT DO UPDATE`)。無需手動去 Supabase 刪除資料。 |
| **CL-02** | `make clean` 破壞性 | ✅ Resolved | **結論**: `make clean` **會清除 Docker Volumes**。這意味著**資料庫內的資料會被清空**。執行後需重新 `db-init`，且之前的動態資料 (如 Knowledge) 會遺失。開發時請謹慎使用。 |
| **CL-03** | Auth vs Profile 不一致 | ✅ Resolved | **結論**: `init_db.py` 內建 `sync_profiles_to_auth` 機制，會自動比對並修復 `profiles` 與 `auth.users` 的 ID 對應。Supabase `auth.users` 若有多餘帳號通常不影響系統運作，可忽略或手動清理。 |
| **CL-04** | Style Guide 參考 | ✅ Resolved | **結論**: <br>1. **Admin UI**: `:3737/style-guide` (若 `STYLE_GUIDE_ENABLED=true`)。<br>2. **Code**: 參考 `PRPs/ai_docs/UI_STANDARDS.md`。<br>3. **Components**: 參考 `archon-ui-main` 的 `Table`, `Card` 等封裝。 |
| **CL-05** | RAG 預設模型 (Google) | ✅ Resolved | **結論**: `seed_mock_data.sql` 設定 `LLM_PROVIDER` 預設為 `'google'`。若目前行為是 OpenAI 優先，請檢查 `.env` 或 `archon_settings` 資料庫值。 |
| **CL-06** | OpenAI 429 Error | ✅ Resolved | **結論**: 錯誤訊息明確指出 OpenAI Quota 不足。短期解決方案是切換 `LLM_PROVIDER` 至 `google` (Gemini)。 |
| **CL-07** | 環境重置順序 | ✅ Resolved | **結論**: 您的理解正確：`make clean` (清除 Volume) -> `make dev-docker` (啟動服務) -> `make db-init` (重建 Schema 與 Seed Data)。這會產生最乾淨的環境。 |

## 2. 待討論/新增項目 (Pending Issues)

> 以下項目源自使用者上傳的 5 張截圖。

| ID | Issue | Priority | Status | Description | User Action Required |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **IMG-01** | **Admin UI Supabase Settings** | Low | Discussion | **截圖**: Admin Control Center -> Settings。<br>**問題**: Admin UI 提供了 Supabase 設定欄位 (URL/Key)。<br>**疑問**: 這裡的設定是否會覆蓋 `.env`？<br>**分析**: `init_db.py` 顯示有 `db-init` 種子資料的機制。Admin UI 可能是為了在不重啟的情況下動態調整，但通常 `.env` 是 Source of Truth。 | **Proposal**: 移除此設定面板，避免混淆，強制使用 `.env`。 |
| **IMG-02** | **Document Version Audit Trail Empty** | Medium | Investigation | **截圖**: Document Versions -> Audit Trail 空白。<br>**問題**: 看起來功能未運作或無資料。<br>**分析**: 需要確認後端是否有記錄 Audit Log，或者只是目前沒有文件變更紀錄。 | **Proposal**: 1. 新增 Mock Audit Data 以供展示。<br>2. 檢查 `DocumentService` 是否正確寫入 Log。 |
| **IMG-03** | **Pitch Generation Failure (429)** | **Critical** | **✅ Fixed (Config)** | **截圖**: "Failed to generate pitch. Please try again."<br>**問題**: 行銷頁面生成 Pitch 失敗。<br>**分析**: 錯誤碼 429 (Insufficient Quota) 確認是 OpenAI 額度問題。代碼位置: `MarketingPage.tsx`。<br>**解法**: 切換至 Gemini 或儲值 OpenAI。 | **Action**: 將 `LLM_PROVIDER` 切換為 `google` (Server Config)。 |
| **IMG-04** | **Team Management UI & Budget** | Low | **✅ Done** | **截圖**: Team Management 卡片介面。<br>**問題**: DevBot 顯示 "SHARED BUDGET 0%"。<br>**分析**: 這可能是預設值，或者預算系統尚未完全實作。UI 與之前討論的 Table 形式不同，使用了 Card 形式。 | **Proposal**: 1. 修改 Avatar 為方形 (所有部門)。<br>2. 依部門設定不同邊框顏色區分。<br>3. 修復 `View Activity` 連結 (目前無效)。 |
| **IMG-05** | **Manager Role UI** | Low | Info | **截圖**: Charlie Brown 顯示 "MANAGER" badge。<br>**分析**: 確認 RBAC UI 顯示正常。 | 無。 |
| **FB-01** | **Alice Promote Failure** | **High** | **✅ Fixed** | **問題**: Alice (及所有人) 無法 Promote to Vendor。<br>**深度分析**: <br>1. **Schema Mismatch (Critical)**: `marketing_api.py` 嘗試寫入 `contact_email` 至 `vendors` 表，但 `008` 遷移檔僅新增 `contact_info` (JSONB) 而無 email 欄位。<br>2. **RBAC**: 權限檢查邏輯本身可能正確，但因 SQL 錯誤導致失敗。<br>**驗證**: 後端 Log 應顯示 "Column contact_email does not exist"。<br> | **Fix**: 1. 新增 migration `015` 補上 `contact_email` 欄位。<br>2. 修正後端代碼以符合 Schema。<br>3. 強化 Error Log。 |
| **FB-02** | **"NA" Position in Leads Table** | Medium | **✅ Verified** | **問題**: Leads Table 的 Position 欄位顯示 "NA"。<br>**分析**: `MarketingPage.tsx` 使用 `lead.job_title`。需確認 `leads` table schema 是否有資料。 | **Fix**: 檢查資料寫入流，或從 `description_snippet` 提取。 |
| **FB-03** | **Task Visibility (Alice/Bob)** | **High** | **✅ Fixed** | **問題**: Alice/Bob 看不到自己建的任務。<br>**分析**: `task_service.py` Line 220 執行 `.eq("assignee_id", assignee_id)`。<br>**連動性**: `TaskService` 目前不支援 `OR` 查詢 (e.g. Me OR Null)。若只改 Router 傳 `None` 會變成 Admin 模式 (看全部)。<br>**必要修改**: 必須修改 `task_service.py` 的 SQL 建構邏輯，支援 `filter_mode="me_or_unassigned"`。 | **Fix**: 修改 `TaskService.list_tasks` 支援複合過濾。 |
| **FB-04** | **"User" Name in Task** | Medium | **✅ Fixed** | **問題**: 任務 Assignee 顯示 "User"。<br>**分析**: `api.ts` `createTask` 行 251 硬編碼了 `assignee: "User"`。<br>**解決**: 移除硬編碼。 | **Fix**: 修改 `api.ts`。 |
| **FB-05** | **Lead Table Sorting** | Low | **✅ Done** | **問題**: 使用者希望能在表上顯示搜尋日期並排序。<br>**分析**: `leads` table 有 `created_at`。 | **Feature**: 前端新增欄位與排序。 |
| **FB-06** | **Duplicate MarketBots** | Low | **✅ Fixed** | **問題**: Profile 列表中出現兩個 Marketing Bot。<br>**分析**: `TeamManagementPage.tsx` 混用了 DB 資料與 Hardcoded Data。<br>**RBAC**: `RBAC_Collaboration_Matrix.md` 定義 Agents 為 DB 實體 (`L4-U`)。 | **Fix**: 移除前端 Hardcoded Data，嚴格遵循 DB 為 Single Source. |
| **UI-01** | **My Tasks Card View** | Medium | **✅ Done** | **截圖**: 使用者上傳圖片顯示卡片太過簡陋。<br>**分析**: 缺 Description, Priority Color, Due Date formatting。<br>**解法**: 參考 `UI_STANDARDS.md` 的 `GlassCard` 重構。 | **Fix**: 重構 Task Card UI。 |
| **UI-02** | **Missing Blog Management (Marketing)** | **High** | **✅ Done** | **問題**: Bob (Marketing) 無法在前端管理/新增文章 (目前只有 Admin 有)。<br>**分析**: `AdminPage.tsx` 有完整 Blog 功能，但 `BrandPage.tsx` 可能缺失。<br>**RBAC**: Marketing Team 應擁有 Content Assets 管理權。 | **Fix**: 將 Blog Management 移植/複用於 `BrandPage.tsx`。 |
| **UI-03** | **System Prompt Icons** | Low | Improvement | **截圖**: Admin System Prompts 列表。<br>**問題**: 列表僅有文字，難以識別是哪個 Agent 的 Prompt。<br>**建議**: 左側卡片加入 User/Bot Avatar。 | **Fix**: 建立 `Prompt -> Agent Icon` 的 Mapping 並顯示於列表。 |
| **EF-01** | **Prompt Feedback Loop** | Medium | Feature | **問題**: 使用者希望能對 Prompt 按讚或建議修改。<br>**方案**: 透過 "Report Issue" 或 "Suggest Change" 按鈕，將建議轉為 **Task** 指派給 Admin/Manager。 | **Feature**: 實作 `Create Feedback Task` 流程。 |
| **Q-01** | **"Market Specs" Unclear** | Low | Info | **問題**: 使用者對 "Market Specs" 的數據定義感到困惑。<br>**分析**: 後端 `get_market_stats` 僅是統計 Leads 中 `identified_need` 包含 AI/LLM 的數量。並非嚴格的規格分析。 | **Action**: 在 UI tooltip 或文件說明此數據為 "Keyword Trend Analysis"。 |
| **CL-04** | **Theme Discrepancy** | High | **✅ Fixed** | **問題**: Port 5173 (End User) 與 3737 (Admin) 主題不一致。<br>**分析**: Admin UI 使用自定義 Tailwind Config，End User 使用預設。需對齊。 | **Plan**: 以 Admin UI 為準，移植色彩變數至 `index.css`。 |

## 3. Action Items

- [x] **Config Check**: 確認 `archon_settings` 中的 `LLM_PROVIDER` 是否為 `google`。
- [x] **Gemini Key**: 確保 `.env` 中設定了有效的 `GEMINI_API_KEY`。
- [x] **UI Inspection**: 根據使用者上傳的圖片進行 UI 檢視。
