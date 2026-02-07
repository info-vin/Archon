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

## 3. 詳細工作流程 UML (Day in the Life of Charlie)

> **場景**: Charlie 的一天從「全局監控」開始，接著「處理例外」，最後進行「系統維護」。

```mermaid
sequenceDiagram
    autonumber
    actor Alice as 👩 Alice (Field)
    actor Bob as 👤 Bob (Marketing)
    actor Charlie as 👨 Charlie (Manager)
    participant UI as 🖥️ Operations Nexus<br>(Command Center)
    participant API as ⚙️ Manager API
    participant Sentinel as 🛡️ Sentinel<br>(Background Service)
    participant Librarian as 🧠 Librarian<br>(RAG Service)
    participant Reviewer as ⚖️ Reviewer<br>(Gemini Service)
    participant DB as 🗄️ 資料庫

    %% ==========================================
    %% 晨間例行 (Morning Routine): 異常偵測與分派
    %% ==========================================
    rect rgb(240, 248, 255)
    Note over Alice, DB: ☀️ Phase 1: 晨間偵測與分派 (Detection & Dispatch)
    
    %% 背景掃描
    Sentinel->>DB: ⏰ CRON: 掃描滯留客戶 (>14天)
    DB-->>Sentinel: 發現 "信義區 VIP 流失風險"
    Sentinel->>DB: 寫入 Alert Log
    
    %% 經理介入
    Charlie->>UI: 登入 Command Center (查看 Alerts)
    UI->>API: GET /api/marketing/manager/alerts (Priority=High)
    API-->>UI: 顯示警示紅燈 🔴
    
    Charlie->>UI: 點擊 "Dispatch Task"
    UI->>Librarian: 請求 "生成任務建議" (Contextual AI)
    Librarian-->>UI: 建議："攜帶新產品 DM 拜訪"
    
    Charlie->>UI: 確認分派 (Approve & Dispatch)
    UI->>API: POST /api/marketing/manager/alerts/{id}/dispatch
    API->>DB: 建立 Alice 的任務
    API->>Alice: 📱 推送通知："收到新指派任務"
    end
    
    %% ==========================================
    %% 下午例行 (Afternoon Routine): 內容把關
    %% ==========================================
    rect rgb(255, 250, 240)
    Note over Alice, DB: 🌤️ Phase 2: 出版品審核 (Content Approval)
    
    Bob->>UI: 提交新文章草稿
    UI->>API: POST /api/marketing/blog/{id}/submit
    API->>Reviewer: 自動合規檢查 (Auto-Check)
    
    alt 分數 < 80
        Reviewer-->>Bob: ❌ 退回：含敏感關鍵字
    else 分數 >= 80
        Reviewer->>DB: 標記為 "Pending Approval"
        Charlie->>UI: 查看 "Approvals Queue"
        UI-->>Charlie: 顯示待審核列表 + AI 摘要
        Charlie->>UI: 點擊 "Publish" (一鍵發布)
        UI->>API: POST /api/marketing/approvals/blog/{id}/approve
        UI->>DB: 更新狀態 = PUBLISHED
        DB-->>Bob: ✅ 通知："文章已上線"
    end
    end

    %% ==========================================
    %% 系統維護 (System Ops): 知識庫重置
    %% ==========================================
    rect rgb(240, 255, 240)
    Note over Alice, DB: 🛠️ Phase 3: 系統維護 (Knowledge Ops)
    
    Charlie->>UI: 發現 RAG 回答過時 -> 點擊 "Rebuild Index"
    UI->>API: POST /api/marketing/manager/knowledge/seed
    API->>Librarian: 觸發全面重建 (Full Re-index)
    loop 掃描文件
        Librarian->>DB: UPSERT 向量資料
    end
    Librarian-->>UI: ✅ 完成：更新 152 份文件
    
    %% 驗證
    Charlie->>DB: (Port 3737) 驗證筆數 (Optional)
    end
```

### 3.1 閉環工作流設計理念 (Closed-Loop Workflow Philosophy)

這張 UML 展示了 Archon 的核心設計哲學——**閉環 (Closed-Loop)**，確保從信號到行動的每一步都有反饋：

1.  **偵測 (Detect)**: 系統主動發現問題 (Sentinel)。
2.  **決策 (Decide)**: 人類管理者 (Charlie) 做高價值判斷，而非淹沒在雜訊中。
3.  **執行 (Action)**: AI 將決策轉化為前線 (Alice) 或系統 (Librarian) 的具體行動。
4.  **反饋 (Feedback)**: 執行結果回寫資料庫 (Alert Resolved / Blog Published)，修正下一次的偵測模型。

---

## 4. 實作計畫 (Implementation Gap Analysis)

為了落地上述流程，Phase 4.6.3 需補足以下缺口：

| 模組 | 現狀 (As-Is) | 缺口 (Gap) | 實作行動 (Action Item) | 狀態 |
| :--- | :--- | :--- | :--- | :--- |
| **RBAC** | 角色有分，但 API 無強制擋權。 | Bob 可以直接 Publish，繞過 Charlie。 | **API Enforcer**: 在 `/approvals` 與 `/dispatch` 端點強制檢查權限。 | ✅ Done |
| **UI** | 只有個人的 Dashboard。 | Charlie 沒有綜觀全域的 **"Team Dashboard"**。 | **New View**: 實作 `ManagerDashboard.tsx`，包含 Alerts Feed, Sentinel Trigger。 | ✅ Done |
| **Agent** | 只有單一 Chat 介面。 | 缺乏 **"背景執行"** 的 Sentinel 與 Reviewer。 | **Sentinel Service**: 實作 `scheduler_service.py` 定期掃描 stale leads。 | ✅ Done |
| **Data** | Task 只能手動建立。 | 無法由 AI 自動生成 Task 草稿。 | **Smart Dispatch**: 在 `task_service.py` 整合 RAG + LLM 自動生成任務。 | ✅ Done |
| **Ops** | 需手動 SSH 進伺服器重置 DB。| 缺乏 GUI 維護工具。 | **Knowledge UI**: 新增 "Rebuild Knowledge Base" 按鈕與 API。 | ✅ Done |
| **Config** | 規則寫死在 Code 中。 | 無法動態調整 Sentinel 的權重。 | **Scoring Rules Grid**: 實作 `ManagerDashboard` 的動態規則編輯表格。 | ✅ Done |
| **Ops Nexus** | 分散的頁面 (Logs, Users)。 | 缺乏統一的戰情中心。 | **Operations Nexus**: 整合 Alerts, Approvals, Health 於單一儀表板 (`ApprovalsPage.tsx`)。 | ✅ Done |

---

## 5. 結論

Charlie 的存在不是為了增加管理成本，而是為了**結構化** Alice 與 Bob 的產出。
透過 **Sentinel (監控)**、**Librarian (建議)** 與 **Reviewer (把關)**，Charlie 能夠用最少的時間，維持系統最高的運作效率。

> **對於 Alice 而言**：Charlie 是一個「只在關鍵時刻出現，指引方向的指揮官」。
> **對於 Bob 而言**：Charlie 是一個「確保工作成果被認可與安全發布的守門員」。