# Phase 5.1.3: David - AI 自我進化 (能力恢復與工作流重連)

## Goal Description
根據 Git Log 考古 (Phase 4.5.7)，系統底層已具備 `CodeModifier` (Git 沙盒修改) 與 `Self-healing` (自動修復) 邏輯。然而在 Phase 5.0 的多智能體架構重構中，這些能力未被正確橋接到 David (Developer) 角色。

本階段目標是執行 **「能力重連 (Re-wiring)」**：讓住在 8052 Port 的 David 能透過 8181 Port 的 `ProposeChangeService` 發起實體代碼修改提案，並在人類核准後自動執行修復。

## User Review Required

> [!IMPORTANT]
> **重連而非重寫**: 我們將直接調用現有的 `src/server/utils/code_modifier.py`，不重複造輪子。
> **提案審核制**: 為了安全，David 的所有修正都必須經過 `proposed_changes` 表，由人類在 UI 點選 Approve 後觸發。

## Proposed Changes (實體對帳版)

### 1. [Backend] 補齊內部 API 與執行觸發 (8181 Port) - 🟢 已完成
*   **[MODIFY] [internal_api.py](file:///Users/vincenta/GoogleKwok022/Archon/python/src/server/api_routes/internal_api.py)**: 
    *   新增 `/internal/david/read` 與 `/internal/david/propose`。
    *   實作 **Internal Trusted Zone** 檢查，解決 David (8052) 呼叫時的 401 權限阻礙。
*   **[MODIFY] [propose_change_service.py](file:///Users/vincenta/GoogleKwok022/Archon/python/src/server/services/propose_change_service.py)**: 
    *   物理連動 `approve_proposal` -> `CodeModifier`。

### 2. [Agents] David 角色賦能 (8052 Port) - 🟢 已完成
*   **[MODIFY] [workflow_engine.py](file:///Users/vincenta/GoogleKwok022/Archon/python/src/agents/workflow_engine.py)**: 
    *   David 升級為實體 Agent，具備 `read_code_file` 與 `propose_code_fix` 工具。

### 3. [Frontend] 審核介面與執行結果 (5173 Port) - 🟢 已完成
*   **[MODIFY] [TaskAgentGroupChat.tsx](file:///Users/vincenta/GoogleKwok022/Archon/enduser-ui-fe/src/components/task-modal/TaskAgentGroupChat.tsx)**: 
    *   偵測 Proposal ID 並自動渲染「Review Proposed Changes」按鈕。
*   **[MODIFY] [useApprovalInbox.ts](file:///Users/vincenta/GoogleKwok022/Archon/enduser-ui-fe/src/features/manager/hooks/useApprovalInbox.ts)**: 
    *   支援 URL 參數自動選中，達成「對話到審核」的無縫跳轉。

### 4. [Infrastructure] 環境缺失加固 - 🔴 待執行
*   **[MODIFY] Dockerfile**: 在 `archon-server` 鏡像中加入 `git` 安裝指令。
*   **[FIX] UUID 兼容**: 在 `ProposeChangeService` 中對 `approved_by` 進行類型防禦，容許 String ID。

## Verification Plan (物理公證)

### [x] 跨容器 API 連動測試 (scripts/verify_david_evolution.py)
*   **結果**: David (127.0.0.1) 已能成功讀取 `/app/src` 並提交提案。

### [/] 物理寫入測試 (scripts/approve_verify.py)
*   **當前狀態**: 阻塞於容器內缺少 `git`。
*   **目標**: 完成 Dockerfile 更新後，達成「提案 -> 核准 -> 分支 -> 實體檔案產出」的完整閉環。
