# Phase 4.6.55: UI/UX 測試基礎設施與基於模型的測試 (Model-Based Testing)

> **文件狀態**: 🟢 進行中 (2026-05-08)
> **目標**: 透過建立零 Token 成本、自動化的 UI 測試基礎設施（基於模型的測試與時光機回放），根除「幽靈開發」並擺脫對手動 UI 驗證的依賴。

## 1. 執行摘要

本階段旨在解決傳統 E2E 測試的脆弱性（UI 腐化、具狀態 Mock 的缺陷、非同步時間差問題）以及 Agentic UI 測試高昂的 Token 成本。我們將向左移 (Shift-left) 採用**基於模型的測試 (MBT)**，並向右移 (Shift-right) 採用**時光機回放 (Session Replay)**，以建立無懈可擊的 UI/UX 防禦網。

本階段的主要成果將包含：
1. **基礎設施部署**: 在前端客戶端安裝 XState 與 Playwright 依賴套件。（✅ 已完成）
2. **PromptManagement MBT 整合**: 重構 David 的 Admin SRE 控制面（Port 5173 上的 `PromptManagement.tsx`），交由正規的 XState 狀態機來控管。（✅ 已完成）
3. **自動化可視化驗證 (時光機回放)**: 整合 Playwright 原生的 Trace Viewer，在執行 E2E 測試時完整記錄 DOM 狀態、影片與網路日誌，徹底消除手動測試與第三方 Session Replay 帶來的額外負擔。（✅ 已完成）

---

## 2. 詳細實作

### 2.1. 環境與基礎設施設定 (✅ 已完成)
- **依賴矩陣**: 在兩個前端專案中安裝了 `xstate`、`@xstate/react` 與 `@playwright/test`。
- **架構修正**: 最初計畫使用 PostHog 作為 Session Replay 方案，但在發現本地 `docker-compose.yml` 根本沒有包含自託管的 PostHog 後，便解除了 `posthog-js` 的安裝並移除相關環境變數。隨後轉向使用零配置的 Playwright Trace Viewer。
- **建置驗證**: 安裝後成功通過 Linting 檢查與生產環境建置。

### 2.2. PromptManagement XState 整合 (✅ 已完成)
- **藍圖建立**: 設計了 `promptMachine`，定義了各種狀態（`loading`、`ready.idle`、`ready.editing`、`ready.saving`、`error`）與事件（`FETCH_SUCCESS`、`SELECT_PROMPT`、`TOGGLE_VIEW`、`UPDATE_VALUE`、`REVERT`、`SAVE`）。
- **元件重構**: 替換掉 `PromptManagement.tsx` 內部脆弱的 `useState` 與 `useEffect` 群組，改用 `useMachine(promptMachine)`，將所有使用者操作映射至狀態機事件。
- **NodeJS 單元測試**: 撰寫了 `PromptManagement.machine.test.ts`，透過 `vitest` 執行並驗證隔離狀態下的邏輯模型。

### 2.3. Playwright MBT 可視化驗證 (✅ 已完成)
- **腳本建立**: 建立了 `PromptManagement.mbt.spec.ts`，在真實的 Chrome 瀏覽器中驅動 XState 狀態路徑，並開啟了 `trace: 'on'` 與 `video: 'on'`。
- **阻礙排除**: 先前因為 Playwright 在隔離的環境中啟動，被 React HashRouter 重新導向至登入頁面，導致 `Timeout 30000ms exceeded` 錯誤。已透過以下方式解決：
  1. 修正 `page.goto`，針對 HashRouter 使用 `/#/auth` 與 `/#/admin`。
  2. 針對 Supabase 驗證 (`/auth/v1/token`) 與 Profiles API (`/rest/v1/profiles`) 新增明確的網路攔截 (`page.route`)，以模擬 `system_admin` 登入狀態。
  3. 將 API 攔截端點從 `/api/admin/prompts` 更正為真實的 `/api/system/prompts`。
- **結果**: MBT 可視化測試現在已能成功執行完整的 XState 生命週期，並產生有效的影片與 Trace 檔案（時光機）。

---

## 3. 核心工程教訓 (已記錄至記憶體)

1. **具狀態的 Mock 與線性腳本的對比**: 缺乏具狀態資料庫 Mock 的線性 E2E 測試無法測試 CRUD 生命週期。MBT 將重點轉移至測試狀態機本身。
2. **Session Replay 勝過影片演練 (Walkthroughs)**: 強迫開發者為 UI 錯誤錄製影片是不符合敏捷精神的。Session Replay 能擷取真實的 DOM 樹與 Network 頁籤，提供可操作的遙測數據，而非單調的 MP4 影片。
3. **零 Token 自動化**: 使用本地 MBT 遍歷測試能帶來與 AI Agent 相同發掘邊緣案例 (Edge-case) 的好處，但成本為 $0，且執行時間只需幾毫秒。
4. **幻想的基礎設施**: 在未實際檢驗 `docker-compose.yml` 中是否存在該服務之前，絕不應提議後端服務（如位於 `localhost:8000` 的 PostHog）。（已作為 Lesson 19 加入 `GEMINI.md`）。
5. **Playwright 的隔離環境**: 執行受保護 UI 路由的 E2E 測試時，若導覽前未先進行 Mock 或植入認證狀態，必然會隱性失敗。瀏覽器的執行環境對開發者本地的登入狀態是沒有記憶的。
6. **HashRouter 導覽與 API 對齊**: Playwright UI 測試必須尊重前端路由機制（例如 `/#/auth`），且 Mock 的 API 路徑必須嚴格對應應用程式真實的後端請求（例如 `/api/system/prompts` vs `/api/admin/prompts`），否則 Mock 會被繞過，導致來自真實後端的隱性認證錯誤。

---

## 4. 下一步
*   **步驟 1**: (✅ 已完成) 透過 Supabase 網路攔截與 HashRouter 對齊，解決 Playwright 的認證阻擋問題。
*   **步驟 2**: (✅ 已完成) 成功執行 Playwright 測試並驗證 `trace.zip` 與 `video.webm` 的產出。
*   **步驟 3**: 總結 Phase 4.6.55，並過渡至 Alice 與 David 工作流強化的配置設定。
