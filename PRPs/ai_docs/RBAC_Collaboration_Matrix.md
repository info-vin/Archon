# Archon Human-Machine RBAC Matrix

**Audience**: Archon Developers, System Admins, AI Agents
**Purpose**: Define the Role-Based Access Control (RBAC) matrix for Human-AI collaboration ecosystem
**Source**: Derived from `frontend-architecture.md`, `PRPs/Phase_5_RBAC_Infrastructure_and_Identity`
**Last Updated**: 2026-01-13

---

## 1. CORE PHILOSOPHY (核心理念)

Archon 是一個「使用者角色的人機協作平台」。在此生態系中，**Admin** 是系統造物主；**Alice/Bob/Charlie** 是業務執行者；而 **Agents** 是具備特定技能的虛擬員工。系統支援「手動專案管理」與「AI 自動化任務」並行運作。

---

## 2. HUMAN ROLE SPECIFICATIONS (人類角色規格)

參考專案 Blog Case 與 Phase 5 實作，定義以下具體角色與 DB 欄位映射：

| 層級 | DB Role 欄位 | 判斷依據 (Role + Dept) | 代表人物 (Persona) | 具體職責 (Responsibilities) |
| :--- | :--- | :--- | :--- | :--- |
| **L1** | `system_admin` | N/A | **Admin** (You) | **系統造物主**。<br>1. 基礎設施維護 (Docker, DB)。<br>2. 實體化 Alice/Bob 等帳號。<br>3. 配置 Agent 工具箱 (MCP)。 |
| **L2** | `manager` | N/A | **Charlie** (Dev Lead) | **團隊管理者**。<br>1. 審核 AI 寫入的程式碼 (Approvals)。<br>2. 查看團隊 HR 儀表板。<br>3. 分配專案資源。 |
| **L3** | `member` | Dept: **Sales** | **Alice** (Sales Rep) | **業務代表**。<br>1. 記錄客戶聯繫進度 (手動)。<br>2. 呼叫 `Marketing Agent` 搜尋潛在客戶。<br>3. 檢視行銷情資列表。 |
| **L3** | `member` | Dept: **Marketing**| **Bob** (Content Lead)| **行銷人員**。<br>1. 撰寫部落格草稿 (手動)。<br>2. 呼叫 `Knowledge Agent` 歸檔文章。<br>3. 分析市場趨勢。 |

---

## 3. AGENT ROLE SPECIFICATIONS (AI 角色規格)

為了開發明確性，Agent 不再是模糊的概念，而是具備特定 `Tools` 與 `System Prompt` 的實體。

| Agent 代號 | 類型 | 對應技能/工具 (MCP Tools) | 開發定義 |
| :--- | :--- | :--- | :--- |
| **`DevBot`** | L4-U | **Developer Agent**<br>- `read_file`, `write_file`<br>- `git_commit`, `run_test` | **協作開發者**。負責修復 Bug、重構代碼。產出需經 Charlie 審核。 |
| **`MarketBot`**| L4-U | **Marketing/Sales Agent**<br>- `search_job_market` (104 API)<br>- `fetch_web_content` | **業務助理**。負責搜尋職缺、分析潛在客戶需求。產出存入 `leads` 表。 |
| **`Librarian`**| L4-U | **Knowledge Agent**<br>- `archive_to_vector_db`<br>- `semantic_search` | **知識管理員**。負責將部落格/文件向量化，或回答 RAG 問題。 |
| **`Clockwork`**| L4-S | **System Agent**<br>- `cleanup_logs`<br>- `check_health` | **系統維運**。由 Cron Job 定期觸發，無須人類介入。 |

---

## 4. HYBRID WORKFLOW (混合工作流：手動 vs AI)

系統區分「日常專案管理」與「AI 任務指派」，兩者在同一介面並行。

### 4.1 Manual Project Management (手動專案管理)
這是 Alice/Bob 80% 的日常工作，**不涉及 Agent**。
- **介面**: `Kanban Board` (看板) & `TaskModal` (任務詳情)。
- **場景**:
    - Alice 打電話給客戶 B -> 在任務卡片新增 Comment：「對方未接」。
    - Bob 完成初稿 -> 勾選 Subtask：「草稿撰寫完成」。
    - Charlie 更改會議時間 -> 修改任務 Due Date。
- **資料流**: User Input -> API -> Database -> UI Update。

### 4.2 AI Task Delegation (AI 任務指派)
這是 Alice/Bob 遇到重複性或需大量資料處理的工作時，主動**召喚 Agent**。
- **介面**: `TaskModal` 中的 "Assign to AI" 按鈕或 Chat 介面。
- **場景**:
    - Alice 需要 50 家潛在客戶名單 -> 指派 `MarketBot` 執行搜尋。
    - Charlie 需要修復一個 UI Bug -> 指派 `DevBot` 讀取代碼並提解法。
- **資料流**: User Input -> Agent Service -> MCP Tools -> **Approval (If needed)** -> Database/Codebase。

---

## 5. PERMISSION MATRIX (RBAC 權限矩陣)

### Legend
- 🔴 **無權限**: UI 隱藏 / API 403。
- 🟢 **個人權限**: 僅限操作自己的資料。
- 🔵 **團隊權限**: 可操作團隊資料。
- 🟣 **全域強制**: Admin 最高權限 (可無視擁有者規則)。

| 功能模組 | 資源/動作 | SYSTEM_ADMIN (You) | MANAGER (Charlie) | SALES (Alice) | MKT (Bob) |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **手動管理** | **更新任務進度/留言** | 🟣 任意任務 | 🔵 團隊任務 | 🟢 指派給我的 | 🟢 指派給我的 |
| | **編輯/刪除 Blog** | 🟣 **全域強制 (Blog Override)** | 🔵 團隊文章 | 🟢 僅限本人 | 🟢 僅限本人 |
| **AI 協作** | **指派 DevBot** | ✅ 允許 | ✅ 允許 | 🔴 禁止 (不懂Code) | 🔴 禁止 |
| | **指派 MarketBot** | ✅ 允許 | ✅ 允許 | ✅ 允許 | ✅ 允許 |
| | **批准代碼變更** | ✅ 允許 | ✅ 允許 | 🔴 禁止 | 🔴 禁止 |
| **資料檢視** | **HR 儀表板** | ✅ 全局 | 🔵 團隊 | 🟢 個人 | 🟢 個人 |
| | **Leads 列表** | ✅ 全局 | ✅ 全局 | 🟢 個人負責 | ✅ 全局分析 |
| **系統** | **MCP 配置** | ✅ 管理 | 🔴 不可見 | 🔴 不可見 | 🔴 不可見 |

---

## 6. DATA & UI LOCATIONS (資料與介面位置)

| 資料類型 | 產生者 | 儲存位置 | UI 呈現位置 |
| :--- | :--- | :--- | :--- |
| **專案進度** | **Human (手動)** | `archon_tasks` (SQL) | 看板 (Kanban), 甘特圖 (Gantt) |
| **行銷情資** | **MarketBot** | `leads` (SQL) | `/marketing` 列表頁 |
| **市場洞察** | **MarketBot** | `knowledge_items` (Vector) | `/knowledge` 或 RAG Chat |
| **程式碼變更**| **DevBot** | `proposed_changes` (SQL) | `/approvals` 審核頁 & 任務卡片 |
| **系統日誌** | **Clockwork** | `system_logs` (SQL/File) | Admin Dashboard (Port 3737) |

---

## 7. TECHNICAL IMPLEMENTATION GUIDELINES (技術實作指引)

為確保 RBAC 策略與系統架構一致，請遵循以下實作標準：

### 7.1 UI Rendering Strategy (UI 渲染策略)
*Ref: `UI_STANDARDS.md`*
- **無權限 (🔴)**: 採用 **Render Nothing** (不渲染)。不要使用 `disabled` 屬性，直接不輸出 DOM 元素。這能降低認知負擔並提升安全性。
- **Hook 範例**:
  ```tsx
  if (!user.hasPermission('approve_code')) return null;
  return <Button>Approve</Button>;
  ```

### 7.2 Data Fetching & Scoping (資料獲取與範疇)
*Ref: `QUERY_PATTERNS.md`*
- **團隊視角 (🔵)**: 使用標準 List Query Key。
  - `queryKey: taskKeys.byProject(projectId)`
- **個人視角 (🟢)**: 必須在 API 層級強制過濾。
  - 前端: `queryKey: taskKeys.assignedTo(userId)`
  - 後端: API 必須驗證 `request.user.id` 與查詢參數一致，否則拒絕。

### 7.3 Optimistic Updates & Error Handling (樂觀更新與錯誤處理)
*Ref: `optimistic_updates.md`*
- **403 Forbidden**: 當使用者試圖執行無權限操作 (如透過 API 工具)，後端回傳 403。
- **Rollback**: 前端 Mutation 的 `onError` 必須捕捉 403 錯誤，觸發 UI 回滾 (Rollback)，並顯示明確的 Toast 錯誤訊息：「權限不足」。

### 7.4 API Endpoint Mapping (API 端點映射)
*Ref: `API_NAMING_CONVENTIONS.md`*
- **指派 Agent**: `POST /api/tasks/{id}/assign_agent`
- **批准變更**: `POST /api/approvals/{id}/execute`
- **HR 數據**: `GET /api/stats/member-performance` (後端需根據 Role 過濾回傳資料)