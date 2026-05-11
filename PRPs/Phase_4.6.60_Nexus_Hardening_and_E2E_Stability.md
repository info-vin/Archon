# Phase 4.6.60: Nexus 穩定性硬化與 E2E 測試實體對齊 (Nexus Hardening & E2E Physical Parity)

> **文件狀態**: ✅ 已完成 (2026-05-11)
> **目標**: 徹底根除 Manager Nexus 儀表板的「加載死鎖」與 Playwright MBT 測試在無頭環境 (Headless) 下的崩潰。將此次修復的經驗系統化，作為未來擴展的「防禦性開發標準」，並成為可注入 RAG 知識庫的工程經驗。

## 1. 執行摘要 (Executive Summary)

在驗證 Phase 4.6.55~59 的過程中，我們發現系統在「空資料庫狀態」與「CI 無頭環境」下會引發連鎖崩潰。這揭示了過去開發中依賴「樂觀路徑 (Happy Path)」與「環境預設 (Environment Assumptions)」的技術債。

本階段實施了四項**物理層級的硬化措施**，成功將測試通過率從不穩定的 0% 提升至穩定的 100%。

## 2. 核心技術債與硬化修復 (Core Debt & Hardening Fixes)

### 2.1 後端空資料防護 (Backend Empty State Hardening)
- **病灶**: `propose_change_service.py` 中使用了 `supabase-py` 的 `.maybe_single()`。當資料表為空時，該方法在特定套件版本下回傳 `None`，導致後續的 `.data` 存取觸發 `AttributeError`，進而產生 HTTP 500 (`PGRST116`)。這會讓依賴此 API 的前端 `Promise.allSettled` 卡死。
- **修復 (防禦性寫法)**: 全面棄用 `.single()` 與 `.maybe_single()`，改為安全的陣列查詢模式：
  ```python
  res = query.execute()
  if res.data and len(res.data) > 0:
      profile = res.data[0]
  ```

### 2.2 前端 API 實體對齊 (API Physical Parity)
- **病灶**: 前端舊版代碼仍呼叫 `/api/stats/overview` 與 `/api/stats/ethics-audit-queue`，但後端重構時遺漏了這些端點，導致前端收到 404，無法解析有效資料。
- **修復**: 在 `stats_api.py` 中補齊別名 (Aliases) 與對應結構，確保前端在任何情況下都能拿到預期的 JSON (如 `{"violations": [], "status": "clear"}`)。

### 2.3 圖表無頭環境崩潰 (Headless Chart Crash)
- **病灶**: Recharts 圖表的「動畫 (Animation)」在 CI (Playwright Headless) 環境中，會因為資料載入瞬間無法計算物理座標，導致 `NaN` 並引發 `TickItem Error`，徹底摧毀 React 元件樹。
- **修復 (測試友善化)**: 在所有儀表板圖表 (`IntegrityAnalysis`, `PerformancePulseChart`) 中，強制設定 `isAnimationActive={false}`，並加入 `payload?.value ?? ''` 的空值防護。

### 2.4 E2E 具狀態模擬 (Stateful Mocks in MBT)
- **病灶**: E2E 測試中的 Mock 寫法過於簡陋，導致 React 重新渲染時，原本 Mock 出來的假資料消失，測試腳本找不到目標元素 (如 `Draft for ...`) 而發生 Timeout。
- **修復**: 在 `PersonaWorkflow.mbt.spec.ts` 導入「具狀態模擬 (Stateful Mocks)」，利用外部變數 (如 `isApproved = false`) 讓 Mock API 的回傳值能隨著操作動態改變，真實還原業務生命週期。

## 3. 經驗文件化與 RAG 注入 (Knowledge Governance)

這些血淚教訓必須成為團隊的共同大腦。此文件的內容應當轉換為 RAG 知識庫的一部分，確保未來的 AI Agent (Librarian) 或開發者在遇到類似問題時能被準確糾正：

- **知識庫注入標的 1**: `Frontend UI Standards` 
  - *規則*: 「所有基於 Recharts 的圖表元件，必須預設關閉動畫 (`isAnimationActive={false}`)，或確保在 E2E 環境下能自動禁用，否則將導致 Playwright 無法完成截圖與狀態驗證。」
- **知識庫注入標的 2**: `Backend Database Standards`
  - *規則*: 「禁止使用 `.single()` 與 `.maybe_single()`。必須使用 `.execute()` 並透過 `len(data) > 0` 來判斷資料是否存在，以防禦 500 Internal Server Error。」
- **知識庫注入標的 3**: `Testing & QA Standards`
  - *規則*: 「E2E 驗證絕不可依賴『已有資料的開發者資料庫』。所有 MBT 測試必須包含空資料 (Empty State) 的負面斷言。」

## 4. 驗證標準 (Definition of Done)

> [!CAUTION]
> **拒絕樂觀路徑**：驗證的標的一定要準確，不可以幻想。

1. [x] **CI=1 Playwright 通過**: 必須在設定了 `CI=1` 的環境下，通過 `PersonaWorkflow.mbt.spec.ts`，證明無頭環境與具狀態 Mock 的有效性。
2. [x] **品質公證**: 必須通過 `make lint` 確保代碼風格一致。
3. [x] **後端防禦公證**: 必須通過 `make test-be` 確保所有 API 端點（包含空資料）不崩潰。
4. [x] **通訊公證**: 必須通過 `make persona-audit` 確保角色實體連線暢通。
