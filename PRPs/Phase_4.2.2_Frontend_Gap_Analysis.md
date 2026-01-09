---
name: "PRP 4.2.2: Frontend Gap Analysis & Remediation Implementation Tasks (前端落差分析與修復實作任務)"
description: "解決 `enduser-ui-fe` 功能落差、建立自動化資料庫初始化標準，並為銷售情資功能穩固基礎的詳細實作計畫。"
---

## 原始故事 (Original Story)

**跨越落差 (Bridging the Gap):**
目前的 `enduser-ui-fe` 正處於過渡狀態。雖然我們已經完成了架構嫁接 (Phase 3.8) 並移除了模擬資料 (Phase 3.9.1)，但連接 UI 與真實後端 API 的「膠水」仍然脆弱。本 PRP 的重點是強化這種整合，確保「銷售情資 (Sales Intelligence)」功能建立在一個穩固、可重現的資料庫基礎和反應靈敏、無 Bug 的 UI 之上。

## 故事元資料 (Story Metadata)

**故事類型 (Story Type)**: Fix & Infrastructure (修復與基礎建設)
**預估複雜度 (Estimated Complexity)**: Medium (中)
**主要受影響系統 (Primary Systems Affected)**: `enduser-ui-fe`, `archon-server`, Supabase Database, `migration/` scripts

---

## 情境參考資料 (CONTEXT REFERENCES)

- **CONTRIBUTING_tw.md (Chapter 4.2)**: 「所有資料庫遷移腳本都必須是冪等的 (`IF NOT EXISTS`)...」——這是 Task 1 的黃金標準。
- **frontend-architecture.md (Section 2.2)**: 描述了 Phase 3.8 建立的「人機協作工作流」。Phase 4.2 在不破壞此非同步核心迴圈的前提下，擴展了領域特定的實體 (Leads, Insights)。
- **GEMINI.md (Chapter 2, Pattern 1)**: 「證據至上：日誌是真相。」——我們必須透過伺服器日誌來驗證 API 失敗，而不僅僅是看 UI 症狀。
- **GEMINI.md (Chapter 2, Pattern 7)**: 「內外網隔離。」——確保 `api.ts` 的主動防禦機制 (Proactive Guard) 不會因為資料缺失導致的 404 而錯誤地觸發「Mock 模式」，從而掩蓋了真正的問題。
- **PRPs/Phase_3.9.1_EndUser_UI_Implementation_Tasks.md**: 確認 `MOCK_` 陣列已被移除。UI **必須**依賴 `api.ts` 呼叫真實端點。

---

## 實作任務 (IMPLEMENTATION TASKS)

### Phase 1: 資料庫標準化與自動化 (Database Standardization & Automation)

### 全面審計所有 migration SQL 檔案 (AUDIT All migration/*.sql Files):

- **目標 (GOAL)**: 在自動化之前，確保**所有 10+ 個** SQL 腳本（包含 Schema 定義與種子資料）都嚴格遵守 `CONTRIBUTING_tw.md` 的冪等性規則。
- **範圍 (SCOPE)**: `migration/000_*.sql` 到 `migration/006_*.sql` 以及所有 `migration/seed_*.sql`。
- **分析 (ANALYSIS)**:
    - **結構檢查 (Schema)**: 檢查 `CREATE TABLE`, `ADD COLUMN`, `CREATE FUNCTION` 是否都加上了 `IF NOT EXISTS` 或 `OR REPLACE`。
    - **資料檢查 (Data)**: 檢查 `seed` 檔案中的 `INSERT` 語句。
    - **違規偵測**: 尋找缺乏 `ON CONFLICT DO NOTHING` 或 `ON CONFLICT DO UPDATE` 的裸 `INSERT` 語句。
- **行動 (ACTION)**: 重構所有不合規的 SQL 檔案，確保重複執行也不會報錯或產生重複資料。
- **驗證 (VALIDATE)**: 連續執行兩次 `psql < migration/00x_...sql`。第二次執行必須完全無錯且不改變資料狀態。

### 實作 scripts/init_db.py 與更新 Makefile (IMPLEMENT scripts/init_db.py & UPDATE Makefile):

- **目標 (GOAL)**: 用一個穩健的 Python 腳本取代手動、易錯的 SQL 執行過程，作為資料庫狀態的「單一事實來源」。
- **邏輯 (LOGIC)**:
    1.  **等待連線**: 實作資料庫連線重試機制 (Wait-for-IT)。
    2.  **基建檢查**: 檢查 `schema_migrations` 表是否存在（若無則優先執行 `002` 腳本建立）。
    3.  **依序執行**: 按照字母/數字順序掃描 `migration/*.sql`（排除 `backup` 與 `RESET` 等工具腳本）。
    4.  **版本比對**: 檢查檔案版本號是否已存在於 `schema_migrations`。
    5.  **執行與註冊**: 若未套用則執行 SQL -> 成功後 `INSERT INTO schema_migrations`。
- **MAKEFILE**: 新增 `db-init` 目標，執行 `uv run python scripts/init_db.py`。
- **驗證 (VALIDATE)**:
    - `make clean` (徹底清理環境)
    - `make dev-docker` (啟動空資料庫)
    - `make db-init` (應套用所有腳本)
    - `make db-init` (再次執行，應全部跳過或無變更)

### Phase 2: 關鍵 UI 與狀態修復 (Critical UI/State Fixes)

### 除錯與修復專案/任務建立 (DEBUG & FIX Project/Task Creation):

- **問題 (PROBLEM)**: 「新增專案」按鈕消失或無反應；任務列表未刷新。
- **調查 (INVESTIGATION)**:
    - **主動防禦檢查**: 檢查 `api.ts`。是否因為 `GET /api/projects` 回傳空列表 (有效狀態) 或 404 (錯誤) 而導致系統錯誤地降級為 Mock 模式？
    - **TanStack Query**: 檢查 `useCreateProject` mutation。成功後是否呼叫了 `queryClient.invalidateQueries({ queryKey: ['projects'] })`？
- **行動 (ACTION)**:
    - 確保 `api.ts` 能區分「網路錯誤」(觸發 Mock) 與「空資料」(有效狀態)。
    - 修復 `useProjects.ts` / `useTasks.ts` mutations 中的 `onSuccess` 回呼。
    - 如果「新增專案」按鈕是根據權限渲染的，確保預設權限設定正確。
- **驗證 (VALIDATE)**:
    1.  打開 `http://localhost:5173`。
    2.  點擊 "New Project"。
    3.  填寫表單 -> 提交。
    4.  **預期結果**: Network tab 顯示 `POST /api/projects` 200 OK。列表立即更新，無需重新整理頁面。

### Phase 3: 資料完整性與視覺化 (Data Integrity & Visualization)

### 恢復部落格內容顯示 (RESTORE Blog Content Display):

- **問題 (PROBLEM)**: 儘管有 `seed_blog_posts.sql`，部落格頁面仍然空白。
- **行動 (ACTION)**:
    - 確認 `Phase 1` 已成功寫入 `blog_posts` 資料表。
    - 檢查 `enduser-ui-fe/src/pages/BlogPage.tsx`。確保它呼叫的是 `api.getBlogPosts()` 而不是已移除的 `MOCK_BLOG_POSTS`。
    - 檢查後端 `blog_api.py`。確認它是否正確查詢了 `blog_posts` 表。
- **驗證 (VALIDATE)**: `curl http://localhost:8000/api/blog` 回傳非空 JSON 陣列。瀏覽器正確顯示 Case 1-5 卡片。

### 連接 HR 分析儀表板 (CONNECT HR Analytics Dashboard):

- **問題 (PROBLEM)**: Dashboard 統計數據是靜態的或損壞的。
- **行動 (ACTION)**:
    - 審計 `stats_api.py`。確保端點在資料表為空時能正確處理 `COUNT(*)`（回傳 0，而不是 500）。
    - 將前端 Dashboard 元件連接到 `useStats` hook (包裝 `api.getStats`)。
- **驗證 (VALIDATE)**: 建立一個新任務。檢查 Dashboard 中的 "Active Tasks" 數字是否自動 +1。

### Phase 4: 銷售情資 UI 優化 (Sales Intelligence UI Polish)

### 標準化銷售情資元件 (STANDARDIZE Sales Intelligence Components):

- **目標 (GOAL)**: 將粗糙的 UI 與 `UI_STANDARDS.md` 對齊。
- **參考 (REFERENCE)**: `PRPs/ai_docs/UI_STANDARDS.md` (Tailwind v4, Radix UI).
- **行動 (ACTION)**:
    - 重構 `LeadsList` 與 `MarketInsights` 元件。
    - 使用 `grid` 佈局卡片。
    - 為非同步資料狀態添加骨架屏 (`<Skeleton className="..." />`)。
    - 確保語意化 HTML (避免 `div` soup)。
- **驗證 (VALIDATE)**: 視覺檢查。控制台無 "unique key prop" 或 "invalid DOM nesting" 警告。

### Phase 5: 架構精煉 (Architecture Refinement)

> **目標**: 逐步剝離前端對 Supabase Client 的直接依賴，轉向「後端中心化」架構，以根除 Mock/Real 混合模式帶來的複雜性與 CORS 問題。

### 步驟 5.1: 清理 `supabaseApi` 實作 (Clean up supabaseApi Implementation)

- **目標 (GOAL)**: 確保所有已存在後端 API 的功能 (Blog, Tasks, Projects)，前端都只呼叫 `fetch('/api/...')`，不再混用 `supabase.from(...)`。
- **行動 (ACTION)**:
    - 審計 `enduser-ui-fe/src/services/api.ts` 中的 `supabaseApi` 物件。
    - **待辦**: `updateEmployee` 仍直接呼叫 Supabase，需遷移至後端 API。
    - 移除不再需要的 `supabase` export，封裝在 `api.ts` 內部僅供 Auth 使用。

### 步驟 5.2: 移除 Mock Mode 殘渣 (Remove Legacy Mock Mode)

- **目標 (GOAL)**: 既然 Mock Data 已刪除，`mockApi` 應被徹底移除，讓系統行為更單純。
- **行動 (ACTION)**:
    - [ ] 刪除 `api.ts` 中的 `mockApi` 物件及其定義。
    - [ ] 刪除 `SmartAPI` wrapper 中的 Fallback 邏輯。
    - 當 `Initial Connection Check` (ping `/api/health`) 失敗時，直接拋出明確的錯誤，讓 UI 顯示「系統維護中」或「無法連線」畫面，而不是默默切換到壞掉的 Mock。

### Phase 6: 落差分析 - Phase 4.0 AI as Developer (Gap Analysis)



> **觀察**: 經代碼審查 `ApprovalsPage.tsx`，發現當前實作與 `@PRPs/Phase_4.0_AI_as_Developer_Plan.md` 的願景存在顯著落差。



1.  **即時通知缺席 (No WebSocket)**:

    *   **願景**: 藍圖規劃透過 WebSocket 主動通知開發者有新提案。

    *   **現狀**: 前端完全依賴 `useEffect` 進行一次性拉取 (Polling)，缺乏即時性。

2.  **Git 上下文缺失 (Missing Git Context)**:

    *   **願景**: Agent 應在獨立分支 (`feat/...`) 上工作，UI 應顯示分支資訊。

    *   **現狀**: 前端僅顯示提案列表，缺乏分支切換或顯示當前分支的 UI 元素。

3.  **執行回饋斷裂 (No Shell Output)**:

    *   **願景**: Agent 執行測試 (`make test`) 的結果應回饋給開發者。

    *   **現狀**: UI 僅有 Approve/Reject，無法查看測試日誌或執行結果。



---

## COMPLETION CHECKLIST (完成檢查清單)



- [x] **DB Automation**: `make db-init` script implemented.

- [x] **Seed Data**: `seed_mock_data.sql` and `seed_blog_posts.sql` refactored.

- [x] **Project CRUD**: Fully functional dropdown and creation logic in Dashboard.

- [x] **Task CRUD**: Verified backend/frontend integration.

- [x] **Blog**: Detail pages implemented with Markdown rendering.

- [x] **Dashboard**: Fixed 406 errors by injecting Auth Headers.

- [x] **UI Standards**: Marketing and Blog UI refactored and scrollable.

- [~] **Phase 5 Refinement**: `mockApi` removed (Done). **Migration Status**:
    - [x] `updateEmployee`: Migrated to `/api/users/me` & `/api/users/{id}` (Backend implemented).
    - [x] `updateTask`: Migrated to `/api/tasks/{id}` (Backend upgraded to resolve ID to Name).
    - [x] `getEmployees`: Migrated to `/api/users` (Admin Only, backend implemented).
    - [x] `getDocumentVersions`: Migrated to `/api/versions` (Admin Only, backend implemented).
    - [x] **Auth/Admin Lifecycle** (Completed):
        - [x] `adminCreateUser`: Uses `POST /api/admin/users` (Backend Admin Auth).
        - [x] `register`: Uses `POST /api/auth/register` (Backend Auth).
        - [x] `updateUserEmail`: Uses `PUT /api/auth/email` (Backend Auth).

- [x] **Phase 6 Batch Fixes**: Auth loops, Scrolling, and Blog detail logic completed and verified via Unit Tests.



---

## 🔍 待驗證項目 (Verification Checklist)

- [x] **自動化測試**: `api.stability.spec.ts` 與 `BlogDetailPage.spec.tsx` 全數通過。

- [x] **UI/Unit 測試**: `DashboardPage.test.tsx` 經修復後通過 (Props & A11y fixes)。

- [~] **E2E 測試**: **In Progress**. 環境配置已修復 (`vite.config.ts`)，但需持續驗證 `sales-intelligence` 在真實後端下的穩定性。

- [x] **視覺驗收**: 已修復刷新頁面時的短暫登出 (Session Hydration Lag)，透過在 `onAuthStateChange` 中管理 `loading` 狀態實現。



## 🔍 待驗證項目 (Verification Checklist)

> 休息過後，請依照此清單進行最後驗證，確保「改 A 壞 B」的循環已終結。

### 1. 核心穩定性 (Infrastructure)
- [x] **後端健康度**: `docker ps` 顯示 `archon-server` 與 `archon-agents` 均為 `healthy` (Verified via `main.py` fixes `cadc0b6`).
- [x] **Internal API**: 檢查 `archon-agents` 日誌，確認不再出現 `GET /internal/credentials/agents 404` (Verified via logs & `700b635`).
- [x] **測試通過**: 再次執行 `make test-be`，確保 480+ 個測試維持綠燈 (Verified: All Passed).

### 2. 資料流與 UI (Data Flow)
- [x] **Dashboard 崩潰修復**: 登入後進入 Dashboard，確認不再出現 `tasks?.filter is not a function` 錯誤 (Verified via `api.ts` defensive coding `700b635`).
- [x] **Blog 內容呈現**: 前往 `/blog` 頁面，確認能看到從資料庫載入的 5 篇案例文章 (Verified via `BlogDetailPage.spec.tsx`).
- [x] **CORS 幽靈**: 檢查瀏覽器 Console，確認不再出現針對 Supabase URL 的 `HEAD` 請求造成的 CORS 錯誤 (Verified via `main.py` middleware config `cadc0b6`).
- [x] **Auth 熔斷**: 刻意斷開網路，確認 `Loading...` 畫面會在 2 秒內消失（顯示未登入狀態而非無限卡死）(Verified via `api.ts` timeout `aa61f15`).

---

## 附錄 A: 架構演進分析 (Architecture Evolution Analysis)

本節比較 **Phase 3.8** (系統嫁接) 建立的基礎架構與 **Phase 4.2** (銷售情資) 的擴展能力，證實新功能是核心設計的自然延伸。

| 構面 (Dimension) | Phase 3.8 (基礎建設) | Phase 4.2 (銷售情資擴展) | 分析 (Analysis) |
| :--- | :--- | :--- | :--- |
| **工作流** | 通用任務執行迴圈 <br> (`Task -> Agent -> Result`) | 領域特定業務迴圈 <br> (`Request -> Research -> Insight -> Dashboard`) | **一致性**。Phase 4.2 重用了 Phase 3.8 的非同步工作流，僅豐富了資料載荷。 |
| **資料實體** | `Tasks`, `Projects` | `Tasks`, `Projects` + **`Leads`, `MarketInsights`** | **垂直擴展**。新增資料表 (`006_*.sql`) 是為了支援新業務，未改動核心 Schema。 |
| **Agent 角色** | 通用執行者 (Mock/Basic) | **專業業務助理** (Sales Rep) | **專業化**。Agent 現在配備了領域專用工具 (爬蟲, 104 整合)。 |
| **使用者介面** | 基礎表單與列表 | **互動式儀表板** & 分析圖表 | **視覺化**。UI 現在消費聚合數據 (`stats_api`) 而非僅僅是原始列表。 |

**結論**: Phase 4.2 嚴格遵守 `frontend-architecture.md` 定義的架構原則。它是在通用的框架中填入了具體的業務邏輯。

---

## 附錄 B: Archon 故事集：銷售經理的一天 (Marketing Stories)

> 這些故事旨在以最具感染力的方式，向非技術人員傳遞 Archon Phase 4.2 的核心價值。

### 故事一：從「早晨的焦慮」到「掌控的快感」
*(Target: Real-time Dashboard & Automation)*

**以前的 Alex (銷售經理)**：
週一早晨 8:50。Alex 盯著全黑的咖啡，焦慮地打開 Excel。他要花 40 分鐘手動合併來自 Email、Slack 和 CRM 的數據，只為了在 9:30 的週會上告訴老闆：「上週大概...還行吧？」。數據是冷的，而且永遠是過時的。

**現在的 Alex (使用 Archon)**：
週一早晨 8:50。Alex 悠閒地走進辦公室，打開 Archon。
**Bam！** 巨大的儀表板上，數字正在跳動。「本週新增潛在客戶：+15」、「轉換率：12%」。這是**即時**的戰情室。他沒做任何事，系統已經在週末自動完成了彙整。9:30 的會議上，他指著螢幕說：「我們現在——就在這一秒——領先目標 5%。」
**價值**：Archon 不只是工具，它是你的戰情室指揮官。

### 故事二：當你在睡覺，你的 AI 隊友在狩獵
*(Target: AI Agents & Specialized Tasks)*

**以前的 Sarah (業務開發)**：
Sarah 的一天有 4 個小時在做「苦工」：上網搜尋公司、複製貼上聯絡人、檢查這家公司是否還在徵人。她覺得自己像個機器人，真正的銷售技巧毫無用武之地。

**現在的 Sarah (使用 Archon)**：
下班前，Sarah 在 Archon 輸入一行指令：「幫我找出台北地區正在招募後端工程師的新創公司，並分析他們的技術部落格。」
然後她就去健身房了。
**深夜 2:00**，當 Sarah 熟睡時，Archon 的 AI Agent 正在網路上不知疲倦地爬梳、閱讀、過濾。
**隔天早上**，一份精美的 `Market Insights` 報告躺在她的收件匣裡。甚至連「切入點建議」都寫好了。Sarah 微笑著拿起電話，開始了她最擅長的談判。
**價值**：把機器人的工作還給 AI，讓人專注於只有人能做的事——建立連結。

### 故事三：消失的 Loading 轉圈圈
*(Target: Performance & State Sync)*

**以前的團隊**：
「欸，你有看到我剛剛改的專案狀態嗎？」
「沒欸，等一下，我按一下重新整理... 還在轉... 好了看到了。啊，可是我剛剛也改了同一個欄位，現在衝突了...」

**現在的團隊**：
工程師 Mark 在他的電腦上將任務拖曳到「已完成」。
**毫秒之間**，坐在對面的 PM 螢幕上的同一個卡片，像是有心電感應一般，滑順地滑進了「已完成」欄位。沒有 Loading，沒有重新整理，沒有衝突。
這不是魔法，這是 Archon 的**零時差協作**。團隊的思緒是同步的，因為系統是同步的。
**價值**：速度不只是快，更是流暢的團隊呼吸。

---

## 附錄 B：資料庫與認證同步指南 (Database & Auth Synchronization Guide)

### B.1 問題背景：為什麼 Admin 變成了 Member？
在開發過程中，我們遇到了「登入成功但權限錯誤 (406 Error)」的問題。這是因為 Supabase 的架構將使用者資料分成了兩部分：
1.  **身份認證 (`auth.users`)**: 由 Supabase Auth (GoTrue) 管理，存儲 Email、密碼雜湊與 **UUID**。
2.  **應用資料 (`public.profiles`)**: 由我們自己定義，存儲 `role`、`name` 等業務欄位。

**核心衝突**: 當我們手動執行 SQL Seed (`seed_mock_data.sql`) 時，我們硬塞了一個固定的 UUID 給 `admin`。但如果您在前端使用 "Sign Up" 註冊同名帳號，Supabase Auth 會生成一個**全新的、隨機的 UUID**。這導致 `auth.users` 的 ID 與 `public.profiles` 的 ID **不匹配 (Mismatch)**，系統因此找不到該使用者的 Profile，前端只好 Fallback 為預設的 Member 角色。

### B.2 解決方案：如何實現連動？

#### 方法一：手動修復 (Manual Fix) - 適用於已損壞的資料
使用 SQL 強制將 `profiles` 表的 ID 更新為 `auth.users` 的真實 ID：

```sql
-- 將 public.profiles 中的 admin ID 更新為 auth.users 中的真實 ID
UPDATE public.profiles
SET id = (SELECT id FROM auth.users WHERE email = 'admin@archon.com'),
    role = 'system_admin' -- 順便修正角色權限
WHERE email = 'admin@archon.com';
```

#### 方法二：自動連動 (PostgreSQL Trigger) - 最佳實踐 (Future Work)
為了避免未來發生此問題，建議建立一個 Database Trigger。當使用者註冊 (`auth.users` 新增資料) 時，自動在 `public.profiles` 建立對應資料。

```sql
-- 範例 Trigger (尚未實作於本專案)
create function public.handle_new_user()
returns trigger as $
begin
  insert into public.profiles (id, email, role, status)
  values (new.id, new.email, 'member', 'active'); -- 預設為 member
  return new;
end;
$ language plpgsql security definer;

create trigger on_auth_user_created
  after insert on auth.users
  for each row execute procedure public.handle_new_user();
```

### B.3 其他環境修正
*   **Auth Timeout**: 由於 Docker 環境的網路延遲，原本 `api.ts` 中的 2 秒逾時限制過於嚴苛，導致登入後隨即被踢出。已放寬至 **10 秒**。
