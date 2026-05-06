---
name: "PRP Phase 4.2.2 Hotfix: Architecture Realignment & Mock Removal"
description: "基於 Git 歷史數據分析，根除 `api.ts` 中的架構違規與 Mock 殘留，並修復基礎設施層的連線問題。"
status: "Completed"
created_at: "2026-01-07"
completed_at: "2026-01-09"
---

## 1. 數據統計與根因分析 (Data Statistics & Root Cause Analysis)

### 1.1 Git Log 歷史數據 (2026/01/01 - Present)
根據 `git log` 分析，以下是導致系統不穩定的熱區：

| 檔案路徑 | 修改次數 | 症狀與意義 |
| :--- | :--- | :--- |
| **`enduser-ui-fe/src/services/api.ts`** | **7 次** | **重災區**。反覆引入與修改 "Smart Fallback", "Proactive Guard" 邏輯。這代表團隊試圖在前端解決基礎設施連線問題，導致代碼極度複雜化。 |
| `PRPs/*.md` (各類計畫文件) | **13 次** | 規劃變更頻繁 (4.0 -> 4.1 -> 4.2 -> 4.2.2)，導致實作一直處於追趕狀態。 |
| `python/src/server/services/agent_service.py` | **4 次** | 配合前端的自癒邏輯進行修改，增加了後端偶合。 |

### 1.2 根因診斷 (Root Cause Diagnosis)
系統目前處於「精神分裂」狀態的根本原因：
1.  **架構違規**: 在 `api.ts` 中實作了本該屬於 Infrastructure 的連線判斷邏輯。
2.  **掩耳盜鈴**: `Smart Fallback` 機制掩蓋了真實的網路配置錯誤。
3.  **測試環境汙染 (新增)**: `vite.config.ts` 未排除 E2E 目錄，導致單元測試環境下執行 E2E 腳本，引發 Mock 缺失導致的連線錯誤。
4.  **無狀態模擬 (新增)**: E2E Mock 為純靜態，無法驗證「新增後顯示」等需要狀態連動的流程。

### 1.3 依賴掃描與驗證 (Dependency Scan & Verification)
... (保持原樣)

---

## 2. 受影響檔案列表 (Impacted Files List)

| 檔案 | 修改目的 | 風險/連動 |
| :--- | :--- | :--- |
| `src/services/api.ts` | 移除 Mock 資料與 Fallback 邏輯。 | 高。 |
| `vite.config.ts` | 在 `test.exclude` 中加入 `tests/e2e/**`。 | 中。 |
| `src/pages/MarketingPage.tsx` | 加入 `document` 存在性檢查，防止測試拆除報錯。 | 低。 |
| `tests/e2e/e2e.setup.tsx` | 實作 `vi.hoisted` 狀態化 Mock Store。 | 中。 |
| `tests/e2e/sales-intelligence.spec.tsx` | 修正斷言以符合真實 UI 錯誤訊息與 Mock 資料。 | 低。 |
| `src/components/TaskModal.test.tsx` | 修正 `onTaskCreated` 斷言。 | 低。 |

---

## 3. 行動指令 (Action Instructions)

### Step 1: 基礎設施與測試環境矯正
- **指令**: 修改 `vite.config.ts` 排除 E2E 目錄。
- **目標**: 確保單元測試與 E2E 測試環境互不干擾。

### Step 2: 程式碼外科手術
- **指令**: 清理 `api.ts`，並修復 `MarketingPage` 異步 Bug。

### Step 3: 測試架構重整 (Test Refactoring)
- **指令**: 使用 `vi.hoisted` 在 `e2e.setup.tsx` 建立 stateful mock。

---

## 4. 驗收標準與結果 (Acceptance Criteria & Results)

| 驗收項目 | 預期行為 | 實際結果 |
| :--- | :--- | :--- |
| **環境變數檢查** | 瀏覽器不應看到內部 DNS 字串。 | **[通過]** 經查 URL 已正確指向外部實體。 |
| **API 行為 (正常)** | Dashboard 顯示資料庫真實任務。 | **[通過]** 移除 Fallback 後，資料連線行為透明化。 |
| **API 行為 (異常)** | 顯示誠實的錯誤提示。 | **[通過]** 測試確認連線失敗時正確顯示 Error UI。 |
| **單元與 E2E 測試** | `make test` 全數通過。 | **[通過]** 前端 26 個、後端 480 個測試全數通過。 |
| **代碼清潔度** | `api.ts` 顯著減少。 | **[通過]** 成功移除約 150 行 Mock 相關 Dead Code。 |
