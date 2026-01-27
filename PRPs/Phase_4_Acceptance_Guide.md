# Archon Phase 4 產品驗收指南 (Product Acceptance Guide)

> **文件目的**: 本指南定義了 Archon Phase 4 的「完工定義 (DoS)」。旨在協助產品經理 (PM) 與利害關係人進行驗收，確保系統從「技術原型」成功轉型為「商業就緒解決方案」。
> **適用角色**: 產品經理 (PM)、QA 工程師、業務利害關係人

---

## 1. 核心功能驗收 (Core Feature Acceptance)

### 1.1 Sales Nexus (銷售情資與工作流)
**目標**: 業務代表 Alice 能搜尋潛在客戶、管理名單，並將其晉升為正式供應商。

| 功能 ID | 功能名稱 | 驗收標準 (Acceptance Criteria) | 驗收步驟 (Verification Steps) |
| :--- | :--- | :--- | :--- |
| **P4-SALES-01** | **潛客開發 (104 爬蟲)** | 1. 點擊 "Fetch 104 Data" 能獲取即時或模擬資料。<br>2. 資料欄位包含「職位」、「公司」、「原始連結」。<br>3. 來源標記 (Badge) 清楚區分 "104 Live" (綠色) 或 "Mock" (黃色)。 | 1. 以 **Alice** (`alice@archon.com`) 登入。<br>2. 進入 **Sales Nexus** 頁面。<br>3. 點擊 **Fetch 104 Data** 按鈕。<br>4. 確認表格出現新資料列。<br>5. 檢查來源標記顏色是否正確。 |
| **P4-SALES-02** | **銷售話術生成 (MarketBot)** | 1. 每筆名單皆有 "Generate Pitch" 按鈕。<br>2. 生成的 Email 內容能針對該職缺描述進行客製化。<br>3. 提供彈窗 (Modal) 讓業務在儲存前進行編輯。 | 1. 對任一潛客點擊 **⚡ Generate Pitch**。<br>2. 等待 **MarketBot** 生成內容。<br>3. 閱讀草稿，確認內容與職缺相關。<br>4. 點擊 **Approve & Save**。<br>5. 確認右上角出現成功通知 (Toast)。 |
| **P4-SALES-03** | **潛客晉升 (Lead Promotion)** | 1. 晉升後的潛客會存入資料庫的 `vendors` 表。<br>2. Librarian (知識管理員) 會自動將話術索引，供未來 RAG 檢索使用。 | 1. 檢查 DB `leads` 表 (或使用 `make probe` 指令)。<br>2. 確認 `job_title` 與 `description_snippet` 欄位已正確儲存。 |

### 1.2 Brand Hub (行銷內容與資產)
**目標**: 行銷專員 Bob 能管理品牌資產，並根據銷售洞察生成內容。

| 功能 ID | 功能名稱 | 驗收標準 (Acceptance Criteria) | 驗收步驟 (Verification Steps) |
| :--- | :--- | :--- | :--- |
| **P4-MKT-01** | **關鍵字資產管理** | 1. "Brand Hub" 頁面僅對行銷與管理角色開放。<br>2. 能看見從銷售端 (Leads) 匯總的 "Trending Keywords"。 | 1. 以 **Bob** (`bob@archon.com`) 登入。<br>2. 進入 **Brand Hub** 頁面。<br>3. 確認畫面顯示關鍵字列表。 |
| **P4-MKT-02** | **AI 內容初稿** | 1. "Draft with AI" 能生成部落格文章。<br>2. 若系統內有相關銷售線索，內容會自動引用 (Citations)。<br>3. 新增文章的預設狀態為 `DRAFT` (草稿)。 | 1. 點擊 **New Post** > **Draft with AI**。<br>2. 輸入主題： "AI for Manufacturing"。<br>3. 檢查生成的文章是否包含 "Manufacturing" 相關產業的案例引用。 |
| **P4-MKT-03** | **審核工作流** | 1. 點擊 "Submit for Review" 將狀態改為 `PENDING_APPROVAL`。<br>2. 送審後，文章應出現在經理 (Manager) 的戰情室中。 | 1. 點擊 **Submit for Review**。<br>2. 確認狀態標籤變為黃色。<br>3. 登出並切換為 Charlie 帳號，確認能看到該篇文章。 |

### 1.3 Team War Room (管理與營運)
**目標**: 經理 Charlie 能監控營運狀況、審核內容，並指派任務給 AI。

| 功能 ID | 功能名稱 | 驗收標準 (Acceptance Criteria) | 驗收步驟 (Verification Steps) |
| :--- | :--- | :--- | :--- |
| **P4-MGMT-01** | **部門權限隔離** | 1. 經理只能看到/管理自己部門的成員。<br>2. 經理無法修改系統管理員 (System Admin) 的權限。 | 1. 以 **Charlie** (`charlie@archon.com`) 登入。<br>2. 進入 **Team Management**。<br>3. 確認人員列表僅顯示 Sales/Marketing 成員。 |
| **P4-MGMT-02** | **內容審核** | 1. "Pending Approvals" 列表顯示 Bob 提交的文章。<br>2. "Approve" 動作將文章發布 (狀態變為 `published`)。<br>3. "Reject" 動作將文章退回草稿。 | 1. 在 **Pending Approvals** 找到 Bob 的文章。<br>2. 點擊 **Approve**。<br>3. 確認文章狀態變為 **Published**。 |
| **P4-MGMT-03** | **AI 任務指派** | 1. 能將任務指派給 **Machine Agents** (如 DevBot, POBot)。<br>2. "Refine" 按鈕能將簡短指令擴充為完整規格書。 | 1. 建立任務："修復首頁 Logo"。<br>2. 指派對象選擇：**DevBot**。<br>3. 點擊 **✨ Refine**。<br>4. 確認描述欄位自動擴充為詳細規格 (Gherkin 語法)。 |

---

## 2. 技術架構驗收 (Technical Architecture Acceptance)

此章節供技術 PM (TPM) 或架構師參考。

### 2.1 API 與文件一致性
| 項目 | 標準 | 驗證方法 |
| :--- | :--- | :--- |
| **API Contract** | `API_ARCHITECTURE.md` 必須與程式碼實作完全一致。 | 人工比對 / Diff 檢查 |
| **Frontend Integration** | `frontend-architecture.md` 準確反映組件與 API 的對應關係。 | 人工審閱前端 Service 層 |

### 2.2 系統穩定性 (The Sentinel)
| 項目 | 標準 | 驗證方法 |
| :--- | :--- | :--- |
| **健康探針 (Health Probe)** | `make probe` 指令回傳 "healthy" 狀態。 | 在終端機執行指令。 |
| **向量維度 (Vector Dimension)** | 系統能正確處理 768 (Gemini) vs 1536 (OpenAI) 維度差異。 | 執行 `make probe` (內建檢查邏輯)。 |
| **RAG 管道 (RAG Pipeline)** | Librarian 能在 5 分鐘內 (或觸發後立即) 索引新內容。 | 建立一筆 Lead 後，立即嘗試從 RAG 搜尋。 |

### 2.3 角色權限控制 (RBAC)
| Role | 允許行為 (Allowed) | 禁止行為 (Denied) | 必備 UI (Must See) |
| :--- | :--- | :--- | :--- |
| **Alice (Sales)** | 瀏覽 Sales Nexus, 生成話術, 管理個人任務 | 審核部落格文章, 管理團隊成員 | **Only** Sales Intel, Workspace |
| **Bob (Marketing)** | 瀏覽 Brand Hub, 撰寫草稿, 管理資產 | 存取敏感銷售名單, 管理使用者 | **Only** Brand Hub, Workspace |
| **Charlie (Manager)** | 審核內容, 管理團隊, 指派 AI 任務 | 系統配置 (Env Vars), 重置資料庫 | Sales Intel **AND** Brand Hub, Team Mgmt |
| **Admin (System)** | 所有權限 (含基礎設施配置) | 無 | All Menus |

---

## 3. 使用者體驗 (UX) 驗收

請 PM 重點關注以下細節：

1.  **視覺一致性**:
    *   [ ] 來源標記 (Source Badges) 在所有列表中樣式統一。
    *   [ ] 狀態標記 (Status Badges) 顏色符合語意 (草稿=灰 / 審核中=黃 / 已發布=綠)。
2.  **回饋迴圈 (Feedback Loops)**:
    *   [ ] 長時間運行的 AI 操作 (如生成話術) 必須顯示 Loading Spinner 或 Modal。
    *   [ ] 成功操作需觸發綠色 Toast 通知。
    *   [ ] 錯誤操作需觸發紅色 Toast 並提供可行動的錯誤訊息。
3.  **導航與權限**:
    *   [ ] 側邊欄應根據角色自動過濾項目 (例如 Alice 不應看到 "Team Management")。

---

## 4. 最終發布檢核 (Final Release Checklist)

- [ ] **E2E 測試**: 執行 `make test`，確保所有關鍵路徑通過。
- [ ] **黃金路徑測試**: 依照 Phase 4.4 文件手動走一遍完整流程 (Alice -> Bob -> Charlie)。
- [ ] **部署驗證**: 部署至 Staging 環境，並確認 `/api/health` 回傳 `ok`。
