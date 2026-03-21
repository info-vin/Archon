# Phase 4.6.8: Digital Twin 深度應用與 Agent XP (經驗值) 系統

## 1. 願景與核心目標 (Vision & Goals)

隨著 **Twin Scout (Playwright + Gemini Vision)** 在 Docker 環境中成功抓出 MCP (port 8051) 未啟動導致的架構異常，數位孿生系統展現了其超越傳統 E2E 測試的巨大潛力。
本階段的目標是：
1.  **擴充 Twin Scout 的應用場景**：除了內部巡檢，更要具備「向外探索 (Outbound Scouting)」的能力，收集外部 UI 設計靈感與產出 Mockup。
2.  **建立 Agent 遊戲化追蹤 (Gamification & XP)**：針對 L1~L3 Agent (如 DevBot, POBot) 建立經驗值 (XP) 與層級追蹤系統，並首重 **「不重造輪子 (Zero-New-Table)」** 原則。

---

## 2. Twin Scout 擴展設計 (Digital Twin Expansion)

### 2.1 報告知識庫化 (Knowledge Ingestion)
*   **策略**: 將 Twin Scout 產出的 `.twin/diagnostics/report_*.md` 直接轉化為系統知識。
*   **作法**: 管理員可直接登入 **Admin UI (3737) -> Knowledge Base** 介面，透過現有的「上傳文件」功能，將 Markdown 報告送入 `archon_sources` 表進行切片 (Chunking) 與向量化 (Embedding)。這讓 RAG 助理能即時掌握系統最新的健康狀態歷史。

### 2.2 多角色自動化巡航 (Multi-Persona Cruising)
*   **物理實作**: `scripts/twin_scout.py` 已實作 Alice, Bob, Charlie 與 Admin 的自動化登入與 UI 渲染檢查。
*   **診斷閉環**: 產出的 `.twin/diagnostics/report_*.md` 可作為系統健康歷史，支援物理性的架構回溯。


---

## 3. Agent XP (經驗值) 系統設計 (Agent Experience Tracking)

**核心指導原則：不開啟新的資料表 (No New Tables)。**

### 3.1 儲存層：利用 `archon_logs` 作為 XP 帳本
不再為了 Agent 開設專屬的 Users 表，而是利用現存的日誌表 `public.archon_logs` 進行唯加 (Append-Only) 紀錄。
*   **Schema 映射**:
    *   `source`: 設為 `'agent_action'`
    *   `level`: 設為 `'success'` 或 `'error'`
    *   `details` (JSONB): `{"agent_name": "DevBot", "target_file": "DashboardPage.tsx", "xp_change": 15, "task_id": "uuid"}`

### 3.2 邏輯層：利用現存的 `stats_api.py`
完全不需要建立新的 `xp_service.py`。我們發現後端 `src/server/api_routes/stats_api.py` 已經實作了實體端點：
*   **物理端點**: `GET /api/stats/agent-xp`。
*   **實作邏輯**: 調用 `StatsService.get_agent_xp_stats()`，透過 SQL SUM() 聚合 `archon_logs` 中 `details->>'xp_change'` 的總和。
    ```sql
    -- 概念 SQL：計算特定 Agent 的總 XP
    SELECT SUM((details->>'xp_change')::int) as total_xp 
    FROM archon_logs 
    WHERE source = 'agent_action' AND details->>'agent_name' = 'DevBot';
    ```
*   **輔助整合 `calculate_ai_score()`**: 
    `stats_api.py` 現存的 `calculate_ai_score` 函式可被改造為「程式碼品質審核器」。當 Agent 提交 PR (Proposed Change) 時，根據通過 `make lint` 或是測試覆蓋率，動態判定應給予的 `xp_change` (+5, +10 或 -20)。

### 3.3 等級與權限連動 (Level Gateways)
根據加總後的 `total_xp`，動態對齊 `RBAC_Collaboration_Matrix.md` 所定義的權限：
*   **< 100 XP (實習生)**: 預設狀態。只能執行 Read 或是基本的 `make lint` 修正檢查。
*   **101 ~ 500 XP (L1 工程師)**: 解鎖修改單一檔案、單一函數的權限 (如本次修正 `Loading...` 的行為)。
*   **> 500 XP (L2 工程師)**: 解鎖跨檔案重構與 API 設計權限。

---

## 4. 下一步行動 (Next Steps)
- [x] **2026-03-20 物理落地 (XP Governance)**: 
    *   已在 `stats_api.py` 物理掛載 `GET /api/stats/agent-xp` 端點。
    *   **權限對齊**: 成功將 XP 等級與 `AgentService` 安全閘門物理連動。Agent 必須達到 Level 1 始獲物理寫入權限，達成「行為資歷化」治理。
- [ ] **待開發**: 將 Twin Scout 報告自動化上傳至 Knowledge Base 的 RAG 流程。

---

## 物理落地查核結論 (Physical Audit Conclusion) - 2026-03-11
*   **執行狀態**: 🟢 **100% 物理落地**
*   **關鍵證據**:
    *   **數位孿生腳本**: `scripts/twin_scout.py` (v28) 已實作完整的多角色登入與 UI 渲染檢查。
    *   **視覺診斷**: 已整合 `gemini-2.5-flash` Vision API，具備自動分析截圖並產出中文報告之能力。
    *   **物理執行痕跡**: `.twin/diagnostics/` 目錄下存有實體報錯截圖與診斷報告 (report_*.md)，證明系統曾在容器環境下真實運作。
*   **查核總結**: Digital Twin 系統已具備「自動巡航、視覺判定、報告歸檔」的完整闭環，成功達成 Agent 體驗的自動化治理。
