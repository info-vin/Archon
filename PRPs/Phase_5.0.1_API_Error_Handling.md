# Phase 5.0.1: API 錯誤處理與模型配額管理指南 (API Error Handling & Quota Management)

> **建立日期**: 2026-05-14
> **目的**: 針對 Phase 5 多智能體 (Multi-Agent) 架構在實際運行時遇到的 HTTP 500, 503, 429 錯誤，提供基於數據與官方文件的實體解決方案與架構規範。

在導入 MCP 與 PydanticAI 後，我們的 Multi-Agent 工作流與 Google Gemini API 產生了緊密的交互。在實際運行時，我們觀察到了三種主要的錯誤代碼。以下是其深層原因與系統解決方案。

---

## 🔴 1. HTTP 429 (Too Many Requests / RESOURCE_EXHAUSTED)

**現象與物理證據**:
當我們使用 `gemini-3-flash-preview` 等模型時，Docker Log 顯示：
`Quota exceeded for metric: generativelanguage.googleapis.com/generate_content_free_tier_requests, limit: 20, model: gemini-3-flash`

**根因分析**:
* 儘管部分 Gemini API 的免費層級 (Free Tier) 提供 1,500 RPD (Requests Per Day)，但特定模型（例如 `gemini-3-flash`）的每日免費額度被嚴格限制為 **20 次/天**。
* 由於星型群聊架構 (Supervisor <-> Worker) 一次完整的任務執行會來回交談多次，這會迅速耗盡這 20 次的配額，導致 429 錯誤。

**架構解決方案與最佳做法**:
1. **實作指數退避 (Exponential Backoff)**: 針對短時間的高頻呼叫 (例如 RPM 限制)，我們已在 `workflow_engine.py` 的 `_run_agent_with_retry` 中導入 `tenacity`，最高等待約 65 秒。
2. **金鑰備援輪替**: 在代碼中實作 `GEMINI_API_KEY` 與 `GOOGLE_API_KEY` 的失效備援。當一把免費金鑰耗盡 429 時，自動切換至備用金鑰。
3. **模型降級策略**: 
   * 若測試頻繁，應將 `SUPERVISOR_AGENT_MODEL` 降級至配額更寬鬆的 `gemini-2.0-flash` 或 `gemini-1.5-flash`。
   * 根據官方文件，應密切關注淘汰時程（例如 `gemini-3.1-flash-lite-preview` 可能即將或已淘汰），適時轉移。
4. **付費層級 (Pay-as-you-go)**: 進入正式生產環境或進行高強度自動化 E2E 測試時，必須綁定付費帳號解鎖限制。

---

## 🟡 2. HTTP 503 (Service Unavailable)

**現象與根因**:
* **現象**: `503 Service Unavailable`
* **根因**: Google 伺服器端暫時過載或正在維護，導致容量不足。這在 `-preview` 或 `-exp` 實驗性模型中尤其常見。

**架構解決方案與最佳做法**:
1. **韌性自癒 (Resilience)**: 這是雲端基礎設施的常態，**不應讓人為介入**。必須依賴 `_run_agent_with_retry` 的重試機制。
2. **模型切換**: 若 503 頻繁且持續，系統應具備動態回退 (Fallback) 到穩定版模型（如 `gemini-2.5-flash`）的能力。

---

## 🟣 3. HTTP 500 (Internal Server Error) 

**現象與根因**:
* 在 MCP 架構下，HTTP 500 **幾乎不是**外部 API 的問題，而是 **MCP Tool 內部拋出了未處理的例外 (Unhandled Exception)**，隨後被 RPC Bridge 強制包裝成 HTTP 500 回傳。

**常見物理罪證與解決方案**:
1. **語法錯誤**: Python 代碼的 Syntax Error (如字串未閉合) 會直接引發 500。
    * *解法*: 嚴格執行 `make lint` 與執行前的基本語法掃描。
2. **資料庫空狀態防禦 (`PGRST116`)**:
    * *教訓*: 使用 `supabase.table().select().single().execute()` 時，若資料表為空，SDK 會暴力拋出 500。
    * *解法*: **絕對禁止**使用 `.single()`。改用安全的陣列查詢模式：`res = query.execute()` 並搭配 `if res.data and len(res.data) > 0:`。
3. **版本斷層 (Version Disconnect)**:
    * *教訓*: PydanticAI 套件升級時，可能發生如 `result.output` 屬性不向後相容的問題，引發 `AttributeError` 導致 500。
    * *解法*: 在底層建立相容性 Helper (`_get_output()`)。

---

### 📝 行動指南 (Next Steps)
1. 在測試環境設定中明確標示「Free Tier 20 RPD Limit」的風險，並建立金鑰池或降級方案。
2. 開發任何新的 MCP Tool 時，必須包含 `try-except` 包裝，防止底層異常直接穿透 RPC Bridge 造成 500 錯誤。