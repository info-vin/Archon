# Phase 4.6.3 Charlie Persona: The Orchestrator (指揮官工作流)

> **Status**: Implemented (2026-02-05)
> **Role**: Manager / Admin
> **Motto**: "Management by Exception" (只處理例外，不陷入細節)
> **Goal**: 連結前線 (Alice) 與市場 (Bob)，確保組織依據數據行動。

---

## 1. 角色定位與團隊視角 (Role Definition)

Charlie 是 Archon 系統的神經中樞。他不生產原始數據，也不撰寫最終內容。他的工作是 **「決策 (Decide)」** 與 **「分派 (Dispatch)」**。

### 團隊如何看待 Charlie？

| 角色 | 視角 (Perspective) | 交互方式 (Interaction) |
| :--- | :--- | :--- |
| **Alice (前線)** | "Charlie 是我的後盾。他不會盯著我的每一步，但當我遇到搞不定的客戶，或者漏掉了重要商機，他會派發精準的任務 (Task) 給我。" | **被動接收**: Alice 透過 App 接收 Charlie 指派的高價值任務。 |
| **Bob (行銷)** | "Charlie 是我的總編輯。他確保我寫的文章符合公司戰略，並幫我擋下可能損害品牌形象的內容。" | **主動提交**: Bob 提交草稿，等待 Charlie 的批准 (Approval)。 |
| **AI Agents** | "Charlie 是最終裁決者。我們先過濾掉 80% 的雜訊，只把剩下 20% 需要人類智慧判斷的選項交給他。" | **輔助決策**: AI 準備好選項 (A/B)，Charlie 做選擇。 |

---

## 2. 核心 AI 助手矩陣 (The Agent Toolkit)

Charlie 的時間最昂貴，因此他只使用經過 **RBAC 權限過濾** 的高效率 Bot。我們不新增任何獨立的 Agent 實體，而是複用現有的後端服務。

| Agent 名稱 | 職責 (Role) | 核心能力 (Capability) | 如何節省 Charlie 工時 (Efficiency) |
| :--- | :--- | :--- | :--- |
| **🛡️ Sentinel (哨兵)** | **異常偵測**<br>(監控 `visit_logs` 與 `system_health`) | **不需主動查表**。只有當「Alice 業績掉 30%」或「API 紅燈」時才發通知。 |
| **🧠 Librarian (參謀)** | **戰略分析**<br>(跨表查詢 `logs` + `leads` + `blog`) | **不需手寫 SQL/報表**。Charlie 問：「本週競品趨勢為何？」，它直接給摘要。 |
| **⚖️ Reviewer (門神)** | **品質審核**<br>(檢查 `blog_posts` 的合規性) | **不需糾錯字/格式**。Bob 提交的草稿必須先通過它的 80 分門檻，才會出現在 Charlie 桌上。 |

---

## 3. 詳細工作流程 UML (Sequence Diagram)

### Workflow A: 戰略指派 (Insight to Action)
> **場景**: Alice 在前線忙碌，可能會漏掉某些長期沒經營的客戶。Charlie 負責補位。

```mermaid
sequenceDiagram
    autonumber
    actor Alice as 👩 Alice (Field)
    participant Cron as ⏰ 排程任務<br>(Cron Job)
    participant Sentinel as 🛡️ Sentinel<br>(HealthService)
    participant Librarian as 🧠 Librarian<br>(RAGService)
    participant UI as 🖥️ 經理儀表板<br>(Admin UI)
    actor Charlie as 👨 Charlie (Manager)
    participant API as ⚙️ Task API<br>(task_service)
    participant DB as 🗄️ 資料庫

    %% 1. 偵測與警示 (背景自動執行)
    Note over Alice, DB: 階段 1：異常偵測 (Anomaly Detection)
    Cron->>Sentinel: 每日掃描 (Daily Scan)
    Sentinel->>DB: SQL Query (Leads WHERE last_visit > 14 days)
    DB-->>Sentinel: 回傳 3 筆 "高價值流失風險"
    Sentinel->>DB: Insert Alert into `archon_logs`
    
    %% 2. 決策與分派 (人工介入)
    Note over Charlie, DB: 階段 2：決策與分派 (Decision & Dispatch)
    Charlie->>UI: 登入 Dashboard
    UI->>API: GET /api/admin/alerts
    API->>DB: SELECT * FROM archon_logs WHERE type='ALERT'
    DB-->>UI: 回傳警示列表
    
    Charlie->>UI: 點擊警示 "信義區 VIP 流失"
    UI->>Librarian: 請求 "生成任務建議" (GenAI)
    Librarian-->>UI: 回傳任務草稿：\n"拜訪信義區 VIP，攜帶新產品 DM"
    
    Charlie->>UI: 點擊 "Approve & Dispatch" (一鍵分派)
    UI->>API: POST /api/tasks (Assignee=Alice)
    API->>DB: INSERT INTO tasks
    
    %% 3. 閉環
    Note over Alice, DB: 階段 3：執行與閉環 (Execution)
    API->>Alice: 推送新任務通知 (Push Notification)
    Alice->>Alice: 執行任務 -> 回報 Log
    Sentinel->>DB: Update Alert Status (Resolved)
```

### Workflow B: 出版審核 (The Approval Gate)
> **場景**: Bob 寫了一篇新文章，需要 Charlie 批准才能上線。

```mermaid
sequenceDiagram
    autonumber
    actor Bob as 👤 Bob (Marketing)
    participant UI as 🖥️ 行銷工作臺
    participant API as ⚙️ Blog API<br>(marketing_api)
    participant Reviewer as ⚖️ Reviewer<br>(Gemini Service)
    participant DB as 🗄️ 資料庫
    actor Charlie as 👨 Charlie (Manager)
    participant Pub as 🌐 公開 Blog

    %% 1. 提交與預審 (機器把關)
    Note over Bob, DB: 階段 1：提交與預審 (Submission & Pre-check)
    Bob->>UI: 點擊 "Submit for Review"
    UI->>API: POST /api/blog/{id}/submit
    API->>Reviewer: 觸發合規檢查 (Check Compliance)
    Reviewer->>Reviewer: 檢查：敏感詞、過時數據、格式
    
    alt 分數 < 80 (低品質)
        Reviewer-->>API: Result: Reject
        API->>DB: Status = CHANGES_REQUESTED
        API-->>UI: 回傳 "退回原因：分數過低"
        UI->>Bob: 顯示 Toast: "請修正後再提交"
    else 分數 >= 80 (高品質)
        Reviewer-->>API: Result: Pass + Summary
        API->>DB: Status = PENDING_REVIEW
        API->>DB: Insert Review Note
    end

    %% 2. 快速決策 (人工裁決)
    Note over Charlie, Pub: 階段 2：人工裁決 (Human Decision)
    Charlie->>UI: 進入 "Approval Queue"
    UI->>API: GET /api/blog?status=PENDING_REVIEW
    API-->>UI: 回傳待審核列表 (含 AI 摘要)
    
    Charlie->>UI: 閱讀 AI 摘要 (30秒) -> 點擊 "Publish"
    UI->>API: PATCH /api/blog/{id}/publish (Check Role=Manager)
    API->>DB: Status = PUBLISHED
    API->>Pub: 更新公開頁面
    Pub-->>Bob: 通知 "文章已上線"
```

---

### Workflow C: 知識庫初始化 (Knowledge Initialization UI)
> **場景**: 系統初次部署或需要重置知識庫時，Charlie (Manager) 點擊儀表板按鈕觸發初始化，Admin 可透過 3737 Port 驗證結果。

```mermaid
sequenceDiagram
    autonumber
    actor Charlie as 👨 Charlie (Manager)
    participant UI as 🖥️ Manager Dashboard
    participant API as ⚙️ Manager API
    participant Librarian as 🧠 Librarian
    participant DB as 🗄️ Vector DB
    actor Admin as 👷 Admin

    Note over Charlie, DB: 階段 1：觸發初始化 (Trigger Seeding)
    Charlie->>UI: 點擊 "Rebuild Knowledge Base"
    UI->>API: POST /manager/knowledge/seed
    API->>Librarian: 掃描 docs/ 目錄
    
    loop 每一份文件
        Librarian->>DB: UPSERT into knowledge_base
    end

    Librarian-->>API: Success (Count)
    API-->>UI: 顯示 "Indexed X documents"
    
    Note over Admin, DB: 階段 2：驗證結果 (Verification)
    Admin->>DB: (Port 3737) SELECT count(*) FROM knowledge_base
    DB-->>Admin: 回傳筆數
```

---

## 4. 實作計畫 (Implementation Gap Analysis)

為了落地上述流程，Phase 4.6.3 需補足以下缺口：

| 模組 | 現狀 (As-Is) | 缺口 (Gap) | 實作行動 (Action Item) | 狀態 |
| :--- | :--- | :--- | :--- | :--- |
| **RBAC** | 角色有分，但 API 無強制擋權。 | Bob 可以直接 Publish，繞過 Charlie。 | **API Enforcer**: 在 `/approvals` 與 `/dispatch` 端點強制檢查 `user.role == 'manager'`。 | ✅ Done |
| **UI** | 只有個人的 Dashboard。 | Charlie 沒有綜觀全域的 **"Team Dashboard"**。 | **New View**: 實作 `ManagerDashboard.tsx`，包含 Alerts Feed, Sentinel Trigger。 | ✅ Done |
| **Agent** | 只有單一 Chat 介面。 | 缺乏 **"背景執行"** 的 Sentinel 與 Reviewer。 | **Sentinel Service**: 實作 `scheduler_service.py` 定期掃描 stale leads。 | ✅ Done |
| **Data** | Task 只能手動建立。 | 無法由 AI 自動生成 Task 草稿。 | **Smart Dispatch**: 在 `task_service.py` 整合 RAG + LLM (`gemini-1.5-pro`) 自動生成任務。 | ✅ Done |
| **SOP** | 需手動 SSH 進伺服器執行 CLI。| Charlie 不會用 Terminal，無法自行重置 RAG。 | **System Maintenance UI**: 在 Dashboard 新增 "Rebuild Knowledge Base" 按鈕與 API。 | ✅ Done |


---

## 5. 結論

Charlie 的存在不是為了增加管理成本，而是為了**結構化** Alice 與 Bob 的產出。
透過 **Sentinel (監控)**、**Librarian (建議)** 與 **Reviewer (把關)**，Charlie 能夠用最少的時間，維持系統最高的運作效率。

> **對於 Alice 而言**：Charlie 是一個「只在關鍵時刻出現，指引方向的指揮官」。
> **對於 Bob 而言**：Charlie 是一個「確保工作成果被認可與安全發布的守門員」。