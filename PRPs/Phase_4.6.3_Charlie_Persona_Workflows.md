# Phase 4.6.3 Charlie Persona: The Orchestrator (指揮官工作流)

> **Status**: Draft
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

Charlie 的時間最昂貴，因此他只使用經過 **RBAC 權限過濾** 的高效率 Bot。

| Agent 名稱 | 職責 (Role) | 核心能力 (Capability) | 如何節省 Charlie 工時 (Efficiency) |
| :--- | :--- | :--- | :--- |
| **🛡️ Sentinel (哨兵)** | **異常偵測** | 監控 `visit_logs` 與 `system_health`。 | **不需主動查表**。只有當「Alice 業績掉 30%」或「API 紅燈」時才發通知。 |
| **🧠 Librarian (參謀)** | **戰略分析** | 跨表查詢 (`logs` + `leads` + `blog`)。 | **不需手寫 SQL/報表**。Charlie 問：「本週競品趨勢為何？」，它直接給摘要。 |
| **⚖️ Reviewer (門神)** | **品質審核** | 檢查 `blog_posts` 的合規性。 | **不需糾錯字/格式**。Bob 提交的草稿必須先通過它的 80 分門檻，才會出現在 Charlie 桌上。 |

---

## 3. 核心工作流程 (Core Workflows)

### Workflow A: 戰略指派 (Insight to Action)
> **場景**: Alice 在前線忙碌，可能會漏掉某些長期沒經營的客戶。Charlie 負責補位。

```mermaid
sequenceDiagram
    participant Alice as Alice (Field)
    participant Sentinel as 🛡️ Sentinel
    participant Librarian as 🧠 Librarian
    participant Charlie as Charlie (Manager)
    participant UI as Admin UI

    %% 1. 偵測與警示
    Note over Alice, Sentinel: 背景：Alice 連續 14 天未拜訪 "信義區 VIP"
    Sentinel->>Sentinel: Daily Scan (Cron Job)
    Sentinel->>UI: 推送 "Alert: High Value Risk"

    %% 2. 決策與分派
    Charlie->>UI: 查看 Alert 詳細資訊
    UI->>Librarian: 請求 "生成任務建議 (Draft Task)"
    Librarian-->>UI: 回傳任務草稿：\n"拜訪信義區 VIP，攜帶新產品 DM"
    
    Charlie->>UI: 點擊 "Approve & Dispatch" (一鍵分派)
    UI->>Alice: 推送新任務通知 (Push Notification) 
    
    %% 3. 閉環
    Alice->>Alice: 執行任務 -> 回報 Log
    Sentinel-->>Charlie: 解除 Alert 狀態
```

### Workflow B: 出版審核 (The Approval Gate)
> **場景**: Bob 寫了一篇新文章，需要 Charlie 批准才能上線。

```mermaid
sequenceDiagram
    participant Bob as Bob (Marketing)
    participant Reviewer as ⚖️ Reviewer
    participant Charlie as Charlie (Manager)
    participant Blog as Public Blog

    %% 1. 提交與預審
    Bob->>Reviewer: 提交草稿 (Submit)
    Reviewer->>Reviewer: 檢查：敏感詞、過時數據、格式
    
    alt 分數 < 80 (低品質)
        Reviewer-->>Bob: 自動退回 (Auto-Reject) + 修改建議
    else 分數 >= 80 (高品質)
        Reviewer->>Charlie: 放入 "待審核佇列 (Approval Queue)"
        Reviewer-->>Charlie: 附上 "審核摘要 (AI Summary)"
    end

    %% 2. 快速決策
    Charlie->>Charlie: 閱讀 AI 摘要 (30秒)
    Charlie->>Blog: 點擊 "Publish" (發布)
    Blog-->>Bob: 通知 "文章已上線"
```

---

## 4. 實作計畫 (Implementation Gap Analysis)

為了落地上述流程，Phase 4.6.3 需補足以下缺口：

| 模組 | 現狀 (As-Is) | 缺口 (Gap) | 實作行動 (Action Item) |
| :--- | :--- | :--- | :--- |
| **RBAC** | 角色有分，但 API 無強制擋權。 | Bob 可以直接 Publish，繞過 Charlie。 | **API Enforcer**: 在 `/publish` 端點強制檢查 `user.role == 'manager'`。 |
| **UI** | 只有個人的 Dashboard。 | Charlie 沒有綜觀全域的 **"Team Dashboard"**。 | **New View**: 實作 `ManagerDashboard.tsx`，包含 `Alerts` 與 `Approval Queue` 區塊。 |
| **Agent** | 只有單一 Chat 介面。 | 缺乏 **"背景執行"** 的 Sentinel 與 Reviewer。 | **Cron Jobs**: 實作後端排程任務，定期掃描並寫入 `archon_logs` 作為 Alerts。 |
| **Data** | Task 只能手動建立。 | 無法由 AI 自動生成 Task 草稿。 | **Smart Task**: 在 `task_service.py` 新增 `generate_task_from_insight()` 方法。 |

---

## 5. 結論

Charlie 的存在不是為了增加管理成本，而是為了**結構化** Alice 與 Bob 的產出。
透過 **Sentinel (監控)**、**Librarian (建議)** 與 **Reviewer (把關)**，Charlie 能夠用最少的時間，維持系統最高的運作效率。

> **對於 Alice 而言**：Charlie 是一個「只在關鍵時刻出現，指引方向的指揮官」。
> **對於 Bob 而言**：Charlie 是一個「確保工作成果被認可與安全發布的守門員」。

