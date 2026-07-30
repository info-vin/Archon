# Phase 5.9.33: Auth & RBAC Hardcoding Cleanup & DRY Refactoring

## 目標 (Goal)
針對 `3.4 Auth 與細粒度 RBAC` 子網域中的 `auth_service.py` 與 `rbac_service.py` 進行重構，徹底消除 DRY 違規與硬編碼 (Hardcoding) 問題。

## 診斷結果 (Diagnosis)
1. **DRY 違規**: `auth_service.py` 與 `rbac_service.py` 中有大量直接呼叫 `supabase_client.table(...).execute()` 的零散邏輯與重複的 `try-except` 區塊，未善用 `BaseRepository.execute_query`。
2. **硬編碼與 SSOT 違規**: `rbac_service.py` 中的 `get_restricted_mcp_tools` 方法，將限制的 MCP 工具清單 (如 `{"delete_project", "execute_sql"}`) 寫死為字串陣列，違反 `Model SSOT` 原則。

## 執行計畫 (Execution Plan)
- [x] 重構 `auth_service.py`: 繼承或使用 `BaseRepository.execute_query` 統一例外捕捉機制。
- [x] 重構 `rbac_service.py`: 拔除寫死的工具清單。
- [x] 更新 `migration/0.2.3/05_seed_system_configs.sql`: 新增 `MCP_RESTRICTED_BASE`, `MCP_RESTRICTED_MARKETBOT` 等設定鍵值至資料庫。
- [x] 修補 `scripts/phase_audit.py`: 強化 `ssot_hardcoding_audit` 函式，使其能偵測到 `{...}` 字串陣列的硬編碼盲點。
- [x] 執行公證 (Verification): 透過 `make lint-be` 與 `make test-be` 驗證零副作用。

## 狀態 (Status)
- 程式碼重構與測試已全數完成。
- **注意**: 資料庫層面的更新尚未執行（因缺乏有效連線憑證），需手動至 Supabase 執行 SQL 或透過 Reset DB 載入。
