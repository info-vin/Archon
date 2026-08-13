# Phase 5.10.14: Weekly Engineering Retrospective (DevBot)

本計畫將實作自動化的每週工程反思機制 (Weekly Engineering Retrospective)，並將計畫文檔存檔為 `@PRPs/Phase_5.10.14_Weekly_Engineering_Retro.md`。

## User Review Required / Open Questions
- **星環討論 (Group Chat) 參與者**：反思會議將由 `DevBot (Engineering)` 主持，並在 Prompt 中明確要求其與 `POBot (Product)` 以及 `Supervisor (Business)` 進行跨維度討論，確保工程決策能對齊產品與商業目標。
- **自動化驗證**：已規劃 `verify_retro_5.10.14.py` 作為硬性公證腳本，絕不採用樂觀路徑，會實體打通配置層與 Prompt 渲染層。

## Proposed Changes

### [NEW] `PRPs/Phase_5.10.14_Weekly_Engineering_Retro.md`
- 將本計畫的技術細節與驗證標準存檔至專案目錄中，作為歷史稽核依據，杜絕虛假開發。

### [MODIFY] `python/src/server/schemas/settings.py` (file:///Users/vincenta/GoogleKwok022/Archon/python/src/server/schemas/settings.py)
- **嚴格遵守 SSOT**：新增 `weekly_engineering_retro_days` (預設 `"sat"`) 與 `weekly_engineering_retro_lookback_days` (預設 `7`)，完全消滅硬編碼。

### [MODIFY] `python/src/server/services/scheduler_service.py` (file:///Users/vincenta/GoogleKwok022/Archon/python/src/server/services/scheduler_service.py)
- **Category 3 掛載**：將排程掛載於 Category 3 (Stateful Weekly Jobs)。
- **動態時間計算**：利用現有的 `self._parse_dynamic_hf_time(config, offset_hours=1)`，精準計算出 `HF_pause` (17:18) 的**前一個小時** (16:18)，徹底動態適應，符合 DRY 原則。

### [MODIFY] `python/src/server/services/scheduler/jobs/tech_debt_patrol.py` (file:///Users/vincenta/GoogleKwok022/Archon/python/src/server/services/scheduler/jobs/tech_debt_patrol.py)
- 新增 `run_engineering_retrospective()` 實體方法。
- **動態 Context 收集**：利用 `subprocess` 動態讀取過去 `config.weekly_engineering_retro_lookback_days` 天的 `git log` 與 `GEMINI.md`，拒絕硬編碼的 7 天。
- **Map-Reduce 引擎**：將 Context 交由 `beta_graph` 進行大腦反思。
- 指派任務給 `AgentUUIDs.DEV_BOT`。

### [MODIFY] `python/src/server/prompts/pm_prompts.py` (file:///Users/vincenta/GoogleKwok022/Archon/python/src/server/prompts/pm_prompts.py)
- 新增 `ENGINEERING_RETRO_DEFAULT` 提示詞模板。
- **動態變數綁定**：使用 `{days}`, `{git_logs}`, `{gemini_logs}` 動態綁定，並明確指示 DevBot 啟動 Group Chat，與 POBot、Supervisor 協作。

### [NEW] `scratch/verify_retro_5.10.14.py`
- 用於執行嚴格自動化驗證的實體腳本。

## Verification Plan

### 自動化公證 (Hard Verification)
不依賴口頭承諾，將執行 `scratch/verify_retro_5.10.14.py`，該腳本會：
1. 實體讀取 `SettingsService`，斷言 (Assert) `weekly_engineering_retro_days == "sat"`。
2. 呼叫 `scheduler_service._parse_dynamic_hf_time(config, 1)`，斷言其計算結果確實為 `HF_pause` 的前一個小時。
3. 實體執行一次 `git log` 抓取測試，確保 subprocess 未發生異常，且能順利替換至 Prompt 模板中。
4. 若任一斷言失敗，腳本將以 `exit(1)` 中止，徹底防堵樂觀路徑與幻想。
