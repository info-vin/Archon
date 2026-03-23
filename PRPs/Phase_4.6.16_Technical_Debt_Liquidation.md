# PRP: Phase 4.6.16 - 技術債清償與大型檔案精煉 (Technical Debt Liquidation)

> **狀態**: 🏗️ 規劃中 (待啟動)
> **日期**: 2026-03-23
> **目標**: 清償 4.6 系列積累的巨型檔案債務。透過職責拆分（SRD），將前端與後端核心服務檔案控制在 500 行以下的健康水平，提升系統穩定性與開發效率。

## 1. 核心精煉目標 (The Big 2)

### A. 前端：`useKnowledgeQueries.ts` (797 行 ➔ 250 行)
*   **現狀**: Query 與 Mutation 高度耦合，樂觀更新邏輯過重。
*   **重構路徑**:
    1.  **`knowledgeKeys.ts`**: 存放靜態 `knowledgeKeys` (預計 +50 行)。
    2.  **`knowledgeOptimistic.ts`**: 抽離 `matchKnowledgeFilter` 與緩存 Updater 函數 (預計 +150 行)。
    3.  **`useKnowledgeMutations.ts`**: 存放所有數據變更 Hook (預計 +350 行)。
*   **驗證**: `pnpm tsc --noEmit` & `pnpm vitest`。

### B. 後端：`crawling_service.py` (732 行 ➔ 430 行)
*   **現狀**: 編排邏輯 (Orchestration) 與進度追蹤、策略調度混合。
*   **重構路徑**:
    1.  **`handlers/orchestration_helper.py`**: 抽離 `_async_orchestrate_crawl` 內部的進度映射與 Heartbeat (預計 +200 行)。
    2.  **`handlers/url_type_detector.py`**: 隔離 URL 類型檢測與相應分發邏輯 (預計 +100 行)。
*   **驗證**: `mypy` & `make test-be` (544+ 測試通過)。

## 2. 品質加固清單 (Quality Checklist)
- [ ] **Lint Zero-Warning**: 修復 `archon-ui-main` 中的 `react-hooks/exhaustive-deps` 警告。
- [ ] **Type Safety**: 確保拆分後無 `Import not found` 或型別斷裂。
- [ ] **Refactoring Parity**: 重構後的代碼行數必須物理對比並記錄。

## 3. 實施里程碑 (Milestones)

| 里程碑 | 描述 | 驗證指標 |
| :--- | :--- | :--- |
| **M1** | 隔離靜態定義與純函數 | `tsc` 與 `mypy` 通過。 |
| **M2** | 執行 Hook 與 Service 職責拆分 | 整合測試 100% 通過。 |
| **M3** | 最終品質清掃與結案 | `make lint` 無任何報錯。 |

## 4. 拒絕樂觀路徑：風險防範 (Risk Mitigation)
*   **循環引用**: Mutations 引用 Queries 導致編譯失敗。**[對策]**: 嚴格統一引用 `knowledgeKeys.ts`。
*   **快取實體斷裂**: 手動更新 `queryClient` 時結構不對齊。**[對策]**: Updater 函數強制使用 TypeScript 型別斷言。
