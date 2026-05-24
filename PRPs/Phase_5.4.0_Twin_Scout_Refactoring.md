# Phase 5.4.0: Digital Twin Scout Data-Driven Configuration Refactoring

## Goal Description

目前系統中負責端到端測試與錄影的 `scripts/twin_scout.py` 與 `Makefile` 存在嚴重的硬編碼（Hardcoding）與技術債。每新增一個測試場景（如 Marketing, Fanout），都需要在 Python 中手寫專屬的 Playwright 控制邏輯（如 `verify_multi_agent_chat`），並在 Makefile 中新增專屬指令。這違反了 DRY 原則且無法規模化。

**Phase 5.4.0** 的目標是將 Twin Scout 重構為**「配置驅動 (Config-Driven) / 資料驅動 (Data-Driven)」**架構。透過統一的 YAML 設定檔來定義 Playwright 操作步驟，並由單一的執行引擎解析執行，實現完全的參數化。

## 架構設計決策

我們將沿用 Python `twin_scout.py` 作為核心，並將其改為讀取 YAML 的模式。
原因：此模式能繼續保持與目前後端依賴（如 Supabase DB, Gemini GenAI API）的無縫整合，不需完全重寫一套 TypeScript 版本。

## Proposed Changes

### `scripts/twin_scenarios/` (New Sub-component)

建立一個全新的配置資料夾，專門存放所有 Scout 的場景定義檔。

#### [NEW] `scripts/twin_scenarios/marketing_chat.yaml`
將原本 `verify_multi_agent_chat` 的硬編碼轉換為 YAML 配置，包含以下區塊：
- `auth`: 登入角色設定 (如 admin@archon.com)
- `steps`: 動作陣列 (包含 `action: click`, `action: fill`, `action: goto`, `action: select_option`, `action: sleep` 等)
- `analysis`: Gemini 驗證設定 (使用的 System Prompt Key 與成功條件)

### Core Twin Scout Engine

#### [MODIFY] `scripts/twin_scout.py`
- **刪除** `verify_multi_agent_chat` 與 `verify_fanout_executive_summary` 等特化函數。
- **新增** `ScenarioRunner` 類別，負責：
  - 讀取並解析 `--scenario <yaml_path>`
  - 將 YAML 定義的 `steps` 轉換為 Playwright 操作 (`pg.click()`, `pg.fill()`, `pg.goto()`)。
  - 將最終截圖與 DOM 狀態傳遞給 Gemini API 進行驗證。

### Makefile Consolidation

#### [MODIFY] `Makefile`
- 移除硬編碼的目標 (如 `twin-scout-marketing`, `twin-scout-action`, `twin-scout-fanout`)。
- 新增通用型指令：
  ```makefile
  # make twin-record SCENARIO=marketing_chat
  twin-record:
  	@echo "🚀 啟動數位孿生錄影 (場景: $(SCENARIO))..."
  	@set -a; [ -f .env ] && . ./.env; set +a; \
  	python/.venv/bin/python scripts/twin_scout.py --scenario scripts/twin_scenarios/$(SCENARIO).yaml --record true
  ```

## Verification Plan

### Manual Verification
1. 執行新的通用指令：`make twin-record SCENARIO=marketing_chat`
2. 檢查命令列輸出是否能正確讀取並循序執行 YAML 檔中定義的每個 Playwright 步驟。
3. 檢查 `enduser-ui-fe/public/assets/videos/auto_demos/` 或 `.twin/videos/` 是否能產出與原本一致的 `.webm` 實體錄影檔。
4. 檢查 `.twin/diagnostics/` 是否能產出 `WORKFLOW_SUCCESS` 報告。
