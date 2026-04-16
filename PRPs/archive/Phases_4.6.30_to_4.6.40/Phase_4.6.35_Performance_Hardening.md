# Phase 4.6.35: Performance Hardening (效能硬化與 N+1 消滅)

## 1. 物理斷層診斷
根據代碼審計，`task_service.py` 在建立任務並重新排序時，存在嚴重的 N+1 查詢陷阱：
- **現象**: 每移動一筆現有任務，就會發起一次額外的資料庫更新請求。
- **影響**: 若專案中有 100 筆任務，建立新任務會觸發 101 次 IO，造成前端嚴重卡頓。

## 2. 落地實作紀錄 (Physical Realization)
- **資料庫層**: 🟢 建立了 SQL Stored Procedure `increment_task_orders` (`migration/0.2.2/13_optimize_task_reordering.sql`)。
- **服務層**: 🟢 修正 `task_service.py`，將迴圈更新替換為單次 RPC 原子操作。

## 3. 驗證數據
- **單元測試**: `make test-be` 通過，共計 559 測項。
- **效能預期**: IO 次數由 O(N) 降至 O(1)。

## 4. 結案狀態
- **狀態**: 🟢 **100% 物理落地** (2026-04-10)
