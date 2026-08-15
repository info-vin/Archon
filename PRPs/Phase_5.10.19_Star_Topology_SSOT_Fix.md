# Phase 5.10.19: Star Topology SSOT Fix

## Goal
修復 `agent_service.py` 依賴字串比對 (`[Daily Report]`) 導致系統降級並靜默跳過「星環群聊 (Star-Topology Group Chat)」的嚴重架構 Bug。我們將引入嚴格的 `TaskFeatureEnum` 進行 SSOT (單一事實來源) 對齊，徹底拋棄依賴 `title` 的脆弱路由邏輯。

## Background & Root Cause
在先前的「SSOT 最終淨化」中，靜態掃描工具漏抓了 `agent_service.py` 裡的一段 `Temporary hack` 邏輯。
根據我實地查核 `archon_workflow_flows` 資料庫實體表，Workflow Engine 目前支援三種流程：
1. `Marketing Data Deep Dive` (由使用者手動於 UI 建立)
2. `Daily Executive Summary` (由 `report_service.py` 每日自動觸發)
3. `General` (包含 `Info Request` 等預設回退流程)

**斷鏈主因**：
`report_service.py` 實際產生的標題是 `[Daily] Executive Summary`，但 `agent_service.py` 的 Hack 卻在尋找 `[Daily Report]`。因為字串不匹配，任務被降級為 `General` 類別。這導致 Supervisor (Charlie) 在執行時，使用了通用的預設 Prompt，判斷無需召喚其他 Agent，直接交由 `SummaryNode` 單點總結後結束，從而靜默跳過了 Alice, Bob, DevBot 的多角色深度討論。

*(註：Weekly 與 Monthly 報告是使用 Map-Reduce 架構 `beta_graph` 獨立執行，不經過 `agent_service` 的 Star-topology 路由，因此未受此 Bug 影響。群聊斷鏈的受災戶確實只有 Daily Report)*

## Proposed Changes

### Shared Constants
#### [MODIFY] `python/src/server/services/shared_constants.py`
- 新增 `TaskFeatureEnum(StrEnum)`，定義系統內所有依賴 Workflow Engine 的特徵：
  - `DAILY_EXECUTIVE_SUMMARY = "daily_executive_summary"`
  - `MARKETING_DATA_DEEP_DIVE = "marketing_data_deep_dive"`
  - `INFORMATION_REQUEST = "information_request"`

### Report Service (Source of Truth)
#### [MODIFY] `python/src/server/services/report_service.py`
- 在 `_create_summary_task_and_log` 時，將原本遺漏的 `feature` 參數補上，明確傳入 `feature=TaskFeatureEnum.DAILY_EXECUTIVE_SUMMARY.value`，徹底拋棄對 `title` 的隱性依賴。

### Agent Service (Consumer)
#### [MODIFY] `python/src/server/services/agent_service.py`
- 在 `_run_workflow_engine_task` 中移除脆弱的 `Temporary hack` 字串比對。
- 改為優先讀取 `task_data.get("feature")`：
  - 若匹配 `TaskFeatureEnum.DAILY_EXECUTIVE_SUMMARY`，則精準設定 `task_type = "Daily Executive Summary"`。
  - 若匹配 `TaskFeatureEnum.MARKETING_DATA_DEEP_DIVE`，則設定 `task_type = "Marketing Data Deep Dive"`。
  - 保留對歷史任務 Title 的相容性 Fallback，但警告這將被逐步淘汰。

## Verification Plan
1. **Automated Tests**: 執行 `make lint-be` 與 `make test-be` 確保無型別與單元測試錯誤。
2. **Physical Integration Verification**: 
   - 撰寫 `scratch/verify_5.10.19.py` 觸發一次 Daily Executive Summary。
   - 物理調閱資料庫的 `archon_tasks.attachments`。
   - 驗證 `messages` 陣列中是否包含 `name: alice`、`name: bob` 等角色的群聊足跡。
