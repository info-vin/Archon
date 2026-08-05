# Phase 5.10.2: Scheduler Updates & Configuration Hardening

## 背景與目標 (Background & Goals)
根據 Phase 5.10.1 的查核結果，我們對多個核心週期任務進行了重新排程與硬化，嚴格遵守 SSOT (Single Source of Truth) 與 DRY 原則，消除硬編碼，並確保自動化測試能夠順利通過。

## 變更項目 (Changes Implemented)
1. **System Probe Cleanup & Prune Stale Leads (資料清理)**
   - 時間調整：設定為每日 11:50 (UTC+8)。
2. **Meta Twin Audit (雙生對帳)**
   - 週期調整：設定為每 45 分鐘執行一次。
   - 修正目標認知：確認該任務負責掃描 Agent 執行日誌與統計（如速率限制、無窮迴圈等），而非場景圖 (Scene Graph) 的實體驗證。
3. **Alice Auto Fetch (104 業務爬蟲)**
   - 時間調整：設定為每週二、三、四、五的 10:25 (UTC+8)，週末取消。

## 物理公證與測試 (Verification)
- 更新了 `settings.py` 內的 SSOT 設定。
- 更新了 `tests/unit/services/test_scheduler_service.py` 內對齊的測試斷言。
- 順手修復了 `scratch.py` 的微小 linter 命名衝突。
- `make lint-be`, `uv run mypy src/server/`, 與 `make test-be` 皆以 100% 綠燈通過。
