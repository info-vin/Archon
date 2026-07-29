# Phase 5.9.27: Global SSOT Eradication & Hardcoding Cleanup

## 1. 目標 (Goal)
此階段旨在徹底根除系統中殘留的硬編碼 (Magic Numbers)，特別是與「排程時間」、「輪詢間隔」及「API 節流延遲」相關的參數，並將其全數提煉至 `SettingsService` 的 Pydantic Schemas 中，以達成真正的 100% SSOT (Single Source of Truth)。

依據指揮官指示：**統一抽離，拒絕硬編碼，並以自動化驗證取代手動確認。**

## 2. 異動範圍 (Scope of Changes)

### 2.1 Configuration Layer (SSOT 定義)
- **`settings.py`**:
  - `SchedulerConfig`: 新增 `alice_auto_fetch_hour`, `alice_auto_fetch_minute`, `alice_auto_fetch_days`, `token_analysis_hour`, `token_analysis_minute`, `business_sentinel_hour`, `business_sentinel_minute`, `monthly_summary_day`, `monthly_summary_hour`, `monthly_summary_minute`, `maintenance_audit_hour`, `maintenance_audit_minute`, `maintenance_audit_days` 等全域設定。
  - `EnrichmentConfig`: 新增 `enrichment_api_delay_long` 與 `enrichment_api_delay_short`。
  - `SystemTaskConfig` (全新建立): 集中管理 `background_cleanup_interval_secs`, `background_error_retry_secs`, `embedding_process_delay_secs`。

### 2.2 Service Layer (邏輯重構)
- **`scheduler_service.py`**:
  - 徹底移除 210-228 行中所有的硬編碼 Cron 觸發器，改由 config 取代。
- **`background_task_manager.py`**:
  - 初始化時掛載 config，以取代寫死的 300 秒與 60 秒輪詢。
- **`enrichment_service.py`**:
  - 引用 `EnrichmentConfig`，消除寫死的 3.0 與 1.5 秒延遲。
- **`contextual_embedding_service.py`**:
  - 引用 `SystemTaskConfig`，消除寫死的 15 秒阻塞延遲。

## 3. 驗證計畫 (Automated Verification)
本階段拒絕盲目的樂觀路徑與手動測試，將依賴以下的自動化公證門禁：
1. `uv run mypy src/server/`: 確保所有 config 新增的屬性與引用皆型別安全。
2. `make lint-be`: 確保代碼風格不受破壞。
3. `make test-be`: 確保重構未造成測試案例 (特別是 scheduler 與 background tasks 相關) 斷層與崩潰。
