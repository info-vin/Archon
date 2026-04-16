# Phase 4.6.33: Digital Twin 工作流感知與數據對齊 (Workflow-Aware Parity)

> **核心目標**: 讓數位分身 (Digital Twin) 理解業務工作流程 (Workflows)，透過資料庫實體數據與 UI 映射的即時比對，偵測邏輯層面的斷層。實施嚴格的 10 份報告代謝機制。

## 1. 工作流基準數據 (Workflow Benchmarks)
根據 2026-04-08 物理探查，各角色的實體工作流狀態如下：
- **Alice (Sales)**: 實體任務數 = `0` (Source: `archon_tasks`)。
- **Scout (Agent)**: 診斷檔案數 = `5` (磁碟佔用 244K)。
- **Metabolism Limit**: 10 份檔案 (硬限制)。

## 2. 物理任務清單 (Concrete Tasks)

### 33.1 任務：實作「工作流快照」注入 (Workflow Snapshot Injection)
- **物理動作**: 
    - 在 `scripts/twin_scout.py` 中，針對每位 Persona，登入前先執行 SQL 查詢取得其工作流狀態（如：任務總數、最新任務標題）。
    - 將這些「實體數據」封裝為 `Reality_Context` 餵給 Gemini Vision。
- **目標**: 讓 AI 具備「預期心理」，能主動指出：「DB 顯示 Alice 有 3 筆任務，但 UI 只畫出 2 筆，工作流顯示異常」。

### 33.2 任務：實作「高壓代謝」與診斷價值分級
- **物理動作**: 
    - 修改代謝上限為 **10 份**。
    - **邏輯分級**: 偵測報告結論。若診斷為 `WORKFLOW_SUCCESS` 且數據對齊，僅保留最新 1 份。若偵測到 `PARITY_MISMATCH`，則鎖定該報告防止被代謝刪除。
- **目標**: 確保磁碟中留下的每一份報告都是「具備診斷價值的資產」。

### 33.3 任務：Agent 行為資歷對齊 (Agent XP Parity)
- **物理動作**: 
    - 修改 `log_agent_xp` 邏輯，在寫入 XP 的同時，由 Scout 自行檢查 `archon_logs`，驗證本次巡檢是否確實被系統記錄。
- **目標**: 驗證 Agent 自身的「行為->紀錄」工作流是否斷裂。

## 3. 物理基準驗證 (Verification Protocols)
1. **數據穿透**: 執行 `make twin-scout`，確認產出的 Markdown 報告中明確寫出了「Expected: 0, Found: 0」等對齊數據。
2. **代謝驗證**: 手動填充 15 份舊報告，執行後確認總數降至 10 份，且包含 `MISMATCH` 字樣的舊報告被物理保留。

## 4. 安全計畫 (Safety Plan)
- **環境隔離**: 僅使用 `uv run` 呼叫 REST API，不破壞 Docker 容器間的依賴邊界。
- **真實數據**: 拒絕使用隨機垃圾數據進行測試，所有測試均基於 Supabase 的實體 Row。
