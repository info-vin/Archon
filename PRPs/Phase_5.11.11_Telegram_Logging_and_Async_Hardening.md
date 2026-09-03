# 實作計畫 - Telegram 非同步硬化與 UI 日誌盲區公證 (Phase 5.11.11)

## 目標 (Goal)
解決 Hugging Face Spaces 等環境下，Telegram 定期報告發送失敗卻在 UI 上「完全查無錯誤 (Ghost Logs)」的問題。
1.  **打通日誌盲區**：強制將 Telegram 網路阻擋或超時錯誤，寫入至 `archon_logs`，讓 Admin UI 可以 100% 監控真實的網路狀況。
2.  **修復 5 秒同步陷阱**：將原本會阻塞 Event Loop 的 `_get_config()` 升級為非同步 (`asyncio.to_thread`) 且具備 3 次重試機制的架構，防止在剛完成重度 Map-Reduce 運算後，因 `httpx.Client` 預設的 5 秒連線卡頓而靜默跳過整個警報發送。

## 使用者審查項目 (User Review Required)

> [!IMPORTANT]
> - 本計畫將使 `telegram_service.py` 具備主動向資料庫寫入 ERROR 的能力。
> - 未來若 HF Spaces 再度遭遇 AWS 節點對 `api.telegram.org` 的連線阻擋，您將能直接在 Admin UI 的「System Logs」面板看到明確的「Network error sending message」紅字，不再需要靠猜測除錯。

## 預計變更 (Proposed Changes)

### 系統層 - Telegram 服務

#### [MODIFY] [telegram_service.py](file:///Users/vincenta/GoogleKwok022/Archon/python/src/server/services/system/telegram_service.py)

1.  **新增 `_log_to_db` 內部方法**：
    *   使用 `asyncio.to_thread` 封裝 `get_supabase_client().table("archon_logs").insert()`。
    *   確保日誌寫入時不會阻塞主執行緒。
2.  **重構 `_get_config` 為 `_get_config_async`**：
    *   將 `SettingsService(supabase).get_all_settings()` 包裝入 `asyncio.to_thread`。
    *   加入 3 次重試迴圈 (`asyncio.sleep(2)`)，大幅增強在 HF Spaces 高延遲環境下取得 Token 的成功率。
    *   若重試 3 次仍失敗（大於 15 秒以上），呼叫 `_log_to_db("ERROR", "Failed to fetch settings from DB")` 並回傳空設定。
3.  **發送失敗與日誌穿透 (`send_message`)**：
    *   將原本只列印在 Console 的 `logger.error`，同步呼叫 `await self._log_to_db("ERROR", ...)`。
    *   這包括 HTTP 400/401 錯誤，以及 3 次 30 秒 `RequestError` 皆失敗後的最終網路報錯。

## 驗證計畫 (Verification Plan)

### 自動化測試 (Automated Tests)
新增單元測試 `python/tests/services/test_telegram_service_hardening.py`，包含以下斷言 (Assertions)：
1.  **非同步安全斷言**：使用 `unittest.mock.patch` 模擬 `SettingsService.get_all_settings`，設定其會發生逾時 (TimeoutError)，驗證 `_get_config_async` 能夠正確捕捉例外、執行重試，並最終非阻塞地回傳空設定，不會導致 Event Loop 崩潰。
2.  **日誌公證斷言**：模擬 `httpx.AsyncClient.post` 拋出 `httpx.RequestError` (網路斷線)，驗證 `send_message` 在經歷 3 次重試失敗後，能夠正確呼叫 `_log_to_db("ERROR", ...)`。
3.  **無設定降級斷言**：驗證當 `_get_config_async` 回傳無 Token 時，`send_message` 也會寫入 ERROR 日誌至 `archon_logs`。

執行指令公證：
```bash
uv run pytest tests/services/test_telegram_service_hardening.py -v
```
