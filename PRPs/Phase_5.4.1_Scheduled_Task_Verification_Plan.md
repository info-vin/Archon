# Phase 5.4.1: 全域排程任務與業務閉環自動化驗證架構 (Global Scheduled Tasks & Business Loop E2E Verification Architecture)

## 1. 執行摘要 (Executive Summary)
本階段目標旨在將 Archon 系統核心的 14 項 Clockwork 背景排程任務，全面納入 Twin Scout 數位雙生自動化驗證 (E2E MBT) 框架中。
鑑於傳統 E2E 測試在動態渲染與非同步架構（如 Server-Sent Events）中常遭遇高度不穩定性（Flakiness），本計畫確立了**「韌性化公證 (Resilient Auditing)」**與**「密閉式測試 (Hermetic Testing)」**雙軌並行的工程標準。我們不只驗證 UI 渲染，更深入驗證從「背景資料注入」到「前台 AI 決策與狀態流轉」的完整業務閉環 (Business Loop)。

---

## 2. 系統架構與設計決策 (Architectural Decisions)

### 2.1 任務拓樸分流設計 (Topology-based Scenario Routing)
為確保 14 項排程任務的公證腳本具備高維護性與低耦合度，將所有的 YAML 驅動配置依據業務生命週期進行三維度分流：

```text
scripts/twin_scenarios/
├── 01_stateless_patrols/          # 無狀態高頻巡檢 (Stateless Operations)
│   # 涵蓋：system_probe, log_patrol, model_verification
│   # 策略：【豁免 UI 錄影】不依賴 Playwright UI 操作。採用純後端 API 斷言與資料庫日誌穿透驗證 (Backend-to-Backend Auditing)，避免無效錄影消耗 CI 資源與儲存空間。
├── 02_stateful_daily/             # 核心商業閉環 (Stateful Business Loops)
│   # 涵蓋：alice_auto_fetch, bob_market_report, marketing_chat, check_workbench_video
│   # 策略：【強制 UI 錄影】實施資料庫前置注入 (Idempotent Seeding)，並執行完整的跨 Agent UI 協作驗證。
└── 03_governance/                 # 全局決策與治理 (Governance & Consolidation)
    # 涵蓋：fanout_executive_summary, tech_debt_audit
    # 策略：區分驗證級別。fanout 報表【強制 UI 錄影】驗證產出是否匯總至 Nexus 面板；tech_debt_audit 則【豁免 UI 錄影】，採後端日誌穿透驗證。
├── 04_persona_workflows/          # 人類角色操作閉環 (Human-in-the-loop Full UI Coverage)
│   # 涵蓋：alice_hunter_mode, alice_visit_log, bob_pitch_generation, charlie_approval_guard, david_rbac_matrix
│   # 策略：【強制 UI 錄影】完全拋棄單點按鈕測試，執行跨組件、跨 Modal 的「地毯式全介面驗證」。所有腳本必須可被 `make twin-record` 執行，產出真實操作錄影。
```

### 2.2 韌性化網路與渲染阻斷機制 (Network & Rendering Resilience)
基於實際 E2E 執行中所遭遇的超時 (Timeout) 與競爭條件 (Race Condition) 痛點，確立以下系統級防禦規範：

1. **SSE 網路死鎖解除 (Global Route Aborting)**：
   * **問題**：React 前端初始化時建立的持久化 `EventSource` (SSE) 連線，會導致 Playwright 的 `wait_until: networkidle` 條件進入無限死鎖，進而觸發框架層級超時 (Timeout 45000ms)。
   * **決策**：在 `twin_scout.py` 的 BrowserContext 層級，透過 `page.route("**/api/sse/tasks", lambda route: route.abort())` 進行全域請求攔截，直接阻斷 SSE 建立。這能確保測試腳本在不受長輪詢干擾下精準到達網路靜止狀態 (Idle State)。
2. **防禦性視圖鎖定 (Resolution-Locked Viewport)**：
   * **問題**：響應式設計 (RWD) 中，部分操作元件（如 FAB 浮動按鈕）在移動端解析度下極易受 Z-Index 層疊或渲染延遲影響，導致 `Locator.click: element is not visible` 的偽陰性錯誤 (False Negative)。
   * **決策**：棄用模糊的 `viewport` 參數，強制所有業務閉環 YAML 套用 `resolution: 1280x720`（對應 `md:table` 桌面端佈局），消滅浮動元件干擾，確保互動的決定性。

---

## 3. 業務閉環實作範式 (Business Loop Implementation Paradigm)

針對複雜的業務情境（如 Alice 的銷售線索流轉），必須嚴格遵守**「前置注入 -> 物理斷言 -> AI 決策驗證 -> 狀態流轉」**的四步合規標準。

### 3.1 冪等性資料前置注入 (Idempotent Data Seeding)
嚴禁測試腳本依賴開發環境的現有隨機狀態。所有 Stateful 測試必須在 `hooks/before_auth` 掛載 Python 前置處理腳本（如 `setup_alice_lead.py`）。
* **規範**：腳本必須具備自癒性，主動呼叫 REST API 鎖定目標資料（如 `RUCKUS Networks`），將其狀態強制還原為 `shortlisted`，並**即時更新 `created_at` 時間戳記**，保證目標卡片始終位於 UI 堆疊首位，消弭資料排序引起的驗證失敗。

### 3.2 靜態與視覺混成評判 (Hybrid AI-Static Judging)
* 對於動態變化的 AI 產出內容（如 POBot 的競品分析），維持使用 Gemini Vision 進行語義與視覺公證。
* 對於標準流程的最終狀態（如按鈕點擊後狀態從 New 變更為 Vendor），採用 Playwright 物理層級的 `wait_selector` 進行嚴格斷言。只要步驟鏈順利執行完畢，`analysis: static` 模組即發出 `[WORKFLOW_SUCCESS]` 簽證，避免因狀態流轉導致 UI 列表清空而引發 AI 視覺誤判。

---

## 5. 待執行公證清單 (Pending Verification Checklist)

以下是截至目前為止，尚未完成實作與自動化錄影驗證的場景清單。我們將依序完成這些 YAML 腳本的編寫與除錯。

### 02_stateful_daily (商業閉環)
- [ ] `bob_market_report.yaml`: 驗證 Bob 的市場情報產出與 RAG 資料聚合。

### 04_persona_workflows (全介面人類角色操作)
- [ ] `alice_hunter_mode.yaml`: 移動端觸控模擬，驗證 Alice 滑動卡片初篩。
- [ ] `alice_visit_log.yaml`: 語音上傳與 GPS 模擬，驗證多模態 AI 轉譯。
- [ ] `bob_pitch_generation.yaml`: 驗證 Bob 一鍵生成行銷提案 (Pitch) 與渲染。
- [ ] `charlie_approval_guard.yaml`: 驗證 Charlie 退件流程與 AI 理由生成是否寫入知識庫。
- [ ] `david_rbac_matrix.yaml`: 驗證 Admin 在 Identity Matrix 變更權限並即時生效。
