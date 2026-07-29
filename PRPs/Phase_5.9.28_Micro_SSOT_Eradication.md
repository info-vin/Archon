# Phase 5.9.28: Micro SSOT Eradication

## 目標 (Goal)
延續 Phase 5.9.27 的成功，本階段致力於徹底根除 `phase-audit` 找出的最後 13 項微型硬編碼 (Micro Hardcoding)，並完善自動化品質門禁。

## 開發任務 (Tasks)
1. **設定檔擴充 (Schema Extension)**
   - 在 `settings.py` 建立或擴充網路預設值 (Ollama, Agents, MCP URLs)。
   - 擴充 `SchedulerConfig` 補齊 `day_of_week`。
2. **服務物理重構 (Service Refactoring)**
   - 替換所有內部微服務連線的 Fallback 網址。
   - 替換 `scheduler_service.py` 剩餘的排程參數。
3. **門禁調校 (Audit Gate Tuning)**
   - 調校 `scripts/phase_audit.py`，使 `ssot_hardcoding_audit()` 能智慧辨識 Event Loop Yielding 的微小休眠 (例如 `asyncio.sleep(0)`)，避免誤判。

## 成功標準 (Definition of Done)
- 零硬編碼：`make phase-audit` 報表顯示 0 項違規。
- 零回歸：`make test-be` 600+ 項測試綠燈。
- 嚴格型別：`uv run mypy src/server/` 0 錯誤。
