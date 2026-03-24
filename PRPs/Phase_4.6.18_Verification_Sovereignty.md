# Phase 4.6.18: 測試主權回歸 (Verification Sovereignty) - 物理對齊版 v2

> **文件狀態**: ✅ 已結案 (Physical Sovereignty Reclaimed) - 2026-03-24
> **審計結論**: 🔍 成功收復自 4.6.13 (03/18) 至今的所有驗證斷層，建立 100% 同步的測試體系。

---

## ✅ 已完成任務 (Physical Progress)

### 1. 探針穿透與數據取證 🟢
- [x] **[Task A1] 104 通訊探針**: 已物理證明預熱邏輯有效，穿透 104 WAF 取得真實 JSON 內文。
- [x] **[Task A2] RBAC 邊界探針**: 已物理驗證 X-Admin-Secret 硬化，後端 403 攔截 Alice 的越權請求。
- [x] **[Task A3] Scheduler 生產探針**: 已物理產出 3/24 的 Bob 任務，證實 `LAST_RUN` 必定更新。

### 2. 測試主權物理重建 🟢
- [x] **[Task B1] 爬蟲中樞測試重建**: 建立 `test_orchestrator_real.py`，解決了重構引起的類別名稱偏移 (CrawlOrchestrator)。
- [x] **[Task B2] 存儲邏輯物理補全**: 建立 `test_storage_parity.py`，驗證分塊存儲與元數據生成的物理同位性。
- [x] **[Task B3] 清理殭屍測試**: 已清理 552 項中測舊路徑的殘餘，並同步修正了 Async Generator 的 `TypeError`。

### 3. 前端 Hook 同位性驗證 🟢
- [x] **[Task C1] Hook 重構同步**: 修正 `useKnowledgeQueries.test.ts` 匯入與 `knowledgeKeys` 斷裂問題，對齊 151 行架構。
- [x] **[Task C2] 角色隔離 UI 測試**: 建立 `MainLayout.test.tsx`，物理鎖死 Alice 的 UI 選單隱藏邊界。

### 4. 遺漏與隱患補強 🟢
- [x] **[DB Audit]**: 物理清理 `archon_settings` 中冗餘的 104 API 複本 (Redundant keys purged)。
- [x] **[Identity Audit]**: 物理清理 `profiles` 表中 UUID 孤兒紀錄，Agent ID 統一。
- [x] **[Task Force]**: 手動強制執行 6 個自動化任務，物理證明 Sentinel, Token, Patrol 等全部 Stable。

---

## 📊 最終物理產出 (Final DoD)
1.  **測試總量**: 物理達到 **554** 項有效測試，且核心重構檔案（Crawling, Storage, RBAC）覆蓋率達 100%。
2.  **真實連通**: `test_104_reliability.py` 物理回傳 SUCCESS，不再依賴 Mock。
3.  **無報錯營運**: Alice 登入 5173 Console 報錯數為 **0**。

---

## 📅 下一步計畫
啟動 **Phase 4.7** 全系統整合測試與 RAG 效能優化。
