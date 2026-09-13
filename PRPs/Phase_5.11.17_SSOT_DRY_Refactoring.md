# Phase 5.11.17: SSOT, DRY Refactoring & Periodic Job State Mismatch Fix

## 1. 目標 (Goal)
本階段旨在進行深度架構重構，徹底消除 Phase 5.11.13~16 所遺留的魔術數字與硬編碼 (Hardcoding)，並修復「週期作業狀態斷層 (Periodic Job State Mismatch)」的核心邏輯錯誤，嚴格落實 SSOT (Single Source of Truth) 與 DRY (Don't Repeat Yourself) 原則。

## 2. 發現與診斷 (Findings & Diagnosis)

### 2.1 週期作業狀態斷層 (The Periodic Job State Mismatch)
我們在 `scheduler_service.py` 中發現了嚴重的語意混淆，導致排程器狀態與預期發生斷層：
*   **Alice 的「見縫插針」目標 (正確)**：Alice 的目標是「Opportunistic Weekly (每週一次，只要有空就跑)」。她使用 `IntervalTrigger(hours=12)` 搭配 `_should_run_weekly`，藉由 Guard 機制確保一週只執行一次，這是完全正確的設計。
*   **Weekly Executive Summary 的「固定排程」目標 (錯誤)**：週報 (Weekly Report) 使用了 `CronTrigger(day_of_week='sun')`，意圖在**週日**執行。然而，它卻與 Alice 共用了同一個 `_should_run_weekly` 驗證器。
*   **斷層爆發點**：因為 `_should_run_weekly` **完全沒有檢查 Trigger 的約定時間** (只檢查本週是否跑過)，當伺服器在「週二」啟動時，它發現「本週還沒跑過」，就會**直接在週二觸發週報** (提早執行尚未到來的週日任務)！

### 2.2 魔術數字與提示詞硬編碼 (SSOT Violations)
*   **Fallbacks**: `leads_patrol.py` 中硬編碼了 24 小時的備用推算時間 (`timedelta(hours=24)`) 與 `ZoneInfo("Asia/Taipei")`。
*   **LLM 溫度**: `ai_operations.py` 中的 LLM 生成直接寫死了 `temperature=0.7`。
*   **提示詞污染**: `agent_registry.py` 寫死了預設的 fallback prompt (`"You are a helpful AI assistant."`)；`visual_generator.py` 更是直接將生圖指令 (`"Professional tech logo..."`) 寫死在字串內。

## 3. 修復方案 (Implementation Plan)

### 3.1 狀態斷層修復：Guard 語意解耦
1.  **更名與保留 Opportunistic 邏輯**：將原有的 `_should_run_weekly` 更名為 `_should_run_opportunistic_weekly` (並保留給 Alice 等不需要特定星期幾的任務)。
2.  **導入基於 Trigger 的精準驗證 (DRY)**：新增一個 `_should_run_scheduled_job` 方法，利用 APScheduler 原生的數學公式 `trigger.get_next_fire_time(last_run, last_run)`，判斷「現在時間」是否大於「上次執行後應發生的下一次排程時間」。只有真正「錯過」的任務才會觸發 Catchup，完美解決週報提早偷跑的問題。

### 3.2 徹底落實 SSOT
1.  **Settings 模型擴充**：在 `SchedulerConfig` 與相關 Config 模型中，新增 `system_timezone`, `market_report_fallback_hours`, `default_llm_temperature` 欄位。
2.  **Prompt 統一管理**：將遺落在程式碼的 Prompt 抽出，新增至 `pm_prompts.py` (`VISUAL_GENERATOR_PROMPT`, `GLOBAL_DEFAULT_FALLBACK`)。
3.  **邏輯層連動**：將上述四個檔案的硬編碼全數替換為動態讀取 SSOT 變數。

