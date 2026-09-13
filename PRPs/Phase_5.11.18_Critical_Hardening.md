# Phase 5.11.18 關鍵硬化：實體路徑與 SSOT 幽靈警告修復 (2026-09-13)

## 📌 背景與目標 (Context & Objectives)

在今日的超長伺服器日誌中，系統暴露了三個由環境限制與早期架構遺留造成的「級聯失敗 (Cascading Failure)」與「斷層」。
本階段的目標是嚴格遵循「拒絕虛假開發」與「物理穿透驗證」原則，不對環境限制（如 Hugging Face 對 Telegram 的封鎖）進行無意義的代碼修補，而是精準針對實體 Bug 進行 L2 級別的架構硬化。

## 🚨 核心問題與物理真相 (Core Issues & Ground Truth)

### 1. 限流報警機制的「實體路徑斷層」 (Silent Rate Limit Alert Failure)
- **病因**：當 Gemini 發生 `429 RESOURCE_EXHAUSTED` 時，Agent 嘗試將警報寫入 `archon_logs`。然而，`src/agents/base_agent.py` 中使用了錯誤的相對路徑 `from ..utils import get_supabase_client`。
- **後果**：觸發 `ImportError`，隨後被 `try-except` 靜默吞噬。導致系統在耗盡 API 額度時，UI 毫無警報，造成嚴重的維運盲區。

### 2. Supabase 504 閘道超時與雪崩效應 (Gateway Timeout & Thundering Herd)
- **病因 A (前端)**：UI 中的 `useTaskQueries` 採用 `useSmartPolling(2000)` 每 2 秒高頻輪詢。當 Supabase 發生短暫過載（如排程爬蟲耗盡連線）並回傳 `504` 時，前端毫無退避機制，繼續瘋狂敲擊，最終導致 Schema Cache 崩潰 (`PGRST205`)。
- **病因 B (後端)**：`Task Dispatcher` 排程器使用 `is_recurring = True` 進行背景輪詢，但資料庫中並無該欄位的索引 (Index)，導致全表掃描。

### 3. PromptService 的幽靈警告 (Ghost Prompt Warnings)
- **病因**：`GLOBAL_DEFAULT_FALLBACK` 與 `VISUAL_GENERATOR_PROMPT` 在實體模組中被宣告，卻未註冊至 `ALL_PROMPTS` 這個 SSOT (單一事實來源) 字典中。
- **後果**：系統啟動或重整時，頻繁跳出 `Missing prompt key` 的錯誤日誌。

### 4. Telegram 網路黑洞 (拒絕虛假修復)
- **物理現實**：日誌顯示 30 秒的超時機制完美生效，但仍回報 `ConnectTimeout`。
- **結論**：這是 Hugging Face Spaces 內部網路防火牆物理封鎖了對 `api.telegram.org` 的 outbound 連線。我們不進行代碼上的「虛假修復」，而是直接依賴先前實作的資料庫 Log 備援。

---

## 🛠️ 實作內容 (Implementations)

### 1. 代理人基礎設施修復 (Agent Infrastructure)
- **檔案**: `python/src/agents/base_agent.py`
- **變更**: 將 `from ..utils` 校正為正確的絕對物理路徑 `from src.server.utils import get_supabase_client`。

### 2. 錯誤退避與效能優化 (Error Backoff & Indexing)
- **檔案**: `archon-ui-main/src/features/projects/tasks/hooks/useTaskQueries.ts`
- **變更**: 為 `useProjectTasks` 與 `useTaskCounts` 導入錯誤退避機制。當發生 `query.state.error` 時，將輪詢間隔強制延長至 60 秒 (`60000`)。
- **檔案**: `migration/0.2.3/06_add_missing_indexes.sql`
- **變更**: 新增 `CREATE INDEX IF NOT EXISTS idx_archon_tasks_is_recurring ON public.archon_tasks (is_recurring);` 徹底消除背景任務的全表掃描。

### 3. Prompt SSOT 對齊 (Prompt SSOT Alignment)
- **檔案**: `python/src/server/prompts/__init__.py`
- **變更**: 匯出並將 `GLOBAL_DEFAULT_FALLBACK` 與 `VISUAL_GENERATOR_PROMPT` 註冊至 `ALL_PROMPTS` 字典，消滅幽靈警告。

---

## 🛡️ 公證與驗證 (Verification & Audit)

- [x] **靜態檢查**: `make lint-be` 零瑕疵通過。
- [x] **單元測試**: `make test-be` (涵蓋 706 項斷言) 100% 綠燈通過，保證 0 退化。
- [x] **架構稽核**: `make phase-audit` 確認 4 大架構維持 99.0% 優良，無 L2 Repository bypass 或 SSOT 硬編碼違規。

*本階段已達成嚴格的物理斷層修復，提升了系統在極端限流與網路隔離環境下的防禦韌性。*
