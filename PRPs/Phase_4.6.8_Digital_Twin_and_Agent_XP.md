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

### 2.2 外部 UI 偵察與 Mockup 生成 (External Scouting)
*   **擴展動機**: 雙生系統並非只能用來「測試」，也能用來「研發」。
*   **實作藍圖**: 透過動態變更 `make twin-scout` 的 Target Prompt，賦予 Twin Scout 外部網址的探索權。
    *   **UI 靈感採集**: 指示 Scout 前往知名網站 (如 Awwwards, Dribbble)，利用 Playwright 截取特定排板的快照，交由 Gemini 分析其色彩美學與 Flexbox 結構。
    *   **Banana Mockup 生成**: 結合 `browser-use` 核心或者 Gemini 的生圖工具，根據擷取到的風格生成前期的 UI 設計稿 (Mockup/Banana image)。
*   **規避 429 與 Docker 瓶頸**:
    *   為防止 Free Tier API 的 HTTP 429 (Rate Limit) 限制，以及省去 Docker Compose 的網路/硬體耗損。
    *   此 External Scouting 模式可改為**純 Local 環境執行腳本** (指定 URL 而非 Docker 內的 `http://enduser-ui:5173`)，靈活度極高且成本近乎為零。

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
完全不需要建立新的 `xp_service.py`。我們發現後端 `src/server/api_routes/stats_api.py` 已經實作了強大的統計端點。
*   **改造 `get_member_performance()`**: 
    將此 API 擴充，使其不僅查詢人類使用者的 `archon_tasks` 處理率，也能透過 SQL SUM() 聚合 `archon_logs` 中 `details->>'xp_change'` 的總和。
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
- [ ] 測試將 Twin Scout 報告上傳至 Admin UI (3737) 的 Knowledge Base。
- [ ] 在 `stats_api.py` 中實作 `get_agent_xp_ranking()` 函數，並與前端 Admin Dashboard 對接。
- [ ] 撰寫一個可存取外部 URL 以抓取 UI 靈感的延伸版 Scout Prompt。
