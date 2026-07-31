# Phase 5.9.36: 服務層 SSOT 淨化計畫 (Services SSOT Eradication)

## 目標 (Goal)
針對 `services/` 層殘留的 46 筆 SSOT 違規，遵循先前的開發軌跡（Phase 5.9.28 的 `NetworkConfig` 與 Phase 5.9.35 的 `shared_constants.py`），進行深度收攏，並配合自動化公證 (`make phase-audit`) 達到零違規。

## 歷史軌跡對帳 (Historical Context Alignment)
> [!NOTE]
> - **Phase 5.9.28** 建立了 `NetworkConfig` (位於 `schemas/settings.py`)，成功將內部 `MCP_SERVICE_URL` 等網址集中管理。這印證了我們處理外部 API Base URL 也應沿用此架構。
> - **Phase 5.9.35** 建立了 `shared_constants.py` (`RoleEnum`, `StatusEnum`)，這印證了跨模組的業務狀態不該各自表述。

## 需要使用者的審查 (User Review Required)
> [!IMPORTANT]
> - 針對爬蟲、模型特徵偵測（如 `["llama", "qwen"]`、`["python", "py"]`），我們將其判定為「合法啟發式規則 (Heuristics)」，直接標註 `# 合法`，**不進行**常數抽離，以免過度設計導致高耦合。您是否同意此架構邊界？

## 預期修改內容 (Proposed Changes)

---
### 1. 網路與端點收攏 (Network & Endpoints)
沿用 Phase 5.9.28 的架構，擴充 `NetworkConfig`。

#### [MODIFY] [schemas/settings.py](file:///Users/vincenta/GoogleKwok022/Archon/python/src/server/schemas/settings.py)
在 `NetworkConfig` 中新增外部 AI 服務的 Base URL 預設值（同時支援由 `archon_settings` 資料庫覆蓋）：
- `anthropic_base_url: str = Field(default="https://api.anthropic.com/v1/")`
- `openrouter_base_url: str = Field(default="https://openrouter.ai/api/v1")`
- `google_base_url: str = Field(default="https://generativelanguage.googleapis.com/v1beta/openai/")`

#### [MODIFY] 依賴的 Client 模組
在以下模組中，將硬編碼網址替換為從 `NetworkConfig` 動態取得：
- `services/llm/clients.py`
- `services/discovery/providers/google_handler.py`

---
### 2. 業務狀態與模型列舉 (Domain Enums & States)
強制使用 Phase 5.9.35 建立的常數中心，消滅各自表述的狀態機。

#### [MODIFY] [services/shared_constants.py](file:///Users/vincenta/GoogleKwok022/Archon/python/src/server/services/shared_constants.py)
- 新增 `TaskStatusEnum (StrEnum)`：收錄 `"todo", "doing", "review", "done", "processing", "dispatched", "error"`。

#### [MODIFY] 行銷與統計模組
- `services/marketing/analytics_handler.py`：替換 `["draft", "changes_requested"]` 為 `StatusEnum`。
- `services/stats/domains/agent_metrics.py`：
  - 狀態陣列替換為 `StatusEnum`。
  - 將硬編碼的 `["DevBot", "MarketBot"...]` 替換為引用 `AgentNames`。

#### [MODIFY] 專案管理模組
- `services/projects/task_service.py` 與 `tasks/query_logic.py`：替換 `["todo", "doing"...]` 為 `TaskStatusEnum`。

---
### 3. 合法放行 (Static Mappings Whitelist)
對於判定為合法的啟發式過濾規則與站外佔位圖，加入 `# 合法` 註解以通過公證。

#### [MODIFY] 標註合法硬編碼的檔案
- `services/discovery/models.py` (模型關鍵字判斷)
- `services/storage/code/extractors.py` (副檔名)
- `services/code_extraction/logic/code_validator.py`
- `services/marketing/lead_handler.py` (職稱過濾)
- `services/marketing/blog_generator.py` (佔位圖 `picsum.photos`)
- `services/marketing/logo_tool.py`

## 驗證計畫 (Verification Plan)

### 自動化測試與品質門禁 (Automated QA Gates)
本計畫執行完畢後，必須 100% 通過以下三道防線：
1. **`make lint-be`**：驗證 `NetworkConfig` 擴充與 `Enum` 取代的語法與強型別安全性。
2. **`make test-be`**：確保 616 項測試全部通過，保證抽離配置後，現有的業務邏輯 (Regression) 零破壞。
3. **`make phase-audit`**：確保終極防線不再噴出任何有關 URL 或 Array 的 SSOT 違規。
