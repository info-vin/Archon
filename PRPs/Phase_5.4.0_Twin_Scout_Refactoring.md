# Phase 5.4.0: Digital Twin Scout Data-Driven Configuration Refactoring

## Goal Description

目前系統中負責端到端測試與錄影的 `scripts/twin_scout.py` 與 `Makefile` 存在嚴重的硬編碼（Hardcoding）與技術債。每新增一個測試場景（如 Marketing, Fanout），都需要在 Python 中手寫專屬的 Playwright 控制邏輯（如 `verify_multi_agent_chat`），並在 Makefile 中新增專屬指令。這違反了 DRY 原則且無法規模化。

**Phase 5.4.0** 的目標是將 Twin Scout 重構為**「配置驅動 (Config-Driven) / 資料驅動 (Data-Driven)」**架構。透過統一的 YAML 設定檔來定義 Playwright 操作步驟，並由單一的執行引擎解析執行，實現完全的參數化。

## 架構設計決策

我們將沿用 Python `twin_scout.py` 作為核心，並將其改為讀取 YAML 的模式。
原因：此模式能繼續保持與目前後端依賴（如 Supabase DB, Gemini GenAI API）的無縫整合，不需完全重寫一套 TypeScript 版本。

## Proposed Changes

### `scripts/twin_scenarios/` (New Sub-component)

建立一個全新的配置資料夾，專門存放所有 Scout 的場景定義檔。為落實資料驅動精神，本階段建立了以下三個核心公證場景矩陣：

| 優先級 | 腳本名稱 (Scenario YAML) | 核心目的 (Purpose) | 涵蓋層級 (Scope) | 複雜度 | AI 視覺裁判 |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **P0** | `marketing_chat.yaml` | 驗證星型群聊實體運作（原 `verify_multi_agent_chat` 重構） | UI -> DB -> LLM -> AI 協作 | 🔴 極高 | 是 (辨識對話泡泡) |
| **P1** | `fanout_executive_summary.yaml`| 驗證 Clockwork 背景排程（原 `verify_fanout...` 重構） | Cron -> DB -> UI 聚合 | 🟠 高 | 否 (靜態 DOM 檢查) |
| **P2** | `check_workbench_video.yaml` | 驗證 RAG 影音素材渲染 (Phase 5.3.2 防禦) | DB (Regex) -> UI (Media) | 🟡 中 | 是 (辨識播放器 UI) |

**YAML 配置共同結構 (Schema):**
- `hooks`: 支援跨界整合 (如呼叫 Python 函數觸發排程)
- `auth`: 登入角色設定 (如 `admin@archon.com`)
- `steps`: 動作陣列 (`action: click`, `fill`, `goto`, `select_option`, `sleep` 等)
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

## Verification Results (Completed on 2026-05-25)

本計畫已透過實體驗證完畢，以下為具體的執行結果與除錯紀錄：

1. **YAML 引擎架構驗證**：已確認 `twin_scout.py` (包含 `YAMLScenarioRunner`) 能夠正確解析 `marketing_chat.yaml`，並順利轉換為 Playwright 的 `goto`, `click`, `fill`, `wait_selector` 等操作。
2. **動態變數解析修復**：在測試中發現 `YAMLScenarioRunner` 在處理 `{TIMESTAMP}` 變數時，會在每一步驟重新擷取系統時間，導致跨步驟的字串比對（如建立任務與後續點擊任務）發生 Timeout。已修復為在 Scenario 開始前產生單一 `session_timestamp` 並在所有步驟中重複使用。
3. **Agent 幻覺與資源耗盡阻斷**：在實彈測試 `marketing_chat` 場景時，發現模糊的指令（"Please perform deep marketing analysis..."）會觸發 Agent 產生幻覺，瘋狂呼叫 `/david/read` 試圖讀取本機不存在的 CSV/JSON 檔案，最終導致後端資源耗盡並使前端 API 請求 `aborted without reason`。已透過精準的 Prompt Engineering 修改 `marketing_chat.yaml` 的描述（注入假設數據並明確禁止外部搜尋），成功杜絕此幻覺現象。
4. **行銷素材與知識庫重載**：
    * 成功通過 AI 視覺裁判，截圖辨識獲得 `[WORKFLOW_SUCCESS]`。
    * 成功錄製並生成 `.webm` 實體錄影檔，並透過腳本自動轉移至 `enduser-ui-fe/public/assets/videos/auto_demos/marketing_demo.webm`。
    * 成功觸發 `KnowledgeRepository` 重載，將錄影檔中繼資料更新回 RAG 系統。
