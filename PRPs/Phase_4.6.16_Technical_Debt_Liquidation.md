# PRP: Phase 4.6.16 - 技術債清償與大型檔案精煉 (Technical Debt Liquidation)

> **狀態**: 🏗️ 實作中 (Task A 已結案)
> **日期**: 2026-03-23
> **目標**: 清償 4.6 系列積累的巨型檔案債務。透過職責拆分（SRD），將前端與後端核心服務檔案控制在 500 行以下的健康水平，提升系統穩定性與開發效率。

## 1. 核心精煉目標 (The Big 2)

### A. 前端：`useKnowledgeQueries.ts` (797 行 ➔ 151 行) ✅
*   **物理成果**: 成功將職責解耦為 4 個模組，主檔案縮減 **81.1%**。
    1.  **`knowledgeKeys.ts`**: 靜態 Query Keys (22 行)。
    2.  **`knowledgeOptimistic.ts`**: 純函數過濾與 Updater 邏輯 (88 行)。
    3.  **`useKnowledgeMutations.ts`**: 數據變更 Hooks (411 行)。
    4.  **`useKnowledgeQueries.ts`**: 唯讀查詢 Hooks (151 行)。
*   **驗證**: `pnpm tsc` 通過，`make lint` 通過，`knowledgeOptimistic.test.ts` 100% 通過。

### B. 後端：`crawling_service.py` (732 行 ➔ 430 行) 🏗️
*   **現狀**: 編排邏輯 (Orchestration) 與進度追蹤、策略調度混合。
*   **重構路徑**:
    1.  **`helpers/rbac_rules.py`**: 遷移 `_get_role_based_max_depth` (預計 +40 行)。
    2.  **`handlers/url_type_router.py`**: 隔離 URL 類型檢測與分發邏輯 (預計 +120 行)。
    3.  **`handlers/orchestrator.py`**: 抽離 `_async_orchestrate_crawl` 內部的進度映射與 Heartbeat (預計 +200 行)。
*   **驗證**: `mypy` & `make test-be` (544+ 測試通過)。

## 2. 品質加固清單 (Quality Checklist)
- [x] **Task A Refactoring Parity**: 物理行數已對比並記錄。
- [x] **Task A Type Safety**: 100% 通過 `tsc --noEmit`。
- [ ] **Task B Refactoring Parity**: 待完成拆分後對比。
- [ ] **Lint Zero-Warning**: 修復 `archon-ui-main` 中的 `react-hooks/exhaustive-deps` 警告。

## 3. 實施里程碑 (Milestones)

| 里程碑 | 描述 | 狀態 | 驗證指標 |
| :--- | :--- | :--- | :--- |
| **M1** | [前端] 隔離 Keys 與純函數 | ✅ | `knowledgeKeys.ts` 建立。 |
| **M2** | [前端] 執行 Hook 讀寫拆分 | ✅ | `useKnowledgeMutations.ts` 建立。 |
| **M3** | [後端] 業務規則與路徑隔離 | 🏗️ | `rbac_rules.py` & `url_type_router.py`。 |
| **M4** | [後端] 核心編排器精煉 | ⏳ | `orchestrator.py` 建立。 |
| **M5** | 最終品質清掃與結案 | ⏳ | `make lint` 無任何報錯。 |

## 4. 拒絕樂觀路徑：風險防範 (Risk Mitigation)
*   **異步上下文風險**: 拆分 `orchestrate_crawl` 時，需確保 `CrawlingService` 的實體狀態在後台任務中正確保持。
*   **循環引用**: Mutations 引用 Queries 導致編譯失敗。**[對策]**: 嚴格統一引用 `knowledgeKeys.ts`。
*   **快取實體斷裂**: 手動更新 `queryClient` 時結構不對齊。**[對策]**: Updater 函數強制使用 TypeScript 型別斷言。
