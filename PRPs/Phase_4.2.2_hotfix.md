---
name: "PRP Phase 4.2.2 Hotfix: Architecture Realignment & Mock Removal"
description: "基於 Git 歷史數據分析，根除 `api.ts` 中的架構違規與 Mock 殘留，並修復基礎設施層的連線問題。"
status: "Draft"
created_at: "2026-01-07"
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
1.  **架構違規**: 在 `api.ts` 中實作了本該屬於 Infrastructure (Docker/Nginx) 的連線判斷邏輯 (`createSmartApi`)。
2.  **掩耳盜鈴**: `Smart Fallback` 機制在後端連線失敗時自動切換回 Mock，掩蓋了真實的網路配置錯誤 (如 Docker 內部 URL 無法解析)。
3.  **環境不一致**: 前端在 `make dev` (Local) 與 `make dev-docker` (Container) 拿到不一致的 `SUPABASE_URL`。

### 1.3 依賴掃描與驗證 (Dependency Scan & Verification)
經過 `grep` 與代碼審查，確認以下依賴狀況：

*   **Mock 汙染範圍**: `MOCK_` 與 `mockApi` 變數僅存在於 `enduser-ui-fe/src/services/api.ts`，未擴散至 UI 元件。
*   **測試依賴**:
    *   `TaskModal.test.tsx`, `DashboardPage.test.tsx`, `e2e.setup.tsx` 使用 `vi.mock` 模擬了 API 層。
    *   **結論**: 只要 `api.ts` 保持公開介面 (Public Interface) 不變，這些測試**不會**因為移除內部 Mock 實作而崩潰。
*   **例外**: `enduser-ui-fe/src/services/api.stability.spec.ts` 專門用於測試 "Smart Fallback" 邏輯。由於該邏輯將被移除，此測試檔已無存在必要。

---

## 2. 受影響檔案列表 (Impacted Files List)

本次 Hotfix 將觸及以下檔案。所有修改必須聯動考慮。

### A. 核心邏輯層 (Core Logic)
| 檔案 | 修改目的 | 風險/連動 |
| :--- | :--- | :--- |
| `enduser-ui-fe/src/services/api.ts` | **移除**所有 `MOCK_` 資料、`mockApi` 物件、`createSmartApi` 邏輯。**保留**純粹的 `supabaseApi`。 | **高**。這會直接導致原本依賴 Mock 的頁面在後端未啟動時報錯 (這是預期的)。 |
| `enduser-ui-fe/src/types.ts` | 清理可能殘留的僅供 Mock 使用的型別定義 (若有)。 | 低。 |

### B. 基礎設施層 (Infrastructure)
| 檔案 | 修改目的 | 風險/連動 |
| :--- | :--- | :--- |
| `docker-compose.yml` | 確保 `enduser-frontend` 服務注入正確的、瀏覽器可解析的 `VITE_SUPABASE_URL` (應為 `http://localhost:8181` 或公開 URL，而非內部 `supabase_kong`)。 | **中**。需重啟容器驗證。 |
| `enduser-ui-fe/vite.config.ts` | 檢查 Proxy 設定，確保 `/api` 請求正確轉發。 | 中。 |

### C. 測試層 (Tests)
| 檔案 | 修改目的 | 風險/連動 |
| :--- | :--- | :--- |
| `enduser-ui-fe/src/services/api.stability.spec.ts` | **刪除**。目前的測試是為了驗證 "Smart Fallback" 邏輯，該邏輯將被移除。 | **高**。確認無其他依賴後刪除。 |
| `enduser-ui-fe/src/components/TaskModal.test.tsx` | 確保測試使用 MSW 或 `vi.mock` 模擬 API，而非依賴 `api.ts` 內部的 Mock Data。 | 中。 |
| `enduser-ui-fe/tests/e2e/e2e.setup.ts` | 確認 E2E 測試的 Mocking 策略不依賴 `api.ts` 的 `useMockData` flag。 | 中。 |

---

## 3. 行動指令 (Action Instructions)

### Step 1: 基礎設施矯正 (Infrastructure Fix)
- **指令**: 檢查並修改 `docker-compose.yml`。
- **目標**: 確保傳遞給前端的環境變數是「外部可訪問」的 (External Reachable)，而非 Docker 內部 DNS。

### Step 2: 程式碼外科手術 (Code Surgery)
- **指令**: 修改 `enduser-ui-fe/src/services/api.ts`。
- **細節**:
    1.  刪除 `const MOCK_...` 所有變數。
    2.  刪除 `const mockApi = { ... }` 定義。
    3.  刪除 `createSmartApi` 函式。
    4.  將 `supabaseApi` 直接改名為 `api` 並 export。
    5.  確保所有 `fetch` 呼叫都有基本的錯誤處理 (throw Error if !response.ok)。

### Step 3: 測試適配 (Test Adaptation)
- **指令**: 刪除 `enduser-ui-fe/src/services/api.stability.spec.ts`。
- **理由**: 該檔案包含針對 `SmartAPI` 和 `isFallbackMode` 的單元測試。隨著這些邏輯被移除，這些測試將變得無效且無法通過。刪除它是維護測試套件健康的必要步驟。

---

## 4. 驗收標準與結果 (Acceptance Criteria & Results)

| 驗收項目 | 預期行為 | 實際結果 (待填) |
| :--- | :--- | :--- |
| **環境變數檢查** | 在瀏覽器 Console 輸入 `import.meta.env.VITE_SUPABASE_URL`，不應看到 `supabase_kong` 或 `archon_db` 等內部字串。 | [ ] |
| **API 行為 (正常)** | 啟動後端 (`make dev`)，前端 Dashboard 顯示資料庫中的真實任務。 | [ ] |
| **API 行為 (異常)** | 關閉後端 (`make stop`)，前端 Dashboard 應顯示紅色錯誤提示或 Toast，**而非**顯示假資料。 | [ ] |
| **單元測試** | `make test-fe` 通過 (排除 E2E 暫時的失敗)。 | [ ] |
| **代碼清潔度** | `api.ts` 檔案行數應顯著減少 (預計減少 100+ 行)，且無 Dead Code。 | [ ] |
