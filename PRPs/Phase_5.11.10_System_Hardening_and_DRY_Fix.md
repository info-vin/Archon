# 目標說明 (Goal Description)

本計畫 (Phase 5.11.10) 旨在解決兩大核心架構問題，嚴格遵守「查清楚原因、比對歷史紀錄、絕不盲猜」的指示：

1. **Telegram 服務網路層斷連 (Network Timeout)**：徹底查明 Telegram 通知為何「又壞掉」的物理原因，並實作韌性防禦 (Resilience)。
2. **爬蟲架構與重試機制重構 (DRY & Gap Fixes)**：根除前一階段在爬蟲雜訊修復中遺留的代碼斷層與不重複原則 (DRY) 違規。

### 🔍 Telegram 反覆失效的「歷史鑑識與物理真相」

針對您的提問：「有比對過 git log 開發紀錄嗎？這問題好像有改過很多次，為何都修復不好？」，我進行了嚴密的 Git 考古與物理驗證：

**歷史盲點 (為何修復不好)**：
回顧 `telegram_service.py` 的 Git 歷史：
- `c458affd`：將 `.env` 讀取移到 property 以解決載入時差。
- `a72f71c4`：為了符合 SSOT，移除 `.env` 降級，改由資料庫 (SettingsService) 讀取。
- `dcbac1a6`：**關鍵點！** 之前我們發現雲端環境中 Telegram 經常超時 (Timeout)，當時判斷是因為 property 被呼叫 3 次，導致資料庫發生 N+1 查詢拖慢了整個執行緒。因此重構為只查詢一次。

**殘酷的物理真相 (本次鑑識)**：
消除 N+1 查詢只是「治標」，並未解決「治本」問題。我透過 Python 的 `httpx` 在您的環境發起真實探針，結果發現：
1. **錯誤訊息為空白的元凶**：日誌中 `Failed to send message:` 後面是空白的。實體測試證明，當 `httpx` 發生 `ConnectTimeout` 或 `ReadTimeout` 時，其被捕捉後的字串特徵 `str(e)` 正好就是「空字串」。這證明本次失效**絕對是網路超時**，而非 Token 錯誤 (會回傳 404/401) 或 Markdown 錯誤 (會回傳 400 且附帶詳細字串)。
2. **22秒網路延遲突波**：我透過 `curl` 連線 `api.telegram.org` 測試，發現正常時僅需 0.6 秒 (這是您昨天用腳本單次測試會成功的原因)，但偶爾會遇到長達 **22 秒** 的解析與連線延遲 (網路抖動/跨國路由阻斷)。
3. **10秒定時炸彈**：從第一次建立 `telegram_service.py` 以來，底層一直寫死 `timeout=10.0`，從未被修改。這表示只要遇到上述的延遲突波，10 秒一到系統就會暴力切斷連線，導致通知失敗。

## 需要使用者審查 (User Review Required)

> [!IMPORTANT]
> 本計畫已包含 Telegram 的實體調查結果與修復計畫。請審閱。一旦您同意，我將同步執行「Telegram 網路韌性硬化」與「爬蟲 DRY 重構」。

## 提議的修改內容 (Proposed Changes)

---

### [Component 1] Telegram 網路韌性硬化 (Resilience Hardening)

#### [MODIFY] [telegram_service.py](file:///Users/vincenta/GoogleKwok022/Archon/python/src/server/services/system/telegram_service.py)
- **放寬網路時間鎖**：將 `httpx.AsyncClient(timeout=10.0)` 調整為 `timeout=30.0`，物理包容海外 API 節點的延遲突波。
- **自癒重試 (Retry-Backoff)**：在 `send_message` 內針對 `httpx.RequestError` 加入最多 3 次的非同步重試機制 (`asyncio.sleep(2)`)，以克服突發的網路抖動。
- **消滅幽靈日誌**：將異常捕捉 `logger.error(f"...: {e}")` 修正為 `logger.error(f"...: {repr(e)}")`。確保未來的斷線能明確印出 `ConnectTimeout`，不再讓我們瞎猜。

---

### [Component 2] 爬蟲設定重構 (消滅斷層與冗餘)

根據 08-29 的代碼鑑識，我們確認在 `batch.py` 等三個策略檔中，隱藏 iframe 與移除彈窗的設定只有被寫入「官方文件站」的條件分支中。一般網站完全漏掉了防禦。此外，包含 OneTrust 腳本在內的長達十幾行的設定被複製貼上了 6 次。

#### [NEW] [config_factory.py](file:///Users/vincenta/GoogleKwok022/Archon/python/src/server/services/crawling/helpers/config_factory.py)
- 實作 `get_base_crawler_config_kwargs(settings: dict) -> dict` 方法，集中管理所有核心的抗雜訊策略：包含 `js_code` (OneTrust)、`excluded_tags` (附帶 `# 合法` 標記)、`excluded_selector`、`process_iframes=False` 以及 `remove_overlay_elements=True`。

#### [MODIFY] [batch.py](file:///Users/vincenta/GoogleKwok022/Archon/python/src/server/services/crawling/strategies/batch.py)
#### [MODIFY] [recursive.py](file:///Users/vincenta/GoogleKwok022/Archon/python/src/server/services/crawling/strategies/recursive.py)
#### [MODIFY] [single_page.py](file:///Users/vincenta/GoogleKwok022/Archon/python/src/server/services/crawling/strategies/single_page.py)
- 完全刪除那 6 坨龐大且重複的 `CrawlerRunConfig` 實例化程式碼。改為呼叫 `get_base_crawler_config_kwargs(settings)` 取得基礎設定 `config_dict`，統一執行 `CrawlerRunConfig(**config_dict)`。使 `else` 分支無痛繼承標準抗雜訊設定，修復斷層。

---

### [Component 3] 向量化管線重構 (消滅冗餘)

#### [MODIFY] [batch_processor.py](file:///Users/vincenta/GoogleKwok022/Archon/python/src/server/services/embeddings/batch_processor.py)
- 新增輔助函數 `_is_rate_limit_error(e: Exception, error_message: str) -> bool`。
- 將內外部兩個迴圈中重複的 `isinstance(e, openai.RateLimitError) or "429" in ...` 替換為該函數呼叫。

## 驗證計畫 (Verification Plan)

### 自動化測試 (Automated Validation)
- `make test-be`: 確保重構與重試邏輯沒有破壞現有的 694 項單元測試，尤其是針對 Telegram 與爬蟲的 Mocks。
- `make lint-be`: 確保 `config_factory.py` 與 `telegram_service.py` 符合 Ruff 與 Mypy 強型別。
- `make phase-audit`: 確保 `excluded_tags` 的 SSOT 繞過標記遷移到工廠方法後，維持 0 違規。
