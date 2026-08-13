# Phase 5.10.15 SSOT Prompt Refactoring

## 目標 (Goal)
統一系統內的 Prompt 管理架構，根除「雙源頭 (Dual Source of Truth)」與「快取穿透 (Cache Defeat)」的技術債，嚴格落實 SSOT 與 DRY 原則。

## 問題背景 (Background)
根據深入的架構分析，目前後端系統有 31 處業務邏輯呼叫 `prompt_service.get_prompt()` 時，被迫從 `src/server/prompts/*.py` 匯入巨大的提示詞字串並作為 `default` 參數傳遞。這導致：
1. **SSOT 破裂**：代碼 (Git) 與資料庫 (Supabase) 之間沒有同步機制。
2. **DRY 破裂**：業務邏輯層被迫管理預設提示詞字串。
3. **N+1 快取穿透**：當資料庫不存在該提示詞時，`prompt_service` 會回傳 `default` 但不進行快取，造成嚴重的資料庫效能負擔。
4. **幽靈模組**：`prompts/__init__.py` 自 Phase 4.4 建立以來始終為 0 Bytes，完全沒有發揮集中管理的作用。

## 實作計畫 (Implementation Plan)

### 1. 建立絕對單一源頭 (SSOT Registry)
將 `python/src/server/prompts/__init__.py` 實體化，匯入所有 `*_prompts.py` 內的常數字串，並匯出一個全域字典 `ALL_PROMPTS`。

### 2. 升級 prompt_service.py
- **啟動時自動 Upsert**：在 `load_prompts()` 時，比對 `ALL_PROMPTS` 與資料庫，若代碼中有新增的 Prompt 但資料庫沒有，自動 `upsert` 至 Supabase。
- **快取命中優化**：`get_prompt()` 直接從記憶體快取或 `ALL_PROMPTS` 讀取，拒絕快取穿透。

### 3. 全域業務邏輯淨化
以自動化腳本掃描並修改所有 Consumer 檔案 (共 31 處)：
- 拔除 `from src.server.prompts... import XXX_PROMPT`。
- 將 `prompt_service.get_prompt("KEY", default=XXX_PROMPT)` 簡化為 `prompt_service.get_prompt("KEY")`。

### 4. 嚴格品質門禁 (Quality Gates)
- 靜態分析：`make lint-be` 確保無 unused imports。
- 自動化測試：確保 `prompt_service` 能正確處理 fallback，並跑通所有既有 `make test-be` 測試。
