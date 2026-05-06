# PRP: Phase 4.6.16 - 技術債清償與大型檔案精煉 (Technical Debt Liquidation)

> **狀態**: ✅ 結案 (物理驗證通過)
> **日期**: 2026-03-24
> **目標**: 清償 4.6 系列積累的巨型檔案債務。透過職責拆分（SRD），將前端與後端核心服務檔案控制在 250 行以下的健康水平，提升系統穩定性與開發效率。

## 1. 核心精煉目標 (The Big 2)

### A. 前端：`useKnowledgeQueries.ts` (797 行 ➔ 151 行) ✅
*   **物理成果**: 成功將職責解耦為 4 個模組，主檔案縮減 **81.1%**。
*   **驗證**: `pnpm tsc` 通過，`make lint` 通過。

### B. 後端：核心服務職責拆分 (SRD) ✅
1.  **`source_management_service.py`** (**688 行 ➔ 198 行**)
    *   **模組化**: 邏輯下沉至 `logic/ai_metadata.py` 與 `logic/storage_ops.py`。
    *   **對齊**: 100% 還原 LLM Prompt 完整度與 Logfire 追蹤標籤。
2.  **`scheduler_service.py`** (**686 行 ➔ 126 行**)
    *   **模組化**: Job 實作遷移至 `jobs/` 目錄（Patrol, Business, Dispatcher）。
    *   **對齊**: 還原 7 天重複 Alert 防禦、GAP-029 監控、與強健的 `LAST_RUN` 持久化。

## 2. 品質加固清單 (Quality Checklist)
- [x] **Task A Refactoring**: 物理行數縮減 81.1%，類型安全驗證通過。
- [x] **Task B Refactoring**: 兩大核心服務均縮減至 200 行以下，平均縮減率 78%。
- [x] **Atomic Parity**: 物理對比 HEAD 版本，確保日誌、提示詞、錯誤字串 100% 一致。
- [x] **Zero-Lint**: 後端 `make lint-be` 達成 Zero-Error，修復了 E701 與型別註解。
- [x] **Test Integrity**: 552 項後端測試通過，特別修正了 `clockwork_patrol` 的 Mock 鏈條。
- [x] **Docker Health**: 全系統 5 個服務物理運作正常，解決了啟動時的 Job 競爭問題。

## 3. 實施里程碑 (Milestones)

| 里程碑 | 描述 | 狀態 | 驗證指標 |
| :--- | :--- | :--- | :--- |
| **M1** | [前端] 隔離 Keys 與執行讀寫拆分 | ✅ | 檔案數 1 ➔ 4。 |
| **M2** | [後端] SourceManagement 邏輯解耦 | ✅ | 主檔案 198 行，AI/DB 職責分離。 |
| **M3** | [後端] Scheduler 插件化重構 | ✅ | 引擎與 Job 實作物理隔離。 |
| **M4** | 原子級對齊與時序加固 | ✅ | 解決 Docker Unhealthy 與功能孤兒問題。 |
| **M5** | 結案與推送 | ✅ | Git Push 完成。 |

## 4. 物理對齊總結 (Grounded Parity)
*   **不遺漏原則**: 透過與原始 HEAD 版本的逐行比對，成功找回並補完了 12 處細節邏輯偏差。
*   **穩定啟動**: 修正了 Job 啟動時序，確保 Docker Health Check 物理穿透。
