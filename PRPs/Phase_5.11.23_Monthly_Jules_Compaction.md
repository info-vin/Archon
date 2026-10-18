# Phase 5.11.23: 代理記憶指南 (.jules/*.md) 極簡化瘦身與月度自動壓縮排程 (2026-10-18)

## 📌 背景與動機 (Context & Motivation)
在審查最近一週的 `git log` 與 `.jules/*.md` 共 6 份代理記憶指南（`bolt.md`, `palette.md`, `type_guardian.md`, `contractor.md`, `reaper.md`, `qa.md`）時，我們發現了嚴重的「LLM 記憶退化與幻覺膨脹」現象：
1. **幻覺日期 (Date Hallucinations)**：檔案是在 2026-09~10 月由自動化代理寫入，卻因 LLM 預訓練權重偏差而大量標註 `2023-xx-xx`、`2024-05-xx`、`2025-xx-xx` 等虛構日期。
2. **無限追加與重複堆疊 (Append-Only Bloat)**：每次自動化重構 PR 都機械式往檔案尾端追加高度雷同的紀錄（例如 `type_guardian.md` 與 `contractor.md` 重複記載了數十次 `TypedDict` / `Pydantic` 替換），導致 6 份檔案膨脹至 **95 KB（558 行）**，消耗大量 Context Token 卻稀釋了核心規範的注意力權重。

本階段的核心目標：**將 `.jules/*.md` 轉型為「高密度極簡核心規則庫 (3~5 條/檔)」，並將「月度極簡化瘦身 (Monthly Jules Compaction)」納入 Clockwork 週期排程與 `make phase-audit` 門禁，永久杜絕記憶檔無限膨脹與幻覺日期污染。**

## 🎯 核心實作目標與三向連動 (Core Objectives)

### 1. `.jules/*.md` 實體極簡化瘦身 (Physical Compaction)
- **目標**：清理 `.jules/` 下全部 6 份 Markdown 檔案（`bolt.md`, `palette.md`, `type_guardian.md`, `contractor.md`, `reaper.md`, `qa.md`）。
- **實作**：移除所有虛構日期標題，合併重複教訓，每份檔案僅保留最精華的 **2~5 條核心工程鐵律**（總容量由 95 KB 降至 9.8 KB，減少 89.7%）。

### 2. SSOT 排程參數定義 (`SchedulerConfig`)
- **目標**：遵循專案 SSOT 鐵律，絕不在排程器或服務層硬編碼 Cron 時間或條目上限。
- **實作**：於 `python/src/server/schemas/settings.py` 的 `SchedulerConfig` 新增：
  - `monthly_jules_compaction_day: int = Field(default=1, alias="MONTHLY_JULES_COMPACTION_DAY")`
  - `monthly_jules_compaction_hour: int = Field(default=9, alias="MONTHLY_JULES_COMPACTION_HOUR")`
  - `monthly_jules_compaction_minute: int = Field(default=30, alias="MONTHLY_JULES_COMPACTION_MINUTE")`
  - `jules_max_entries_per_file: int = Field(default=5, alias="JULES_MAX_ENTRIES_PER_FILE")`

### 3. 獨立排程模組、API 觸發路由與狀態對齊 (`jules_compaction.py`, `SchedulerService`, API & Stats)
- **目標**：避免 `tech_debt_patrol.py` (315 行) 觸碰 360 行巨型檔案警戒線，建立職責單一的月度壓縮模組並完成全鏈路掛載。
- **實作**：
  1. 新增 `python/src/server/services/scheduler/jobs/jules_compaction.py`，實作 `run_monthly_jules_compaction(jules_dir: Path | None = None) -> dict[str, int]`：利用正規表達式剝除 `YYYY-MM-DD` 幻覺日期前綴、以正規化標題與內文去重、強制截斷保留前 `jules_max_entries_per_file` (預設 5) 條核心規則與標準編號 (`## 1. Title`)，並在完成後呼叫 `log_service.create_log_entry` 寫入 `archon_logs`。
  2. 於 `python/src/server/services/scheduler_service.py` Category 3 註冊 `monthly_jules_compaction`（每月 1 號 09:30 Asia/Taipei 執行）。
  3. 同步於 `python/src/server/api_routes/internal_api.py` 與 `python/src/server/api_routes/admin_api.py` 的 `job_map` 註冊 `"monthly_jules_compaction"`，並於 `python/src/server/services/stats/__init__.py` 正規化 `_catchup` 與 `_recurring` 後綴。

### 4. `make phase-audit` Step 11 實體守門員 (`scripts/phase_audit.py`)
- **目標**：防止未來自動化 PR 再次塞入幻覺日期或超過 5 條規則。
- **實作**：於 `scripts/phase_audit.py` 新增 `jules_guidelines_audit()` (Step 11)，強制掃描 `.jules/*.md` 確保每檔 `<= 5` 條規則且 `0` 幻覺日期前綴。

## 🛡️ 物理公證防線 (Zero Fake Verification)
- **真實檔案讀寫測試 (No Fake Mocks)**：在 `python/tests/unit/services/test_scheduler_service.py` 中，使用 Pytest 實體 `tmp_path` 建立含有幻覺日期 (`## 2024-05-18 - Rule`)、重複段落與 8 條規則的 `.md` 檔案，直接呼叫 `run_monthly_jules_compaction(jules_dir=tmp_path)`，讀取磁碟實體檔案驗證日期剝除、去重、數量上限（`<= 5`）、`log_service.create_log_entry` 稽核紀錄與二次執行冪等性 (`files_modified == 0`)。
- **排程器觸發器公證**：在 `test_scheduler_jobs_configuration` 驗證 `monthly_jules_compaction_recurring` 的 `CronTrigger` 欄位與 `SchedulerConfig` SSOT 100% 對齊。
- **三向門禁全綠**：通過 `make lint`（393 來源檔 0 錯誤）、`make test-be`（769 passed）與 `make phase-audit`（Step 1 ~ Step 11 全綠）公證。
