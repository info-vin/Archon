# Phase 5.6.4 - RBAC 與 Twin Scout 一致性審計與強化規格

本文件為 Archon 系統在 Phase 5.6.4 階段針對 **角色權限管理 (RBAC)** 與 **數位雙生巡檢 (Twin Scout)** 進行的一致性審計報告與未來強化規格。

---

## 1. 角色權限管理 (RBAC) 矩陣

### 1.1 規格邊界 vs. 代碼現實
在 `RBAC_Collaboration_Matrix.md` 中，定義了 L1 到 L3 的人類角色（`system_admin`, `manager`, `member`）與 L4 AI 代理人（`DevBot`, `MarketBot`, `Librarian`, `POBot`, `Clockwork`），並有詳細的團隊範疇與任務指派邏輯。

*   **動態角色權限映射（規格 vs. 現實）**：
    *   *規格*：資料庫資料表 `archon_roles_permissions` 動態控管角色權限。
    *   *現實*：[rbac_service.py](file:///Users/vincenta/GoogleKwok022/Archon/python/src/server/services/rbac_service.py) 已正確實作從資料庫 `archon_roles_permissions` 撈取動態權限的邏輯（並有快取機制防止資料庫連線過載）。
*   **指派範疇（規格 vs. 現實）**：
    *   *規格*：指派對象下拉選單需根據角色相容性動態過濾（例如：Alice/Sales 只能看到銷售相關的代理人，Charlie/Manager 則能看到所有人）。
    *   *現實*：[/assignable-users](file:///Users/vincenta/GoogleKwok022/Archon/python/src/server/api_routes/projects/core.py) API 路由確實會驗證角色限制。然而，`rbac_service.py` 存在**關鍵的一致性落差**：`has_permission_to_assign` 與 `get_assignable_roles` 仍然依賴建構子中寫死的靜態字典 `self.permissions`，繞過了資料庫的動態矩陣。
*   **部門範疇隔離（規格 vs. 現實）**：
    *   *規格*：使用者僅能檢視或管理自身所屬部門（Sales 或 Marketing）的專案與任務。
    *   *現實*：已實作於 `scope_projects` 與 `validate_project_access`，直接比對 JWT 中的 `department` 與項目的 `department` 欄位。此邏輯為集中式且靜態。
*   **MCP 工具權限裁剪（規格 vs. 現實）**：
    *   *規格*：AI 代理人應根據權限等級 (Level 1-7) 限制其工具呼叫能力。
    *   *現實*：實作於 `get_restricted_mcp_tools(...)`。對特定角色進行了物理裁剪（例如：禁止 Librarian 呼叫 `delete_project` 或 `execute_sql`）。

### 1.2 已知 RBAC 痛點
1.  **雙軌邏輯（靜態與動態衝突）**：由於 `has_permission_to_assign` 仍然使用 Python 程式碼中寫死的靜態字典，這意味著：若系統管理員在資料庫的 `archon_roles_permissions` 中動態更改了指派權限規則，**前端的任務指派選單並不會跟著動態更新**。
2.  **部門過濾彈性不足**：部門隔離機制是基於簡單的字串比對，目前不支援跨部門協作或矩陣式組織的專案權限宣告。

---

## 2. 數位雙生巡檢 (Twin Scout) 與模擬套件

### 2.1 規格邊界 vs. 代碼現實
數位雙生套件（`.agents/skills/twin-scout/SKILL.md`）定義了兩個執行維度：
1.  **雙生對帳 (Twin Scout - 稽核模式)**：在無狀態環境下（繞過 macOS 本地 Keychain 限制）模擬各個角色登入，擷取 UI 畫面，並由 Gemini 結合資料庫現狀進行一致性對帳。
2.  **雙生模擬 (Twin Simulator - 關卡模式)**：配置驅動的 YAML 關卡執行引擎，可在隔離沙盒中併發運行，並支援注入網路混沌。

*   **繞過 Keychain（規格 vs. 現實）**：
    *   *規格*：E2E 測試必須能在不依賴本地 Keychain 的 CI 容器環境下運作。
    *   *現實*：實作於 [cookie_injector.py](file:///Users/vincenta/GoogleKwok022/Archon/scripts/cookie_injector.py)，藉由物理注入 `storage_state.json` 到 Playwright 的 `BrowserContext` 來保持登入狀態。
*   **混沌攔截（規格 vs. 現實）**：
    *   *規格*：需具備隨機注入網路延遲與 HTTP 500 錯誤的能力。
    *   *現實*：實作於 [twin_scout.py](file:///Users/vincenta/GoogleKwok022/Archon/scripts/twin_scout.py)，利用 Playwright 的 `page.route("**/api/**")` 進行請求攔截。
*   **AI 視覺裁判（規格 vs. 現實）**：
    *   *規格*：擷圖與基準圖比對，當變更率 > 5% 時，交由 Gemini Vision 進行語意審查。
    *   *現實*：在 `twin_scout.py` 與 `vision_judge.py` 中皆已實作且運作中。

### 2.2 工作流規格對帳（手動 vs. AI 審批流）
In 人機協作生態中，Twin Scout 必須對以下核心工作流進行對帳：
1.  **手動專案管理流**：使用者手動點擊看板卡片、更新進度或填寫子任務。此部分由 `twin_scout.py` 的實體 DOM 操作（例如 `goto('/#/dashboard')`）結合資料庫變更驗證。
2.  **AI 任務分派與審批流 (AI Delegation & Approval)**：
    *   *規格*：Alice (Sales) 呼叫 `MarketBot` 生成開發信，寫入資料表 `leads`。
    *   *規格*：Charlie (Manager) 登入 `/approvals` 頁面，檢視 AI 提交的提案，執行「批准 (Approve)」或「退件 (Reject)」。
    *   *現實*：`twin_scout.py` 模擬了 Alice 查看行銷情資，以及在 E2E 測試中 mock 了對應的 API（如 `**/api/marketing/suggestions/*/reject`）。然而，目前 `audit` 模式並未真正將「Alice 寫入 -> Bob/Charlie 審批 -> 狀態從 Pending 轉為 Approved」的「跨角色接力變更」納入實體對帳，各角色目前仍是獨立、無關聯地執行單點頁面驗證。

### 2.3 已知 Twin Scout 痛點
1.  **DOM 選擇器的脆弱性 (Brittleness)**：網頁佈局調整時，`twin_scout.py` 內寫死的定位器（如 Bob 的定位器 `aside div.flex-1.overflow-y-auto > div`）容易失效，導致視覺比對報出偽陽性的對帳失敗。
2.  **Gemini 503 限流與測試延遲**：使用免費額度呼叫 Gemini 進行截圖分析時容易遇到 503 錯誤。`twin_scout.py` 被迫在切換角色時加入 `15 秒` 的硬編碼冷卻時間，這大幅降低了測試的執行效率。

---

## 3. 覆蓋率分析

### 3.1 後端測試覆蓋率
*   **API 測試**：[test_phase49_rbac.py](file:///Users/vincenta/GoogleKwok022/Archon/python/tests/integration/api/test_phase49_rbac.py) 使用 `TestClient` 模擬 `sales` 與 `system_admin` 身分，驗證 Alice 僅能撈取 MarketBot，而 Admin 可看見全部。
*   **服務測試**：[test_phase49_rbac_service.py](file:///Users/vincenta/GoogleKwok022/Archon/python/tests/integration/services/test_phase49_rbac_service.py) 針對 `AgentService` 的過濾規則進行了單元測試。
*   **覆蓋率狀態**：**優良**。後端的權限限制在 API 邊界上皆有對應的自動化測試覆蓋。

### 3.2 前端測試覆蓋率
*   **狀態機測試 (MBT)**：[TaskAssignment.mbt.spec.ts](file:///Users/vincenta/GoogleKwok022/Archon/enduser-ui-fe/tests/playwright/TaskAssignment.mbt.spec.ts) 模擬了在 Dashboard 建立任務、選擇 Librarian 代理人、配置爬蟲目標，並驗證了任務創建時的 API Payload 資料格式。
*   **覆蓋率狀態**：**中上**。任務指派精靈的 UI 狀態流轉均被驗證，而資料庫層面的實體同步則是透過 Twin Scout 腳本完成。

### 3.3 實體對帳覆蓋率
*   `twin_scout.py` 覆蓋了系統中五個核心角色（Alice, Bob, Charlie, Admin, DevBot）的頁面載入、實體資料庫指標與 UI 畫面的比對。
*   **覆蓋率狀態**：業務核心主流程覆蓋**完整**，但對介面改版的容忍度較為**脆弱**。

---

## 4. 實體對帳覆蓋率強化方案

為了解決 DOM 脆弱性、503 延遲以及工作流規格的缺失，建議以下列三點強化數位雙生對帳覆蓋率：

### 4.1 實作「跨角色接力工作流對帳 (Sequential Multi-Persona Journey)」
*   **方案**：將獨立的角色檢查改為一個連續的接力場景：
    1.  **Alice (Sales)** 登入：呼叫爬蟲獲取一份新 Leads，並提交一封 AI 生成的開發信草稿（此時 Leads 狀態為 `Pending`）。
    2.  **Charlie (Manager)** 登入：前往 `/approvals`，核對並批准 Alice 剛才提交的開發信草稿（此時狀態轉為 `Approved`）。
    3.  **Bob (Marketing)** 登入：確認 Leads 被批准，並呼叫 `Librarian` 進行 RAG 查詢與部落格撰寫。
    4.  **對帳判定**：Twin Scout 需全程檢索資料庫的生命週期狀態轉移，確保前端與資料庫狀態 100% 物理一致。

### 4.2 引入「資料-視覺雙軌裁判 (Dual-Judge System)」
*   **方案**：為降低對 Gemini Vision 的呼叫頻率與 DOM 改版脆性：
    *   **資料級斷言 (Data-Level Invariants)**：前端頁面加上標準的 `data-testid`（例如 `data-testid="leads-count"`）。Twin Scout 優先使用 Playwright 擷取該文字內容，與資料庫進行硬編碼斷言。如果資料不一致，直接判定 Failed，完全不需要呼叫 LLM 視覺裁判。
    *   **語意與佈局裁判 (Layout Visual-Judge)**：只有在「版面整體美觀審查、文字是否交疊、頭像顏色是否隨權限正確變色」等無法透過純文字驗證的 UI 項目上，才擷圖並呼叫 Gemini Vision 裁判。這能將 Gemini 的呼叫頻率降低 80%，根除 503 Rate Limits。

### 4.3 健全混沌測試覆蓋率
*   **方案**：在 CI/CD 中強制啟用 `make twin-simulator`，模擬高延遲（3秒阻滯）與 HTTP 500。
*   **對帳指標**：檢測 Playwright 執行時是否會在頁面捕獲到 React 的 `Uncaught TypeError` 崩潰，並驗證 UI 是否成功顯示非阻塞的「neon警告指示燈 (Budget Warning/Error Badges)」。

---

## 5. Lean 4 形式化驗證規格

為了保證上述三個強化戰線的邏輯正確與狀態轉移安全性，我們將在 `lean_proofs/LeanProofs/` 下建立定理模型，其形式化數學規格定義如下：

### 5.1 戰線一：RBAC 動態與靜態單一事實來源等價性定理
若資料庫（動態）權限與程式碼（靜態）配置一致，則判定邏輯必須是等價的。
```lean
-- 定義指派判定函數的等價性
theorem assign_parity 
  (user : User) 
  (assignee : Agent) 
  (matrix : RBACMatrix) 
  (h_sync : sync_state matrix = true) :
  has_permission_assign_dynamic user assignee matrix = true ↔ 
  has_permission_assign_static user assignee = true
```

### 5.2 戰線二：跨角色工作流狀態機轉換安全定理
在跨角色接力工作流中，狀態轉移必須嚴格遵循業務合約，任何操作不能跳過主管 Charlie 的審查步驟。
```lean
-- 證明不經過 Approve 動作，狀態無法從 pending 躍遷至 approved 或是 published
theorem workflow_safety 
  (s1 s2 : WorkflowState) 
  (act : WorkflowAction) 
  (h_start : s1 = WorkflowState.pending_approval)
  (h_step : step s1 act = s2)
  (h_not_approve : act ≠ WorkflowAction.approve) :
  s2 ≠ WorkflowState.approved ∧ s2 ≠ WorkflowState.published
```

### 5.3 戰線三：雙軌裁判短路求值正確性定理
若資料級別的硬斷言（Data Invariants）判定失敗，則整體雙軌裁判必失敗（保證短路求值不會因為視覺噪訊或 LLM 錯誤而給出偽陰性結果）。
```lean
-- 證明資料檢測失敗時，整體裁判定為失敗
theorem dual_judge_short_circuit
  (x : UISnapshot)
  (h_data : data_check x = false) :
  dual_judge x = false
```

### 5.4 戰線四：多 Agent 星環討論拓樸安全性與終止性定理
為了防範多 Agent 在星環群聊 (Star-Topology) 討論中陷入無限的訊息循環 (Infinite Loop) 並確保拓樸合法性：

*   **拓樸安全性 (Topology Safety)**：證明任意訊息路由必定以 `Supervisor` 為中繼中心。任意兩個功能型 Agent 之間禁止繞過 Supervisor 直接通訊。
```lean
-- 若發言者與接收者都不是 Supervisor，則該訊息流非法
theorem star_flow_safety 
  (msg : Message) 
  (h_not_su_sender : msg.sender ≠ AgentNode.supervisor) 
  (h_not_su_recv : msg.receiver ≠ AgentNode.supervisor) :
  ¬ (is_valid_star_flow msg)
```

*   **終止性證明 (Termination via Budget)**：基於遞減的步驟預算 (Chat Budget)，證明整個多 Agent 討論在預算耗盡時必定會收斂終止。
```lean
-- 證明當步數預算為 0 時，討論狀態機被迫終止且不再接受任何新訊息
theorem star_chat_termination 
  (s : ChatState) 
  (h_budget : s.budget = 0) :
  chat_step s = ChatState.terminated
```

---

## 6. 定理之自動化驗證機制 (Automated Verification Pipeline)

為確保 Lean 形式化定理與實體代碼不脫節，將這套形式化驗證整合至既有的品質門禁網關中：

### 6.1 整合終極品質網關 (`make audit-qa` / `make test-be` / `make lint`)
*   **定理自動化編譯**：將 `make test-lean` 的 Lake 編譯過程正式納入 `make audit-qa` 與 `make lint` 中。任何 Lean 定理的證明編譯失敗，都將會直接導致 Linter 網關返回非零代碼。
*   **雙向物理對帳自動執行**：形式化對帳測試檔案 `python/tests/integration/test_lean_model_alignment.py` 作為整合測試，將會自動被 `make test-be` 與 `make audit-qa` 掃描並物理執行。

### 6.2 雙向物理對帳測試 (Parity Python Test) 運作原理
*   **機制**：`test_lean_model_alignment.py` 測試會動態撈取後端實際資料庫權限與 Python 狀態機代碼。
*   **比對**：與 `AuditParity.lean` 中的 `WorkflowState` 與 `AgentNode` 定理前提假設進行邊界比對。一旦代碼中的狀態改變而 Lean 定理模型未同步更新，Pytest 將直接失敗阻斷，保證形式化與實體代碼的「一致性自癒」。
