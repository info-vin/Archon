# Phase 5.10.16: SSOT Defensive Hardening (防禦性硬化)

## 目標 (Objective)
在 Phase 5.10.15 完成提示詞 (Prompt) 絕對單一事實源 (SSOT) 架構後，本次維護階段專注於**修補邊界條件與潛在的盲區風險**，確保系統的強健性與開發者的除錯體驗，並排除「樂觀路徑」所帶來的隱患。

## 任務清單 (Task List)

### 1. 靜默降級 (Silent Degradation) 陷阱防禦
- **問題**: 拔除 `default` 參數後，若 `prompt_service.get_prompt(name)` 遇到不存在的 key (例如 Typo 打錯字)，會無聲無息地回傳 `"You are a helpful AI assistant."`，造成除錯困難。
- **解法**: 
  - 在 `get_prompt` 回傳最終 fallback `default or "You are a helpful AI assistant."` 之前，主動注入 `logger.warning(f"⚠️ [PromptService] Missing prompt key: {name}")`。
  - 這樣能讓日誌監控系統主動捕獲異常。

### 2. 測試斷言的潛在脆弱性 (Fragile Tests) 修復
- **問題**: `test_prompts_loading.py` 的長度斷言 `assert len(service._prompts) == 4 + len(ALL_PROMPTS)` 依賴了 mock keys 與 ALL_PROMPTS 絕對不重疊的樂觀假設。
- **解法**: 
  - 將長度計算改為基於 Set 的聯集計算：`len(set(mock_keys) | set(ALL_PROMPTS.keys()))`。
  - 增加針對個別新增 mock key 的驗證，避免未來架構變動導致測試誤判紅燈。

### 3. Auto-Upsert 的同步延遲與連線風險防禦
- **問題**: 分散式系統中，若啟動時 Supabase 連線瞬斷，`load_prompts()` 的 `upsert_batch` 會失敗並吃下例外。此時雖然記憶體 Cache 運作正常，但會造成多節點 (Node) 間的提示詞不同步。
- **解法**:
  - 引入 `retry_with_backoff` 機制來包裝 `self.execute_query` 中的 Bulk Upsert。
  - 保證在容器啟動時的微小網路抖動不會導致永久的 DB 寫入失敗。

## 驗證標準 (Definition of Done)
1. **0 虛假驗證**: 所有防禦性邏輯皆具備對應的 pytest 測試涵蓋 (例如：測試輸入不存在的 key 是否確實觸發 warning logger)。
2. **品質門禁**: `make test-be` 與 `make lint-be` 必須 100% 通過。
3. **沒有 A 壞 B**: 確認日誌硬化不會對系統效能產生負面影響。
