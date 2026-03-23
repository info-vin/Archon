# PRP: Phase 4.6.15 - Agent XP 進化與 Token 成本透明化 (Grounded Transparency)

> **狀態**: ✅ 結案 (物理驗證通過)
> **日期**: 2026-03-23
> **目標**: 將 Agent 的運算價值物理化。實作 Agent 排行榜、XP/Level 系統與 Token 成本追蹤，實現基於數據的 ROI 透明管理。

## 1. 核心開發任務

### A. 實體 XP 評分系統 (Physical Scoring)
*   **評分指標**: `StatsService.py` 中的 `calculate_ai_score` 物理包含 `word_count`, `returncode`, `lint_passed`。
*   **獎勵機制**: 實作 `add_agent_action_log` 以在 `archon_logs` 紀錄 Agent 的貢獻。
*   **XP 歸屬**: 成功從 `profiles` 表中將 Agent 的 UUID 關聯到顯示名稱 (Display Name)。

### B. Token 經濟治理 (Economic Governance)
*   **動態定價**: 透過 `TOKEN_PRICING_JSON` 配置模型定價。
*   **成本透明**: 在 `TokenUsageService.py` 中實作「運算貢獻獎勵」，每模型調用獎勵 1 XP。
*   **ROI 聚合**: 修改 `StatsService.get_agent_xp_stats`，實現了「累計消耗金額」與「累計 XP」的後端 SSOT 聚合。

### C. 視覺化標籤 (Visual Badging)
*   **Token 成本標籤**: 在 `SystemHealthDashboard.tsx` 實作了四色標籤（LOW POWER / STANDARD / HIGH PERF / WATCHLIST）。
*   **Agent 排行榜**: 依據 `total_xp` 降序排列，實體呈現 ROI 指標。

## 2. 三向對齊驗證 (Physical Parity)
1.  **AGENT_CONFIG** ➔ 物理映射 UUID。
2.  **Profiles** ➔ 建立 `06_seed_agent_profiles.sql` 完成實體身分注入。
3.  **StatsAPI** ➔ 100% 通過 Mypy 型別檢查與 Pytest 邏輯驗證。

## 3. 完工清單
- [x] 補齊 `StatsService.get_agent_xp_stats` 中的 `total_cost` 物理聚合邏輯 (Backend)。
- [x] 實作 `SystemHealthDashboard.tsx` 中的「資源消耗動態標籤」 (Frontend)。
- [x] 物理驗證：通過 `make lint` 與 `make test-be` (544+ tests)。

## 4. 物理查核結論與大型檔案重構計畫

本階段稽核發現 `useKnowledgeQueries.ts` (**797 行**) 已達系統維護臨界值。以下為本階段產出之**物理重構實施計畫**，旨在下個階段立即啟動：

### A. 拆分目標架構 (Refactored State)
將巨型檔案拆分為以下 4 個具備單一職責 (Single Responsibility) 的模組：
1.  **`knowledgeKeys.ts` (~50行)**: 靜態存放所有 Query Keys 定義。作為全特徵的最底層依賴，物理切斷循環引用。
2.  **`knowledgeOptimistic.ts` (~150行)**: 抽離 `matchKnowledgeFilter` (輔助函數) 與樂觀更新的快取操作邏輯。轉為**純函數 (Pure Functions)**，支持 100% 脫離 React 的單元測試。
3.  **`useKnowledgeQueries.ts` (~250行)**: 僅保留 `useKnowledgeSummaries`, `useKnowledgeChunks`, `useCodeExamples` 等讀取 Hooks。
4.  **`useKnowledgeMutations.ts` (~350行)**: 集中管理 `useCrawlUrl`, `useUploadDocument`, `useDeleteSource` 等變更 Hooks。

### B. 實施里程碑與驗證步驟 (Milestones & Validation)

#### Milestone 1: Keys 隔離與引用對齊
*   **動作**: 建立 `knowledgeKeys.ts`，並使用 `replace` 更新全專案 6 個引用路徑。
*   **驗證**: 執行 `pnpm tsc --noEmit`。若無 `Import not found` 錯誤，即視為 M1 物理通過。

#### Milestone 2: 邏輯下沉與測試化
*   **動作**: 將樂觀更新邏輯與 `matchKnowledgeFilter` 移至 `knowledgeOptimistic.ts`。
*   **驗證**: 建立新測試檔 `knowledgeOptimistic.test.ts`，物理驗證過濾邏輯在不同 `KnowledgeItemsFilter` 下的正確性。

#### Milestone 3: 讀寫分離 (The Final Split)
*   **動作**: 建立 `useKnowledgeMutations.ts`，將 Mutation Hooks 從原檔案中物理移除。
*   **驗證**: 
    - 執行 `make lint` 確保風格一致。
    - 執行 `pnpm vitest useKnowledgeQueries.test.ts`。由於 Keys 與邏輯已隔離，整合測試必須在「零修改測試代碼」的情況下通過。

### C. 數據誠實性與連通性
*   **掃描發現**: 3/18 以前的歷史數據存在 `user_id: None` 缺失。
*   **實施成果**: 透過 `06_seed_agent_profiles.sql` 物理注入 Agent 實體，3/23 以後的 ROI 計算已達成後端 SSOT， Poisson Gate 權限系統正式物理掛載並通過 Pytest 驗證。

## 5. 驗證清單 (Final Assertions)
- [x] **SSOT 驗證**: 後端 `/api/stats/agent-xp` 回傳值包含物理總成本。
- [x] **視覺驗證**: `SystemHealthDashboard` 正確渲染四色 Token 標籤。
- [x] **品質驗證**: `make lint` 達成 Backend Zero-Error。
- [x] **計畫固化**: 重構地圖已 100% 寫入 Phase 4.6.15，拒絕任何幻想與猜測。



