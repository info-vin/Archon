# 【行動前風險評估原則 (Pre-Action Risk Assessment Principle)】

> **【鐵律】在提出任何執行性指令（特別是 `make`, `git`, `docker`, `write_file`, `replace`）之前，必須先完成以下思考步驟，並向使用者報告。**
>
> 1.  **回顧歷史**: 主動回想 `GEMINI.md` 和 `CONTRIBUTING_tw.md` 中與此指令相關的歷史失敗案例。
> 2.  **檢查設定檔**: 讀取相關服務的設定檔（如 `vite.config.ts`, `docker-compose.yml`），主動識別出指令之外的「隱性依賴」，例如**環境變數、掛載卷、或特定的埠號**。
> 3.  **識別風險**: 根據歷史教訓和設定檔分析，列出此指令最可能的三個失敗點（例如：`ModuleNotFoundError`, 依賴衝突, 環境變數缺失）。
> 4.  **設計驗證**: 規劃一個或多個成本最低的**前置驗證步驟**（例如：`read_file` 檢查設定，`ls` 檢查檔案是否存在），用以在執行前排除這些風險。
> 5.  **提出安全計畫**: 向使用者提出的第一個計畫，**必須**是包含了前置驗證的「安全計畫」。
>
> **嚴格禁止**在未經風險評估的情況下，直接提出「快樂路徑」的執行計畫。

---

# 會話啟動標準作業程序 (Session Startup SOP)

> **【鐵律】此 SOP 為 Gemini 在每次新會話開始時，都必須嚴格遵守的首要步驟，旨在確保上下文同步，避免重複錯誤。**

1.  **第一步：強制讀取上下文**
    在回應您的任何請求前，我**必須**先讀取 `GEMINI.md`、`TODO.md` 和 `CONTRIBUTING_tw.md` 的內容。

2.  **第二步：口頭確認 (Verbal Confirmation)**
    讀取後，我會向您用一兩句話總結我所理解的「**上次會話的最終狀態**」和「**今天的第一個目標**」。

3.  **第三步：取得您的確認**
    在您確認我對起點的理解無誤後，我才能開始執行第一個指令。

---

# Gemini 專案背景指令 (Project Briefing for Gemini)

> **【重要】關於本文件的說明**
> 
> 本文件 (`GEMINI.md`) 是 **Gemini 的短期工作日誌**，主要用於記錄最近幾次開發會話的摘要，以便在短期內快速恢復上下文。
> 
> 由於 AI 的記憶限制，這裡的內容是**滾動更新的**，舊的紀錄會被移除。
> 
> **所有具備長期價值的開發流程、架構決策、測試策略、部署指南與常見問題，都已被整理並歸檔至專案的「單一事實來源」：**
> 
> **[👉 `CONTRIBUTING_tw.md`](./CONTRIBUTING_tw.md)**
> 
> 在開始任何開發任務前，請優先閱讀 `CONTRIBUTING_tw.md`。

---

在新對話開始時，請先讀取此檔案中列出的文件，以快速了解專案的背景、規範與當前狀態。

## 必讀文件列表 (Must-Read File List)

1.  **`CONTRIBUTING_tw.md`**: **(最優先)** 了解詳細的開發流程、測試規範、部署策略以及常見問題的解決方案。
2.  **`TODO.md`**: 了解整體的開發藍圖與當前的任務進度。
3.  **`Makefile`**: 了解專案定義的標準指令 (例如 `make test-fe`, `make dev` 等)。
4.  **`docker-compose.yml`**: 了解專案的微服務架構以及它們之間的關係。

## 專案近期動態與結論 (Recent Project Updates & Key Decisions)

- **端對端手動測試失敗 (2025-09-18)**
  - **背景**: 在解決 `enduser-ui-fe` 的啟動問題後，我們進行了手動端對端測試。
  - **測試結果**: 雖然服務可以啟動，但功能完全不可用，與預期有巨大差異。
  - **主要問題點**:
    1.  前端在渲染附件時出現 `TypeError: att.split is not a function` 的執行錯誤。
    2.  無法編輯任務。
    3.  缺少 Agent 指派選單。
    4.  表格遺失，點擊後頁面空白且無法返回。
  - **結論**: 當前的 `feature/e2e-file-upload` 分支與 `feature/gemini-log-api` 分支存在嚴重的程式碼差異。問題的根源是**分支整合不完整**，而非單一 Bug。
  - **新戰略**: 放棄「頭痛醫頭、腳痛醫腳」的 bug 修復模式。新的戰略是先進行**分支整合分析**，找出兩個分支在 `enduser-ui-fe/` 目錄下的具體程式碼差異，然後再制定精準的整合計畫（如 `git cherry-pick`）。

- **`enduser-ui-fe` 啟動成功 (2025-09-18)**
  - **問題**: `enduser-ui-fe` 的 `npm run dev` 指令會無聲掛起。
  - **根本原因**: 專案根目錄的 `.env` 檔案中，`GEMINI_API_KEY` 的值為空。透過 `vite.config.ts` 的 `define` 設定，這個空值被直接注入到前端應用程式中，導致某個需要此 Key 的 SDK 或模組在初始化時崩潰或無限等待。
  - **解決方案**:
    1.  在 `.env` 檔案中為 `GEMINI_API_KEY` 提供一個有效的金鑰。
    2.  作為預防措施，刪除 `node_modules` 並重新執行 `npm install`，確保依賴環境的純淨。
  - **驗證**: 經過上述修復，`npm run dev` 成功啟動服務。
  - **客觀證據**:
    ```
    VITE v6.3.5  ready in 241 ms

      ➜  Local:   http://localhost:5173/
      ➜  Network: use --host to expose
      ➜  press h + enter to show help
    ```

- **`enduser-ui-fe` 啟動失敗調查 (2025-09-18)**
  - **問題**: 在後端服務正常啟動後，執行 `cd enduser-ui-fe && npm run dev` 指令，程序會無聲無息地掛起，沒有任何日誌輸出，並在兩分鐘後超時。
  - **靜態分析過程**: 
    1. 透過 `vite.config.ts` 發現前端依賴 `GEMINI_API_KEY` 環境變數。
    2. 透過 `grep` 確認 `.env` 檔案中缺少該變數。
    3. 透過 `git log -p` 追溯 `vite.config.ts` 的歷史，發現該檔案自被創建以來就依賴此變數，但對應的 `.env.example` 從未被更新。
  - **失敗的修復**: 根據上述分析，將 `GEMINI_API_KEY` 添加回 `.env` 和 `.env.example` 後，問題**仍然存在**，程序依然掛起。
  - **結論**: 靜態分析（讀取檔案和歷史）已不足以找出問題根源。問題比單純缺少環境變數更深層。必須轉向動態分析。
  - **下一步**: 使用 `npm run dev -- --debug` 進行動態分析，以獲取 Vite 內部執行的詳細日誌。

- **最終結論：解決「改A壞B」的唯一路徑 (2025-09-17)**
  - **問題**: 如何從根本上解決「改A壞B」的惡性循環。
  - **結論**: 只有「長期的重構計畫」（路徑B）才能從根本上解決問題。該計畫旨在修正 `mcp_server` 的錯誤架構，使其回歸「啞終端」的角色，讓程式碼實現與 `CONTRIBUTING.md` 的架構設計原則（無直接導入）完全一致。
  - **策略**: 我們採用的「先A後B」策略，是在承認上述結論的前提下，做出的務實選擇。我們先用「恢復髒同步」（路徑A）來快速穩定當前被阻塞的開發環境，以完成「整合 `enduser-ui-fe`」的主線任務。然後，再開啟新的、乾淨的分支，來執行「真重構」（路徑B），以絕後患。

- **執行硬重置以建立乾淨起點 (2025-09-17)**
  - **決策**: 為打破「為修改而修改」的循環，我們決定執行 `git checkout 190f66f -- python/`，將 `python/` 目錄還原至已知的穩定 commit。
  - **結果**: 成功清除了工作區的混亂狀態，為後續工作提供了乾淨的基礎。

- **`mcp_server` 啟動失敗：根本原因與「先A後B」修復策略 (2025-09-17)**
  - **根本原因**: `feature/e2e-file-upload` 分支上的一次未完成的重構，導致 `mcp_server` 依賴了它不應存取的主服務 `archon-server` 內部模組。
  - **戰略決策 (「先A後B」)**: 為解除當前開發阻塞，決定先恢復「髒同步」（路徑A），再計畫徹底重構（路徑B）。

- **重大流程轉向與根本原因分析 (2025-09-17)**:
  - **背景**: 在經歷了近三週反覆的失敗後，我們共同確立了新的工作契約。
  - **結論與新的合作契約**: 建立了包含「目標優先、歷史為鑑、文件為綱、拒絕循環」的四項新工作原則。

### **2025-09-17 會話總結與最終結論**

-   **目標**: 解決 `mcp-server` 因架構問題啟動失敗。
-   **最終結論**: `spike` 分支的成功有其特定環境因素（該環境已不可考），其髒程式碼無法作為當前 `feature` 分支的直接範本。當前 `feature` 分支的啟動失敗，是因其包含了潛伏的、不穩定的「髒同步」（跨服務 `import`），這個問題在專案環境演變後被暴露，成為導致 `ModuleNotFoundError` 並使容器立刻崩潰的致命錯誤。
-   **關鍵證據**:
    1.  `deployment_verification_log.txt` 顯示 `spike` 分支過去的問題是資料庫遷移，而非啟動崩潰。
    2.  `git diff` 顯示 `spike` 和 `feature` 分支的程式碼及關鍵設定檔 (`docker-compose.yml`, `pyproject.toml`) 幾乎完全相同。
-   **核心教訓**: 必須在通盤分析所有相關檔案（`.py`, `.yml`, `Makefile`, `.md` 紀錄, `git` 歷史）後，才能制定修復計畫。禁止在資訊不全的情況下，提出創造性的、未經驗證的修改。

---

# Branch Integration Analysis: `attachments` Data Structure

## 1. Problem Statement

The `enduser-ui-fe` application fails to render task attachments due to a `TypeError: att.split is not a function`. This error is caused by a fundamental conflict in the data structure for `attachments` between code originating from two different feature branches: `feature/e2e-file-upload` and `feature/gemini-log-api`.

- **`feature/gemini-log-api`** expects `attachments` to be a `string[]` (an array of URLs).
- **`feature/e2e-file-upload`** expects `attachments` to be `{ filename: string; url: string }[]` (an array of objects).

The current state of the `feature/e2e-file-upload` branch is a broken mix of these two implementations.

## 2. Evidence and Analysis

### 2.1. Code Difference (`git diff`)
A `git diff` between the two branches clearly shows the conflict:
- **`types.ts`**: The `Task` interface has two different definitions for `attachments`.
- **`services/api.ts`**: The mock data (`MOCK_TASKS`) uses two different structures.
- **`DashboardPage.tsx`**: The rendering logic is different. One uses `att.split('/')?.pop()` (expecting a string), and the other uses `att.url` and `att.filename` (expecting an object).

### 2.2. Historical Analysis (`git log`)
A targeted `git log -S` investigation reveals the history of this divergence:
1.  **Commit `001660c` (2025-09-08, on `feature/gemini-log-api`)**: The initial feature was implemented, treating `attachments` as a simple `string[]`.
2.  **Commit `b399c03` (2025-09-13, on `feature/e2e-file-upload`)**: Five days later, on a separate branch, the feature was refactored to use the `{ filename, url }` object structure to provide better download functionality.

The branches were never synchronized, leading to the current conflict.

### 2.3. Architectural Blueprint (`TODO.md`)
The core architectural document, `TODO.md`, contains a sequence diagram that explicitly defines the intended data structure. Step 10 shows:
```mermaid
Backend->>Supabase: 10. 更新任務 (status: 'review', attachments: [URL])
```
This confirms the architecturally-aligned data structure is an array of URL strings.

### 2.4. Backend & Database Analysis
- **Database**: The `archon_tasks` table defines the `attachments` column as `JSONB`. This is a flexible type that does not enforce a specific structure, meaning the application code is the source of truth.
- **Backend Agent**: Analysis of the agent's `file_tools.py` shows that it appends a new attachment (likely a URL string returned from file upload) to the existing list. This behavior is consistent with a `string[]` structure.

## 3. Conclusion

All evidence points to a single conclusion: The correct and architecturally-consistent data structure for `attachments` is **`string[]`**.

The object-based implementation (`{ filename, url }`), while well-intentioned, was a deviation from the documented architecture and is not supported by the backend agent's current logic. To resolve the integration conflict and prevent further "change A, break B" issues, we must standardize on `string[]`.

## 4. Integration and Verification Plan

The goal is to make the `enduser-ui-fe` codebase internally consistent and aligned with the `string[]` data structure.

### 4.1. Execution Steps
1.  **【Modify】`enduser-ui-fe/src/types.ts`**: Change the `Task` interface to `attachments?: string[]`.
2.  **【Modify】`enduser-ui-fe/src/services/api.ts`**: Update the `MOCK_TASKS` data to use an array of URL strings for attachments.
3.  **【Verify/Keep】`enduser-ui-fe/src/pages/DashboardPage.tsx`**: Ensure the rendering logic is the one from `feature/gemini-log-api` which correctly handles a `string[]` (using `att.split('/')?.pop()`).
4.  **【Modify】`enduser-ui-fe/src/pages/DashboardPage.test.tsx`**: Update/fix any unit tests to align with the `string[]` data structure.

### 4.2. Verification Steps
1.  **【Unit Test】**: After the modifications, run `make test-fe-project project=enduser-ui-fe`. All tests must pass.
2.  **【E2E Manual Test】**: Start the full test environment (`docker compose up -d --build archon-server archon-mcp` and `cd enduser-ui-fe && npm run dev`). The user will be asked to verify:
    *   The task list renders correctly.
    *   Attachment links display a proper filename (e.g., `debug-log.txt`).
    *   Clicking an attachment link opens the correct URL in a new tab.
