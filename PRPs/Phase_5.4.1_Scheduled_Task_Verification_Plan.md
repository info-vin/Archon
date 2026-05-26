# Phase 5.4.1: 自動化排程任務驗證計畫 (Scheduled Tasks Verification)

本階段目標是將 14 項核心排程任務 (Clockwork) 納入 Twin Scout 數位雙生自動化驗證架構中。我們不再依賴脆弱的定時測試，而是透過「觸發-等待-斷言」模式確保所有商業關鍵路徑 (Critical Paths) 皆能真實反映於前端 UI。

## 1. 任務分流架構 (Scenario Directory Structure)

所有場景檔將按任務屬性嚴格分流：

```text
scripts/twin_scenarios/
├── 01_stateless_patrols/          # 檢查系統健康度 (如：system_probe)
├── 02_stateful_daily/             # 商業核心邏輯 (如：alice_auto_fetch, marketing_chat)
└── 03_governance/                 # 決策彙整 (如：fanout_executive_summary)
```

## 2. 實作計畫 (Implementation Plan)

### A. 優先驗證項目 (高重要性)
1. **alice_auto_fetch.yaml**: 驗證每日線索導入 (Lead Ingestion) 是否反映於 UI 列表。
2. **bob_market_report.yaml**: 驗證 RAG 內容聚合與趨勢圖表渲染。
3. **daily_executive_summary.yaml**: 驗證各 Agent 協作後的成果是否成功產出於主管 Nexus 面板。

### B. 技術規格：韌性化測試 (Resilience Strategy)
*   **動態等待**: 使用 `wait_selector` 替代 `sleep`，實作輪詢機制。
*   **視覺公證**: 設定 Gemini Vision Prompt 識別 Headless 環境下的深色區塊，降低偽陰性 (False Negative)。
*   **狀態防禦**: 在 `hooks/before_auth` 中動態注入測試所需權限，不污染生產資料庫。

## 3. 驗收門禁 (Acceptance Criteria)
1. [ ] 14 項排程任務的場景腳本建立並通過 `make twin-record` 驗證。
2. [ ] 所有場景驗證影片成功匯入 `enduser-ui-fe/public/assets/videos/auto_demos/`。
3. [ ] 整合至 `make audit-qa` 門禁，作為系統每日自動化體檢的一環。
