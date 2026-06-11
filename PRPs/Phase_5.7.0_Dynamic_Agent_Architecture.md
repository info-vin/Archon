# Phase 5.7.0 - AI Agent 動態架構配置與流程治理 (Dynamic Agent & Workflow Architecture)

## 🎯 核心目標 (Goal)
1. **消滅配置硬編碼**：將 AI Agent 的元數據（名稱、模型、可用工具）、部門指派權限（RBAC），以及工作流走向定義（Flow Graph）完全資料庫化。
2. **實現動態治理**：後端與 5173 UI 透過資料庫進行 100% 物理對齊。管理員可在 UI 上動態指派工具權限、調整模型，以及設計工作流節點走向。
3. **無損降階 Fallback**：在資料庫異常時，後端代碼具備嚴格的 Bounded Meet-Semilattice 有界半格防禦性降階，保障服務不 Crash。
4. **硬性證據驗收**：本階段的驗收必須包含 **Playwright 自動化錄影驗證 (E2E Record Video)**，將影片實體嵌入 walkthrough 進行物理公證。

---

## 📋 建議變更與詳細實作計畫 (Proposed Changes)

### 1. 資料庫 Schema 擴充 (Database Tables)
- **新增 SQL 遷移檔**：
  - `public.archon_agents`：管理 Agent 屬性（key, name, model_tier, default_tool）。
  - `public.archon_agent_tools`：管理 Agent 與工具的授權關係。
  - `public.archon_role_agents`：管理系統部門（sales, marketing...）與 AI Agent 的權限矩陣。
  - `public.archon_workflow_flows`：管理工作流節點與 Supervisor 的路由走向 JSON。

### 2. 後端服務解耦 (Backend Refactoring)
- **修改檔案**：
  - `agent_registry.py`：改為調用 `AgentConfigService` 從資料庫加載 Agent 配置與工具。
  - `agent_service.py`：`get_assignable_agents` 改為動態查詢 `archon_role_agents`。
  - `nodes.py`：`SupervisorNode` 與工作流節點走向改為從 `archon_workflow_flows` 表動態解析 node 路由。

---

## ✅ 驗證與驗收計畫 (Verification & Quality Gate)

### 1. 自動化測試 (Automated Tests)
- **靜態語法檢查**：`make lint` 必須 0 Errors / 0 Warnings。
- **單元與整合測試**：執行 `make test-be` 確保無任何 Regression 錯誤。
- **動態架構測試**：新增 `tests/integration/services/test_dynamic_agents.py`，驗證在資料庫中動態修改 Agent 屬性與工具後，後端獲取的配置立即生效。

### 2. Playwright 自動化錄影驗收 (E2E Video Recording)
- 撰寫 Playwright 腳本：`tests/playwright/DynamicAgentGovernance.spec.ts`。
- **自動化流程**：
  1. 登入 Admin 帳戶至 5173 UI。
  2. 動態變更 `market-bot` 的可用工具。
  3. 登入 Marketing 帳戶，驗證該 Bot 可用工具已即時改變。
  4. 執行任務並調用該 Bot，驗證任務成功完成。
- **錄影規格**：
  - 在 `playwright.config.ts` 中啟用 `video: "on"` 錄製選項。
  - 驗收時將產生的錄影檔案實體複製到 artifacts 資料夾，並使用 `![Dynamic Agent Config Video](file:///path/to/video.webm)` 語法嵌入在 `walkthrough.md` 中作為物理公證證據。
