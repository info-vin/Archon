# Archon Nexus 戰情室：指標規格說明 (Nexus Metrics Spec)

> **版本**: 1.0.0
> **管理角色**: Charlie Howard (Manager) / David Howard (Admin)
> **目的**: 提供組織數位體質與業務效率的量化觀察口徑。

---

## 1. 核心指標定義 (The 9 Panels)

### 1.1 Integrity (GAP-027) - 系統完整度
*   **目標**: 衡量系統連通性與知識庫新鮮度。
*   **計算**: `(AI Latency Score 30% + RAG Match Count 70%)`。
*   **決策**: 若低於 80%，Admin 應啟動「Rebuild Index」。

### 1.2 Op Load (GAP-028) - 營運負載
*   **目標**: 觀察團隊任務堆積情況。
*   **數據**: 區分 `In Review` 與 `Doing` 狀態的任務總數。
*   **決策**: 峰值過高時，Charlie 應調整任務優先級。

### 1.3 Sent Risks (GAP-029) - 業務流失風險
*   **目標**: 異常偵測哨兵成果。
*   **數據**: 標記為 `ALERT` 且未轉換為 Task 的 Stale Leads。
*   **決策**: Charlie 應立即執行 `Dispatch Task`。

### 1.4 Resources (GAP-035) - 預算消耗
*   **目標**: AI 成本監控。
*   **數據**: `archon_token_usage` 的 30 天滾動總額 vs $100 USD 門檻。
*   **決策**: 超出預算時，Admin 應切換為更平價的模型（如 Flash Lite）。

### 1.5 Act Force (GAP-030) - 活躍武力
*   **目標**: 衡量人機協作的頻率。
*   **數據**: 7 天內有動作的 Agent 與人類帳號比例。

### 1.6 Ethics (GAP-031) - 倫理與合規
*   **目標**: 攔截不當請求的稽核。
*   **數據**: PII 洩漏預警與 Prompt 變更紀錄。

### 1.7 Collab (GAP-032) - 協作矩陣
*   **目標**: 9x9 實體關聯分析。
*   **數據**: Alice 轉 Bob、Charlie 轉 Alice 的任務流向。

### 1.8 Graph (GAP-033) - 情資 ROI
*   **目標**: 爬蟲轉換率。
*   **數據**: `(頁面存檔數 / 網域掃描數)`。

### 1.9 Velocity (GAP-034) - 生產速率
*   **目標**: 衡量組織從想法到執行的整體流轉效率。
*   **數據**: 聚合部落格產出、任務結案 (SLA) 與業務線索轉換的平均小時數。
*   **保護**: 實作 168 小時 (1 週) 上限門檻，防止極端離群值扭曲決策趨勢。

---

## 2. 管理權責區隔

*   **David (Admin)**: 負責維持 Integrity 與 Resources。
*   **Charlie (Manager)**: 負責優化 Op Load 與 Sent Risks。

> **備註**: 目前版本僅提供數據展示，自動修復功能為 Phase 5 項目。
