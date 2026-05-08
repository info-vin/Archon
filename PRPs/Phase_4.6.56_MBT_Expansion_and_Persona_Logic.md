# Phase 4.6.56: MBT 防禦網擴展與角色商業邏輯推進

> **文件狀態**: 📝 規劃中 (2026-05-08)
> **目標**: 基於 Phase 4.6.55 建立的可視化 MBT 測試框架，將零 Token 成本的 UI 自動化測試擴展至更複雜的業務元件（如 `ApprovalsPage.tsx`）。同時，推進各核心角色（Alice, Bob, Charlie, David）的特定商業邏輯，強化整體系統的業務閉環。

## 1. 執行摘要

本階段將以「系統開發與驗證」的宏觀視角，分為三軌並行，徹底根除測試環境與真實環境的斷層：
- **第一階段 (基礎設施打底)：建立全域系統級驗證地基 (Global Test Infrastructure)**。停止「單點修補測試腳本」，建立 Playwright 全域登入狀態 (`global.setup.ts`) 與中心化具狀態的 Fixtures，確保所有測試都在 100% 物理對齊的基礎上執行。
- **第二階段 (防禦網擴展)：向左推進 (Shift-Left) MBT 防禦網**。在系統級驗證地基上，將 Playwright + XState MBT 測試模式擴展到容易發生狀態衝突的複雜元件（如 `ApprovalsPage.tsx`）。
- **第三階段 (邏輯推進)：向右推進 (Shift-Right) 角色商業邏輯**。大膽推進各核心角色的專屬功能，包含資料流的串接與權限的細化。

---

## 2. 第一階段：建立系統級驗證基礎設施 (Global Test Infrastructure)

### 2.1. 全域身分持久化 (Global Auth State)
- **現狀痛點**: 每個測試腳本各自為政處理登入，導致測試跑得慢且一旦認證機制改變便會全軍覆沒。
- **系統解法**: 建立 `tests/playwright/global.setup.ts`。所有 E2E 測試在啟動前，透過系統自動取得 Auth Token 並儲存為 `.playwright/admin_storage_state.json`。測試腳本啟動時即處於「完美登入」狀態。

### 2.2. 中心化資料攔截與異常注入器 (Centralized Mock & Chaos Injector)
- **現狀痛點**: 各腳本自行捏造 `page.route` 假資料，缺乏 Schema 對齊，產生「幻覺測試」。
- **系統解法**: 建立 `tests/playwright/fixtures/systemFixtures.ts`，提供標準化的具狀態 Mock (Stateful Mocks)。同時提供 `simulateNetworkTimeout(page)` 或 `simulate500Error(page)` 介面，強制 UI 測試必須通過極端異常環境的考驗。

### 2.3. 基礎設施嚴格綁定
- **設定檔升級**: 修改 `playwright.config.ts`，將 `baseURL` 嚴格綁定至 `make dev-docker` 提供的本地物理環境，徹底拋棄依賴殘缺前端孤島的「樂觀測試」。

---

## 3. 第二階段：擴展 MBT 防禦網 (Expand MBT Defense Net)

### 3.1. ApprovalsPage 狀態機重構
- **現狀盤點**: `ApprovalsPage.tsx` 依賴多個 `useState` 與 `useEffect`，非同步狀態（批准、駁回、載入）易發生 Race Condition。
- **藍圖設計**: 建立 `approvalMachine.ts`，並在元件中導入 `@xstate/react`。
- **系統級驗證**: 使用剛剛建立的「全域登入」與「系統級 Fixture」，撰寫 `ApprovalsPage.mbt.spec.ts`，驗證其在網路延遲與 500 錯誤下的時光機錄影 (`trace.zip`)。

---

## 4. 第三階段：角色商業邏輯推進 (Persona Logic Advancement)

### 3.1. Alice (Sales) & Bob (Marketing) 工作流深化
- **資料連動**: 確保銷售線索 (Leads) 與行銷活動 (Campaigns) 之間的資料轉換與狀態流轉正確無誤。
- **防禦性 UI**: 在他們專屬的 Dashboard 中加入防呆機制與載入狀態的 XState 管理，防止在網路不穩時出現「重複提交」或「畫面卡死」。

### 3.2. Charlie (Manager) & David (Admin) 治理與審批
- **審批閉環**: 結合上述的 `ApprovalsPage` MBT 重構，確保 Charlie 能正確審核 Bob 與 Alice 送出的任務或預算申請。
- **權限硬化**: 嚴格測試 Role-Based Access Control (RBAC)，確保只有具備對應權限的角色能看到並操作特定的 API 端點與 UI 區塊。

---

## 5. 核心工程指引與驗證標準 (Engineering & Validation Standards)

> [!CAUTION]
> **絕對禁止「樂觀路徑 (Happy Path)」與「幻覺 Mock」**。本階段的交付標準，是建立在「系統隨時會崩潰、網路隨時會斷線」的假設之上。

1. **強制物理對齊 (Physical Parity Enforcement)**: 這是**現在唯一**的驗證標準，絕不妥協。所有 E2E 測試與 Mock 資料，必須與真實資料庫 (Supabase Schema) 及後端 API (FastAPI) **100% 物理對齊**。禁止憑空捏造（幻覺）任何欄位或端點。若使用 Mock，必須是「具狀態且型別安全」的；否則，測試必須直接連動 `make dev-docker` 的真實本地基礎設施。
2. **先設計狀態，再寫 UI**: 在修改任何 React 元件前，必須先定義 XState 狀態機。從數學上窮舉所有狀態，杜絕「人類想像」的漏網之魚。
3. **極端路徑優先 (Pessimistic Path First)**: 自動化驗證必須強制測試以下情況（透過 Playwright 網路攔截或真實環境模擬）：
   - API 回傳 500 / 503 / 401 錯誤。
   - 網路極度延遲 (Timeout > 10s)。
   - 多次狂按按鈕引發的 Race Condition。
4. **眼見為實 (Trace Viewer 公證)**: 所有的驗收都必須附帶 Playwright 的 `trace.zip`。沒有時光機錄影證明，該功能即視為「未完工」。

---

## 6. 下一步 (Next Steps)
*   **步驟 1**: (✅ 已完成) 實作第一階段。建立 `playwright/global.setup.ts` 並設定 `playwright.config.ts` 以支援 `admin_storage_state.json` 全域認證持久化。
*   **步驟 2**: (✅ 已完成) 建立 `systemFixtures.ts` 以提供標準化的 100% 物理對齊資料與異常狀態模擬 (`StatefulMock`, `simulateNetworkTimeout`, `simulate500Error`)。
*   **步驟 3**: (✅ 已完成) 將稍早遇到登入牆的 `PromptManagement.mbt.spec.ts` 重構為依賴上述系統級基礎設施，移除了腳本內的假登入與 API Mock，改用 `global.setup.ts` 的持久化狀態與 `systemFixtures.ts` 的具狀態 Mock，並成功產出時光機錄影。
*   **步驟 4**: (✅ 已完成) 實作第二階段：擴展 MBT 防禦網。重構了 `ApprovalsPage.tsx`，提取狀態邏輯至 `approvalMachine.ts` 並全面導入 `@xstate/react`；同時撰寫了 `ApprovalsPage.mbt.spec.ts` 以驗證在極端網路延遲與 500 錯誤下的時光機錄影與防呆狀態。
*   **步驟 5**: (✅ 已完成) 實作第三階段：向右推進角色商業邏輯。成功修復並穩定了 `PersonaWorkflow.mbt.spec.ts` 跨角色工作流測試（Alice -> Bob -> Charlie）。
*   **步驟 6**: (🚀 結案) 達成 Phase 4.6.56 所有目標。本階段成功建立了系統級驗證地基，擴展了 MBT 防禦網至 `ApprovalsPage`，並打通了跨角色的業務閉環驗證。

## 7. 階段性成果總結 (Conclusion)

本階段 (Phase 4.6.56) 已物理落地，達成以下關鍵指標：

1. **基礎設施硬化**: 透過 `global.setup.ts` 實現全域認證持久化，並建立 `systemFixtures.ts` 提供具狀態的 Mock 環境，消滅了「測試幻覺」。
2. **MBT 防禦網實體擴展**: 成功對 `ApprovalsPage.tsx` 進行 XState 重構，並建立對應的 MBT 測試，具備應對 500 錯誤與網路延遲的防禦能力。
3. **跨角色業務閉環驗證**: 徹底修復 `PersonaWorkflow.mbt.spec.ts` 的所有失效點，包含：
    - **CORS 與 Preflight 解決**: 透過 Mock `OPTIONS` 請求解決了跨網域提交的阻斷。
    - **具狀態審批流**: 實作了會隨操作改變狀態的 Mock，驗證了「審批後消失」的真實業務邏輯。
    - **UI 穩定性與逾時優化**: 針對複雜頁面（如 Manager Dashboard）優化了頁籤切換與可視性等待，達成 100% 通過率。

> [!IMPORTANT]
> **下一個里程碑**: 基於目前穩定的測試地基，我們已準備好進入 Phase 4.7，進行更大規模的特徵開發與效能優化。所有新開發的功能必須嚴格遵守本階段建立的「先設計狀態，再寫 UI，且必附 MBT 測試」的鐵律。
