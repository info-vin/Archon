# Phase 5.9.10: SchedulerService L2 最終模組化與硬編碼淨化

> **狀態**: Planning
> **目標**: 完成 Phase 5.9.6 未竟的 L2 重構，將 `scheduler_service.py` 內部的基礎設施邏輯（DB 連線、硬編碼時區、幽靈狀態）徹底解耦。

## 1. 歷史考古與斷層發現 (Audit Findings)
正如您的精準指正，我在重新檢閱 `git log` 後確認了以下歷史：
- **Phase 5.9.6 (`91a71f89`)**: 已經成功完成了第一階段的 L2 重構，將超過 370 行的 `business.py` 巨獸拆分為精簡的 `leads_patrol.py`, `sentinel_patrol.py` 等業務模組。
- **遺漏的技術債 (The Gap)**: 當時的重構範圍僅限於 `scheduler/jobs/*.py` 內的業務邏輯，**然而核心控制器 `scheduler_service.py` 本身並未被淨化**。

這導致 `scheduler_service.py` 目前仍存在三大違規：
1. **L2 模組化違規**: 檔案長達 398 行，且包含直接呼叫 `get_supabase_client().table(...).execute()` 的**裸資料庫操作 (Bare DB calls)**，破壞了 repository 隔離原則。
2. **硬編碼技術債**: `CronTrigger` 中的 `"Asia/Taipei"` 被四度硬編碼；`HF_SLEEP_START` 預設值 `"20:18"` 也被硬編碼。
3. **幽靈死碼 (Dead Code)**: 檔案開頭定義了 30 多行的 `is_hf_awake()` 邏輯，但在當前類別內**完全沒有被呼叫**（因為 Phase 5.5.10 的架構演進中，已被 Cron 取代，這段代碼成為歷史遺跡）。

## 2. 實作計畫 (Implementation Plan)

### A. 剝離裸資料庫操作 (Bare DB Calls)
- **目標**: `scheduler_service.py` (`_update_last_run`, `_get_last_run`)
- **行動**:
  1. 在 `settings_service.py` 中擴充 `set_setting(key: str, value: str)` 方法，並使用安全的 `BaseRepository.execute_query` 來封裝。
  2. 將 `scheduler_service.py` 內部所有的 Supabase 呼叫，改為呼叫 `SettingsService` 的 `get_setting` 與 `set_setting`。

### B. 清除死碼與重構配置 (Dead Code & Configuration)
- **目標**: `scheduler_service.py`
- **行動**:
  1. **刪除死碼**: 徹底刪除未使用的 `is_hf_awake()` 函數（共 33 行），立即幫檔案瘦身。
  2. **統一時區配置**: 在類別頂部宣告 `DEFAULT_TIMEZONE = ZoneInfo("Asia/Taipei")`，並全面取代散落各處的 `"Asia/Taipei"` 硬編碼。
  3. **統一防呆移除**: 確保 `_schedule_jobs` 內不再出現 `self._scheduler.remove_job(...)` 的硬編碼防呆，全面統一信任 `apscheduler` 的 `replace_existing=True` 參數。

## 3. 驗證計畫 (Verification)
- 執行 `make lint-be` (Ruff) 檢查是否完全清除了未使用的依賴 (`os`, `time` 等)。
- 執行 `make test-be` 確保 `scheduler_service.py` 的 DB 狀態鎖（`LAST_RUN` 機制）在切換至 `SettingsService` 後依舊 100% 正常運作。
