# Phase 5.11.12: Scheduler Log Hardening (SSOT & DRY Refactoring)

## 📌 背景 (Context)
在先前的版本 (Phase 5.11.10 之前)，`scheduler_service.py` 中的狀態型排程器 (Stateful Job Scheduler) 在開機的 Catchup 補撈階段，會因為時間未到而正確阻擋提早發動的排程任務（例如 `alice_auto_fetch` 目標時間為 10:25，在 09:05 觸發 Catchup 時被正確擋下）。
然而，因為 `_schedule_stateful_job` 的封裝設計缺陷，外部註冊時被強迫**硬編碼 (Hardcoded)** 傳入了一個固定的字串 `skip_msg = "Already run today"`，導致了「雖然是因為時間還沒到而跳過，日誌卻盲目印出『今日已執行』」的嚴重誤導陷阱。

（*附註：透過 Docker 日誌實體查核，Alice 的確在 10:25 準時精準發動，並在稍後成功跑完並觸發了 Bob 的報表與高階主管摘要。這證實了物理系統完美運作，純粹是日誌封裝的設計問題。*）

## 🎯 目的 (Objectives)
徹底落實 SSOT (單一事實來源) 與 DRY 原則，消滅硬編碼的日誌字串，讓判斷邏輯自己為跳過的行為給出精確的物理理由。

## 🛠️ 修改計畫 (Implementation Plan)

### 1. 升級驗證邏輯特徵標記 (Signature Upgrade)
修改 `python/src/server/services/scheduler_service.py` 中所有的 `_should_run_*` 驗證方法，將回傳值從單純的 `bool` 變更為 `tuple[bool, str]` (決定, 理由)。
受影響的方法：
- `_should_run_local_only`
- `_should_run_daily`
- `_should_run_weekly`
- `_should_run_biweekly`
- `_should_run_monthly`

**範例實作 (`_should_run_daily`)**：
```python
if now_local.hour < target_hour or (now_local.hour == target_hour and now_local.minute < target_minute):
    return False, f"Time not reached (Target: {target_hour:02d}:{target_minute:02d})"
# ...
if current_day_name not in target_days:
    return False, f"Not scheduled for {current_day_name} (Target: {target_days})"
# ...
if last_run.astimezone(DEFAULT_TIMEZONE).date() >= now_local.date():
    return False, f"Already run today at {last_run.strftime('%H:%M:%S')}"

return True, "Time arrived"
```

### 2. 徹底移除外層硬編碼 (DRY & SSOT)
修改 `_schedule_stateful_job` 的封裝結構：
- **移除參數**：將 `skip_msg: str` 參數從方法特徵中徹底刪除。
- **解構回傳值**：在內層的 `wrapper()` 解構出 `should_run, reason`。
- **動態日誌**：將原本的 `logger.info(f"⏭️ Clockwork: Skipped '{job_id}' ({skip_msg})")` 改為使用真實的動態理由：`logger.info(f"⏭️ Clockwork: Skipped '{job_id}' ({reason})")`。

### 3. 清理呼叫端 (Call Sites)
在 `_schedule_jobs` 方法中，刪除高達 12 處手動傳入的 `"Already run today"`, `"Already run this week"`, `"Already run recently"` 硬編碼字串，大幅縮減代碼冗餘。

## ✅ 自動化驗證計畫 (Automated Verification Plan)
為了落實零虛假驗證，我們將以自動化腳本取代人工肉眼檢查：

1. **單元測試斷言升級 (Unit Test Assertion Upgrade)**
   - 執行 `uv run pytest tests/test_scheduler_service.py -v`。
   - 同步修改所有 `patch.object` 針對 `_should_run_*` 的 Mock 返回值，將單一布林值替換為 `(True, "")` 或 `(False, "Reason")`，嚴防 `too many values to unpack` 崩潰。
   - 新增單元測試，精準斷言不同情境下的動態字串：
     - 情境 A：當前時間 < 目標時間 ➔ 斷言字串包含 `"Time not reached"`
     - 情境 B：非排程日 (如週末) ➔ 斷言字串包含 `"Not scheduled for"`
     - 情境 C：同日重複觸發 ➔ 斷言字串包含 `"Already run today at"`

2. **實體探針自動化公證 (Physical Probe Automation)**
   - 撰寫 `scratch/verify_catchup_log.py` 探針腳本，實例化 `SchedulerService`。
   - 注入一個刻意提早觸發的 `Catchup` 假任務，並攔截 (Intercept) `logger` 的輸出。
   - 腳本必須自動斷言 (Assert) 日誌輸出是否為動態理由字串，徹底捨棄「人工看 Docker log」的僥倖心態。

3. **全域品質門禁 (Global Quality Gate)**
   - 最終執行全域測試 `make test` 與型別檢查 `make lint`，確保本次重構達成 100% 綠燈，無改 A 壞 B 之情事。
