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
    *   整個 `api_routes` 目錄下，手動編寫的 `raise HTTPException(status_code=...)` 總共出現了 **262 次**。
    *   **重構行動**: 將業務邏輯拋出的錯誤一律改為 Python 內建 Exception (如 `ValueError`, `PermissionError`)，並在 FastAPI 入口處 (如 `main.py`) 註冊 Global Exception Handler 統一攔截並轉換為 400/404/500。
    *   這樣可以直接刪除 Router 層中高達 200 多行的錯誤轉換代碼。
    
---

## 結論與執行 SOP (「日常修改 -> 驗證」)

上述計畫**不會**採用「停機重構」的模式，共計 **3 個具體方向**，將融入接下來的每一個任務中：

1.  **遇到表單需求 (Feature)** -> 先將該頁面那 **14~17個** Input 轉成 Config-Driven -> `make lint-fe` -> 再加新欄位。
2.  **遇到 API 需求 (Feature)** -> 先把同一個 Router 裡的 `if not success:` 洗掉，改用 Global Exception 或 Repository 封裝 -> `make test-be` -> 再寫新 API。
3.  **遇到大型頁面 (Feature)** -> 先把頁面頂端的 `useEffect` 抽出為 `useXxx` Hook -> `make lint-fe` -> 再修復 UI Bug。
