# Phase 4.6.11: 系統重構與模組化精確執行計畫 (Precise Refactoring Strategy)

> **前言**: 本文件基於 `find`, `wc -l`, 與 `grep` 的精確靜態代碼掃描結果，確立 3 項大型檔案重構指標，替換所有模糊用語，以數字與具體數量為執行的唯一標準。

---

## 標的 1. 前端巨型元件分解 (50~100行標準)

我們掃描了超出 900 行的 3 個主要前端檔案，並制訂具體切分計畫：

1.  **`enduser-ui-fe/src/pages/AdminPage.tsx` (總計 902 行)**
    *   **提取目標**: 將內部的 `fetchDashboardStats`, `fetchCrawlerTargets` 等 `useEffect` 邏輯抽出。
    *   **預期模組**: `useAdminDashboard.ts` (純邏輯 Hook)。
2.  **`enduser-ui-fe/src/pages/ManagerNexus.tsx` (總計 1510 行)**
    *   **提取目標**: 將 `mockData` 與過於冗長的資料過濾迴圈抽離。
    *   **預期模組**: `useManagerNexusStats.ts` (純邏輯 Hook)。
3.  **`archon-ui-main/src/features/rag-settings/index.tsx` (總計 2411 行)**
    *   **提取目標**: 將內部過於龐大的狀態管理 (`useState` 海) 抽成 Context 或 Hook。
    *   **預期模組**: `useRagSettingsData.ts`。

---

## 標的 2. 前端表單配置化 (Config-Driven UI 降維打擊)

透過 `grep` 分析這 3 個表單重災區，我們取得以下精確的表單元件數量。這些將是我們轉換為「設定檔迴圈驅動 (`fields.map(...)`)」的明確標的：

1.  **`AdminPage.tsx`**:
    *   精確包含 **14 個** `<input>`, `<textarea>`, `<select>` JSX 元件。
    *   **重構行動**: 刪除這 14 個手寫的 JSX 標籤，改用 1 組設定檔驅動的陣列綁定。
2.  **`rag-settings/index.tsx`**:
    *   精確包含 **17 個** `<input>` 與 `<Select>` JSX 元件。
    *   **重構行動**: 透過 Map 迴圈渲染。
3.  **`rag-settings/components/CodeExtractionSettings.tsx`**:
    *   精確包含 **8 個** `<Input>` 與 `<input>` JSX 元件。
    *   **重構行動**: 透過 Map 迴圈渲染。

**總計可以銷毀 39 個重複編寫的 Input JSX 獨立節點。**

---

## 標的 3. 後端重複邏輯降維打擊 (BaseRepository 與 Pydantic)

分析 `python/src/server` 揭示了巨大的重複錯誤處理樣板 (Boilerplate)：

1.  **冗餘的錯誤回傳 (`if not success:`)**:
    *   單單在 `projects_api.py` 中，就出現了高達 **24 次** 的 `if not success: raise HTTPException(...)`。
    *   **重構行動**: 建立 `BaseRepository.execute_or_404()`，不再讓 Router 層手動判斷 `response.error`。
2.  **手動的 HTTPException 觸發**:
    *   **整個 `api_routes` 目錄下**，手動編寫的 `raise HTTPException(status_code=...)` 總共出現了 **262 次** (以全目錄字串搜尋計算而得)。
    *   **重構行動 (註記：目前決議跳過實作)**: 原定將業務邏輯拋出的錯誤改為內建 Exception，並於 FastAPI 註冊 Global Exception Handler。但為控制本次重構風險，此項目**暫緩實作**。
    *   這樣未來可以直接刪除 Router 層中高達 200 多行的錯誤轉換代碼。
    
---

## 結論與執行 SOP (「日常修改 -> 驗證」)

上述計畫**不會**採用「停機重構」的模式，共計 **3 個具體方向**，將融入接下來的每一個任務中：

1.  **遇到表單需求 (Feature)** -> 先將該頁面那 **14~17個** Input 轉成 Config-Driven -> `make lint-fe` -> 再加新欄位。
2.  **遇到 API 需求 (Feature)** -> 先把同一個 Router 裡的 `if not success:` 洗掉，改用 Global Exception 或 Repository 封裝 -> `make test-be` -> 再寫新 API。
3.  **遇到大型頁面 (Feature)** -> 先把頁面頂端的 `useEffect` 抽出為 `useXxx` Hook -> `make lint-fe` -> 再修復 UI Bug。

---

## 實作修復日誌 (Refactoring Log)
> 紀錄重構過程中所遇到的問題與解法，作為未來參考。

- **[2026-03] 初始化日誌**：依據真實數據啟動重構，確保「不造輪子、精準修復」。
- **[2026-03] AdminPage 降維打擊**：
    - **問題**：`AdminPage.tsx` 原本 923 行，內部嵌套宣告了 6 個大型 Component（如 `SystemSettings`, `CrawlerTargetManager` 等），導致狀態散落與 JSX input 重複 12 次。
    - **解法**：建立 `useAdminDashboard.ts` 集中管理所有 `api.*` 的提取與狀態（Loading/Saving/Error）。建立 `ConfigDrivenInput.tsx` 統包 `<input>`/`<select>`/`<textarea>` 渲染，消除所有手動標籤。
    - **結果**：`AdminPage.tsx` 從 923 行縮減至 ~380 行。成功將 12 個 raw input JSX 降為 0，改由 ConfigDrivenInput 透過陣列設定檔驅動。
- **[2026-03] ManagerNexus 瘦身**：
    - **問題**：`ManagerNexus.tsx` 龐大達 1510 行，前 280 行皆是資料獲取與狀態維護（包含 10 多個 state variables 與 API handlers），混雜在視圖層中。
    - **解法**：建立 `useManagerNexusStats.ts` 純邏輯 Hook，抽離所有 `api.get*` 等狀態及 `handleApprove*` 相關動作。
    - **結果**：原組件行數減少近 300 行，將核心邏輯封裝並成功通過型別檢查，確保元件專注於 UI 切換邏輯。
- **[2026-03] RAG Settings 巨石元件拆解**：
    - **問題**：`rag-settings/index.tsx` 長達 2351 行，包含所有的 Ollama 連線狀態追蹤、憑證快取、定時去 polling instance health 的巨大 Side Effects 以及 11 個需要維護的設定欄位。
    - **解法**：透過腳本抽離 line 15 到 1168 所有業務範圍為 `useRagSettingsData.ts`。同時將 `ProviderModelMap`、`colorStyles` 等 Type & Const 一併遷移。
    - **結果**：`index.tsx` 從 2351 行一次銳減破千行，讓視圖 (View) 與領域狀態邏輯 (Model) 給予明確的分野。
