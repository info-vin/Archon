# Phase 4.6.43: MCP 與成本數據物理對齊 (Grounded Alignment)

> **目標 (Goal)**: 徹底終結 MCP 的「影子架構」並修復積壓兩個月的成本數據展示斷層。
> **核心對帳 (Audit Date: 2026-04-20)**:
> 1. **MCP 失效**: `main.py` 啟動時靜默失敗，且 `AgentService` 使用本地 `_native_tools` 攔截了工具執行。
> 2. **數據斷層**: `stats_api.py` 因 `PGRST200` (JOIN 錯誤) 導致 64 筆數據無法回傳。
> 3. **UI 遺漏**: 5173 的 `AdminPage.tsx` 缺少成本展示標籤。

---

## 1. 物理斷層診斷報告 (Physical Gap Audit)

### A. MCP 執行鏈條斷裂
*   **現狀 (Fact)**: `AgentService` 定義了 `_native_tools` (25-29行)，攔截了 `apply_modification` 等工具。
*   **物理阻塞 (Blocking)**: `docker-compose.yml` 中 `archon-mcp` 服務未掛載 `/app/src`，導致其無法執行實體檔案操作。
*   **靜默失敗**: `main.py` 在 MCP 連線失敗時僅發出 `warning`，未中斷啟動也未在 UI 警報。

### B. Token 成本數據「視而不見」
*   **現狀 (Fact)**: 資料庫 `token_usage` 已有 64 筆數據，但 `MetricsManager` 使用了錯誤的 JOIN 查詢。
*   **UI 缺失**: 5173 介面無「Cost & Usage」入口，且 `$0` 成本顯示為空白。

---

## 2. 實作計畫 (Action Items - 已執行與待執行)

### [Phase 1] 數據通路修復 (Data Path Recovery)
- [x] **Task 1: 修正後端 API 查詢**
    - **檔案**: `python/src/server/services/stats/metrics.py` (242行)。
    - **動作**: 移除 JOIN 查詢，改為單表查詢以繞過 `PGRST200` 錯誤。
    - **驗證**: `uv run` 撥測成功獲取 10 筆數據。
- [x] **Task 2: 物理掛載前端標籤**
    - **檔案**: `enduser-ui-fe/src/pages/AdminPage.tsx`。
    - **動作**: 新增 "Cost & Usage" 標籤並掛載 `SystemHealthDashboard`。
- [x] **Task 3: 修正成本顯示邏輯**
    - **檔案**: `TokenUsageTable.tsx`。
    - **動作**: 確保 `$0` 顯示為 `$0.0000` 而非空白。

### [Phase 2] MCP 物理封印解除 (Physical Unblocking)
- [x] **Task 4: 硬化啟動報警**
    - **檔案**: `python/src/server/main.py`。
    - **動作**: 提升 MCP 連線失敗至 `ALERT` 級別，寫入 `archon_logs`。
- [ ] **Task 5: 解除 MCP 權限封印**
    - **檔案**: `docker-compose.yml`。
    - **動作**: 將 `./python/src` 掛載到 `archon-mcp` 服務。
- [ ] **Task 6: 遷移影子工具 (Shadow Tool Migration)**
    - **檔案**: `python/src/server/services/agent_service.py`。
    - **動作**: 逐步移除 `_native_tools` 攔截，將邏輯回歸 `mcp_server` 的實體工具中。

---

## 3. 驗證標準 (Verification)

1. **數據透明**: David (Admin) 登入 5173 點擊 "Cost & Usage" 必須能看到實體 64 筆數據。 (🟡 待 David 驗證)
2. **MCP 監控**: 斷開 MCP 服務，驗證 "Connectivity Exception Log" 是否出現 `mcp-neural-wiring` 紅色警告。 (🟡 待物理斷連測試)
3. **MCP 執行**: 移除攔截後，Agent 呼叫 `apply_modification` 必須由 `archon-mcp` 容器物理完成修改。 (🔴 待實施)

---

## 4. 結案與下一步
- **下一步**: 修改 `docker-compose.yml` (Task 5)，這是不幻想、不猜測的物理環境調整。
