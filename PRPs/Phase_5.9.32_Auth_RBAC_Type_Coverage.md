# Phase 5.9.32: Auth 與細粒度 RBAC 型別覆蓋率補強計畫

## 專案目標
將 `3.4 Auth 與細粒度 RBAC` 子網域的型別覆蓋率從 96.2% 提升至 **100%**。

## 診斷結果
透過執行 AST 型別掃描器，確認唯一未標註型別的函式為 `python/src/server/services/ethics_service.py` 內的 `__init__` 建構子。

## 執行步驟
1. 為 `EthicsService.__init__` 補上 `-> None` 標註。
2. 驗證 MyPy 型別安全。
3. 驗證 `scripts/backend_type_health.py` 動態計算分數。
