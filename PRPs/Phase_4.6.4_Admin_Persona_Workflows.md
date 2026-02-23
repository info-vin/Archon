# Phase 4.6.4 Admin Persona: The Architect (系統架構師)

> **Status**: Implemented (2026-02-11)
> **Role**: System Admin / CTO / SRE
> **Motto**: "Stable Core, Evolving Soul" (穩固核心，進化靈魂)
> **Goal**: 確保系統的安全性、穩定性與自我進化能力，維護 Archon 的「數位體質」。

---

## 1. 角色定位與權限優勢 (Role Definition)

Admin 是 Archon 系統的創造者與守護者。他擁有上帝視角 (God Mode)，但不應介入日常業務細節（那是 Charlie 的工作）。他的核心職責是維護 **「基礎設施 (Infrastructure)」** 與 **「認知架構 (Cognitive Architecture)」**。

### 角色責任區分 (Admin vs Manager)

| 特徵 | 👨 Charlie (Manager / 琥珀色) | 🛠️ David (Admin / 玫瑰色) |
| :--- | :--- | :--- |
| **關注點** | **Business Health** (SLA、Velocity、轉換率) | **System Health** (API 延遲、模型存活、Token 成本) |
| **介入時機** | 業務流轉緩慢或內容品質不佳時 | 系統報錯、API Key 洩漏或 Agent 邏輯損壞時 |
| **權限邊界** | 僅限戰略決策區 (Amber Zone) | 擁有基礎設施區 (Rose Zone) 的物理控制權 |
| **核心工具** | Nexus Command, Approvals, Team | Admin Center, Identity Matrix, **Crawler Targets** |
| **色彩規範** | **Amber-500** (代表決策與分派) | **Rose-500** (代表安全與防禦) |

---

## 2. 核心 Agent 協作矩陣 (The Agent Collaboration)

Admin 的 Agent 團隊不是用來處理業務，是用來「修系統」的。

| Agent 名稱 | 職責 (Role) | 核心能力 (Capability) | 如何節省 Admin 工時 (Efficiency) |
| :--- | :--- | :--- | :--- |
| **Clockwork (巡邏員)** | **主動巡邏 (L5)**<br>(分析 `archon_logs`) | **不需手動查 Log**。每小時自動掃描錯誤，使用 `LLMProviderService` 分析 Traceback，區分是「偶發網路問題」還是「代碼邏輯錯誤」。 |
| **DevBot (工匠)** | **自癒執行 (L2)**<br>(生成 Hotfix) | **不需手寫修復代碼**。接收 Clockwork 的診斷，可透過 `ProposeChangeService` 建立 `proposed_changes` 紀錄 (Diff)。 |
| **Sentinel (哨兵)** | **安全監控**<br>(API Key & RBAC 審計) | **不需手動檢查設定**。定期檢查 API Key 額度，並監控 `auth.users` 異常權限變更。 |
| **Librarian (圖書館員)** | **知識管理**<br>(RAG Indexing) | **不需手動整理文件**。Admin 可透過 **"Rebuild Index"** 按鈕強制 Librarian 掃描所有文件並更新向量資料庫。 |

---

## 3. 詳細工作流程 UML (Day in the Life of Admin)

> **場景**: Admin 登入系統，首先確認系統健康度，處理權限變更要求，並監控 Token 成本。

```mermaid
sequenceDiagram
    autonumber
    actor Admin as 🛠️ Admin
    participant UI as 🖥️ Command Center<br>(ManagerDashboard)
    participant RBAC as 🔑 Identity Matrix<br>(IdentityMatrix.tsx)
    participant API as ⚙️ Admin API<br>(stats_api / auth_api)
    participant Sentinel as 🛡️ Sentinel
    participant DB as 🗄️ Database

    %% ==========================================
    %% 1. 系統健康巡檢 (System Health Check)
    %% ==========================================
    rect rgb(240, 248, 255)
    Note over Admin, DB: Phase 1: 系統健康巡檢 (Health Check)
    
    Admin->>UI: 登入 Command Center
    UI->>API: GET /api/stats/system-overview (Admin Only)
    
    par Health Checks
        API->>Sentinel: Check RAG Integrity (Vectors)
        Sentinel-->>API: Status: Healthy (Latency: 45ms)
        API->>DB: Count ERROR Logs (Last 24h)
        API->>DB: Sum Token Costs (Last 24h)
    end
    
    API-->>UI: 回傳健康報告 (RAG Green, Errors < 5, Cost $2.50)
    UI-->>Admin: 顯示 "System Healthy" 綠燈儀表板
    end

    %% ==========================================
    %% 2. 身份與權限管理 (RBAC Management)
    %% ==========================================
    rect rgb(255, 250, 240)
    Note over Admin, DB: Phase 2: 權限變更 (RBAC Ops)
    
    Admin->>RBAC: 開啟 "Identity Matrix" Tab
    RBAC->>API: GET /api/users
    API-->>RBAC: 回傳員工列表 + 當前角色
    
    Admin->>RBAC: 點擊 "New User" (e.g., 新進工程師)
    RBAC->>API: POST /api/admin/users/create
    API->>DB: INSERT INTO auth.users & public.profiles
    
    Admin->>RBAC: 編輯 User "Bob" -> 升級為 "System Admin"
    RBAC->>API: POST /api/admin/users/{id}/update
    
    API->>Sentinel: 記錄稽核日誌 (Audit Log)
    Sentinel->>DB: INSERT INTO archon_logs (Action="ROLE_CHANGE")
    API-->>RBAC: Success (Metadata Synced)
    end

    %% ==========================================
    %% 3. 系統配置與維護 (System Ops)
    %% ==========================================
    rect rgb(240, 255, 240)
    Note over Admin, DB: Phase 3: 配置與維護 (Configuration)
    
    Admin->>UI: 調整 "Scoring Logic" (提升 Funding 權重)
    UI->>UI: Update Weights (Client State)
    Admin->>UI: 點擊 "Save Config"
    UI->>API: POST /api/admin/config/scoring
    API->>DB: Save New Rules Metadata
    
    alt 需要重置知識庫
        Admin->>UI: 點擊 "Rebuild Index"
        UI->>API: POST /knowledge/seed
        API->>DB: Truncate & Re-embed
        API-->>UI: Toast "Index Rebuilt: 1240 docs"
    end
    end
```

---

## 4. 實作計畫 (Implementation Gap Analysis)

| 模組 | 現狀 (As-Is) | 缺口 (Gap) | 實作行動 (Action Item) | 狀態 |
| :--- | :--- | :--- | :--- | :--- |
| **System Health** | `system_api.py` 鎖定權限。 | 模型 ID 與邊界隔離。 | **Fix BUG-047/048**: 校正模型版本為 2.0，將 Probe 改為唯讀檢查。 | ✅ Done |
| **RBAC** | `IdentityMatrix.tsx` 支援細粒度覆寫。 | 已實作 `permission_overrides` 覆寫機制。 | **Permission Override**: 實作交互式權限矩陣，支援三態授權 (Inherit/Grant/Revoke)。 | ✅ Done |
| **Crawler Management** | `admin_api.py` 具備專屬端點。 | 物理隔離 URI 設定。 | **Feature 1.7**: 建立 `archon_crawler_targets` 表並實施 David 專屬管理。 | ✅ Done |
| **Trinity Workflow** | 規則與執行斷開。 | 實作 3737 -> 5173 -> 背景執行 閉環。 | **Ops-001**: 實作動態白名單注入、循環任務排程與 Clockwork 任務分派器。 | ✅ Done |
| **Token Ops** | `stats_api.py` 支援 Hybrid 統計。 | 補齊 `/ai-usage` 端點。 | **Fix 404**: 實作聚合成本計算邏輯並連接至 Nexus。 | ✅ Done |
| **Config** | `Scoring Logic` 已持久化。 | 評分規則已存入 `archon_settings` 資料庫。 | **Config Persistence**: 實作 Lead Scoring Weights 配置區塊，支援即時微調。 | ✅ Done |
| **Audit** | 前端具備搜尋與過濾介面。 | 已實作多維度即時過濾稽核紀錄。 | **Audit Log Viewer**: 在 `DocumentVersionsLog` 增加 Search UI 與 Sticky Header。 | ✅ Done |

---

## 5. 三位一體營運流 (The Trinity Operational Loop) - 2026-02-23 落地

今日已物理打通 David Howard 的核心自動化營運路徑：

1.  **認知定義 (3737)**：David 在 Admin UI 設定 `archon_crawler_targets` (包含網址、動態白名單、深度)。
2.  **行動指派 (5173)**：David 在 Project Task Modal 中將任務「連結」至上述目標，並勾選「加入排程 (Recurring)」。
3.  **自動執行 (Background)**：`Clockwork` 任務分派器每 30 分鐘自動掃描到期任務，指派 `Librarian` 執行爬取並更新 RAG 知識庫。

---

## 6. 實體操作範例：政府政策每日自動同步 (SOP)

**場景**：David 需要系統每日自動更新「勞動部工作生活平衡網」。

### **第一階段：3737 建立基礎 (Source Creation)**
1.  **入口**：`Admin UI (3737) > Knowledge Base > + Knowledge`。
2.  **動作**：輸入 `https://wlb.mol.gov.tw/Page/index.aspx`，設定 Type=`Business`，點擊 `Start Crawling`。
3.  **物理結果**：系統產生 `source_id` 並在 `archon_sources` 建立基礎索引。

### **第二階段：5173 定義營運規則 (Operational Setup)**
1.  **入口**：`User UI (5173) > Project > Create Task`。
2.  **指派**：選取 `Librarian Bot`。
3.  **David's Architect Tools** (玫瑰色區域)：
    *   **Associate Target**：下拉選單選取上述 WLB 來源。
    *   **Add to Periodic Schedule**：勾選並選取 `Daily`。
    *   **Dynamic Whitelist** (由後端推導)：David 在 3737 輸入的網域 `wlb.mol.gov.tw` 會自動被 `RBACService` 納入爬取許可。

### **第三階段：自動化循環 (Expertise Loop)**
*   `Clockwork` 每 30 分鐘執行掃描。
*   自動觸發 `Librarian` 穿透動態許可，執行 `crawl4ai` 抓取最新動態內容。
*   數據自動歸檔，維持 RAG 知識時效性。

---

## 7. 結論

Admin Persona (`Phase 4.6.4`) 的基礎架構已完成 **100%**：
1.  **可視化 (Visibility)**: 透過 **Command Center**，系統健康度、成本與稽核紀錄一目了然。
2.  **可控制 (Control)**: **Identity Matrix** 讓細粒度權限管理變得極致靈活。
3.  **持久化 (Persistence)**: 所有業務規則（如評分權重）均已資料庫化，確保系統具備真正的「數位體質」。