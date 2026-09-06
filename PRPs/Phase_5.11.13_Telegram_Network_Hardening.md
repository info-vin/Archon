# Phase 5.11.15: Telegram Network Hardening (IPv6 Blackhole Defense)

## 📌 背景 (Context)
在 Phase 5.11.11 的硬化中，我們為 `TelegramService` 導入了 `timeout=30.0` 與 3 次重試機制，意圖防範網路突波。然而，在實際營運環境 (Hugging Face Spaces 等 Docker 雲端主機) 中，依然連續遭遇 3 次 `ConnectTimeout` 失敗。

經由 Git Log 溯源與實體除錯（與本地端 `test_telegram2.py` 的對照），確認這並非暫時性網路突波，而是著名的 **IPv6 Blackhole (路由黑洞)** 缺陷。`httpx.AsyncClient` 預設啟用雙棧 (Happy Eyeballs)，當解析到 Telegram 伺服器的 IPv6 位址時會優先嘗試，但在缺乏 IPv6 對外路由的雲端環境中，封包會遭到靜默丟棄 (Blackholed)，導致程式死等直到 30 秒觸發超時。

## 🎯 目的 (Objectives)
1.  **根除網路黑洞**：在 `telegram_service.py` 實作底層的 IPv4 強制綁定，避開會引發超時的 IPv6 路由。
2.  **拒絕硬編碼與 DRY**：將強制 IPv4 的行為、超時秒數封裝為模組化設定，避免四處散落 `0.0.0.0` 字串。
3.  **零虛假公證**：實作一個包含自動化斷言 (Assertion) 的整合型驗證腳本，證明 HTTP Transport 確實綁定了 IPv4。

## 🛠️ 實作計畫 (Implementation Plan)

### 1. `telegram_service.py` 網路傳輸層硬化
*   **不硬編碼**：使用原生的 `httpx.AsyncHTTPTransport` 並透過 `local_address="0.0.0.0"` 強制底層 Socket 只綁定 IPv4。
*   **防禦性連線池**：配置合理的 `retries` 與連線屬性，徹底解決 `ConnectTimeout`。

### 2. 自動化驗證門禁 (Automated Verification)
*   **拒絕肉眼驗證**：撰寫 `python/tests/test_telegram_network.py` 或直接利用專案內的 `make test-be` 體系，透過 `pytest` 與 `patch` 檢驗 `httpx.AsyncClient` 實例化時，其 Transport 屬性是否 100% 被設定為 `local_address="0.0.0.0"`，證明我們的防禦機制真實存在，且在沒有網路連線的情境下也能透過單元測試攔截退化 (Regression)。

## ⚠️ 防禦機制檢核 (Defensive Checks)
*   [ ] **悲觀路徑防禦**：確保如果 `httpx` 即便在 IPv4 下也拋出異常，依然能觸發 `_log_to_db("ERROR", ...)` 並寫入資料庫供 UI 檢視。
*   [ ] **SSOT 對齊**：不改變原有的 `NotificationConfig` 取值邏輯，保持 `bot_token` 與 `chat_id` 來自單一資料源。
