# Phase 4.6.18: 測試主權回歸 (Verification Sovereignty) - 物理對齊版

> **文件狀態**: 🛠️ 執行中 (Active) - 2026-03-24
> **審計結論**: 🔍 發現自 4.6.13 (03/18) 至今，系統處於「代碼大重構、測試零更新」的幻覺狀態。

---

## 🔍 物理斷層診斷 (Physical Gap Analysis)

經過三向審計，確認以下核心功能自 03/18 至今處於「未經驗證」的高風險區：
1.  **爬蟲重構中樞 (Crawling Orchestrator)**: 原本 732 行邏輯已拆分至多個模組，但測試檔案 `test_crawling_service.py` 仍停留在舊架構，覆蓋率物理歸零。
2.  **資源存儲邏輯 (Source Management)**: 模組化後的 `storage_ops.py` 與 `ai_metadata.py` 物理上**完全沒有**任何對應的測試檔案。
3.  **前端巨型 Hook (useKnowledgeQueries)**: 縮編 80% 後，現有測試 `useKnowledgeQueries.test.ts` 仍在引用已被刪除/移動的舊 Hook (如 `useCrawlUrl`)。
4.  **104 數據真實性**: 爬蟲雖已修正預熱邏輯，但目前的後端測試 `test_job_board_service.py` 在無網路環境下會跳過真實驗證，導致「假性綠燈」。

---

## 🛠️ Phase 4.6.18 實施清單 (探針驅動版)

### 第一階段：探針穿透與數據取證 (Probe-First Verification)
- [ ] **[Task A1] 104 通訊探針**: 物理證明 `_fetch_job_detail` 的預熱邏輯能拿到 104 Session Cookie。
- [ ] **[Task A2] RBAC 邊界探針**: 使用 Alice 的實體 Token 強行呼叫 Admin API，驗證 403 攔截是否在**後端**物理生效（而非前端偽裝）。
- [ ] **[Task A3] Scheduler 生產探針**: 物理查詢資料庫，確保 6 個自動化任務在執行後**必定**更新 `LAST_RUN` 與產出實體 Task。

### 第二階段：測試主權物理重建 (Backend Reconstruction)
- [ ] **[Task B1] 爬蟲集成測試重建**: 為 `orchestrator.py` 與 `url_type_router.py` 撰寫實體測試，取代已失效的舊測試。
- [ ] **[Task B2] 存儲邏輯物理補全**: 針對 `source_management/` 目錄建立第一個物理測試檔 `test_storage_parity.py`。
- [ ] **[Task B3] 清理殭屍測試**: 物理刪除 552 項測試中，所有指向已刪除檔案或過時路徑的斷言。

### 第三階段：前端 Hook 同位性驗證 (Frontend Realization)
- [ ] **[Task C1] Hook 重構同步**: 修正 `useKnowledgeQueries.test.ts` 的匯入路徑，對齊 151 行的新架構。
- [ ] **[Task C2] 角色隔離 UI 測試**: 為 `MainLayout.tsx` 建立物理測試，斷言 `sales` 角色下 `Nexus/Approvals` 按鈕物理不存在於 DOM 中。

---

## ✅ 最終驗收標準 (No Fantasy Numbers)
1.  **物理覆蓋**: 03/18 至今變動的所有核心代碼檔案，其對應的測試檔案必須有當日的 Commit 紀錄。
2.  **探針結果**: `scripts/probe_*.py` 全部物理回傳 SUCCESS 狀態碼。
3.  **同位性 (Parity)**: 縮編後的 Hook 與 Service，其功能輸出與 03/18 原始版本物理一致。
