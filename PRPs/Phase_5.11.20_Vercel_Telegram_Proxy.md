# Phase 5.11.20: Vercel 代理突破 HF 防火牆 (Telegram Egress Bypass)

## 📌 背景與物理真相 (Context & Physical Truth)
經過實體驗證與網路查證，`ConnectTimeout` 並非 IPv6 黑洞或單純的網路不穩，而是 **Hugging Face Spaces 官方的平台防火牆 (Egress Firewall)** 蓄意攔截了對 `api.telegram.org` 的對外連線（用以防範惡意機器人濫用免費資源）。
此封鎖會將封包默默丟棄 (Drop) 而不立即拒絕，導致 `httpx` 掛起直到觸發 30 秒逾時。

## 🎯 目標 (Objectives)
在【不搬離 HF Spaces】且【不更改 SSOT 資料庫架構】的前提下，利用目前已部署於 Vercel 的前端專案 (`enduser-ui-fe`) 作為反向代理 (Reverse Proxy)，合法繞過 HF 的防火牆限制。

## 🛠️ 實作計畫 (Implementation Plan)

### 1. 前端端點：Vercel Serverless Function (`enduser-ui-fe`)
*   **路徑**：新增 `enduser-ui-fe/api/telegram.ts`。
*   **職責**：
    *   接收來自 HF 後端的 POST 請求（含 `bot_token`, `chat_id`, `text`, `parse_mode`）。
    *   於 Vercel 的 AWS Lambda 網路環境中（不受 Telegram 封鎖），使用原生 `fetch` 轉發至 `https://api.telegram.org/bot{bot_token}/sendMessage`。
    *   將 Telegram 的回應原封不動回傳給後端。

### 2. 後端端點：HF Spaces 發送邏輯修改 (`telegram_service.py`)
*   **動態路由與防雷機制 (改A不壞B)**：不硬編碼 `FRONTEND_URL` 以免破壞本地開發 (Local Vite Server 預設不支援 `/api` 解析)。
    *   在 `NotificationConfig` 新增 `TELEGRAM_PROXY_URL`。
    *   **邏輯**：
        1. 若設定了 `TELEGRAM_PROXY_URL` (例如在 HF 雲端環境中)，則使用 Proxy 發送，並將 `bot_token` 放進 JSON Payload 中。
        2. 若未設定 (例如本地開發環境，網路暢通)，則無縫降級回原生直連模式 (`https://api.telegram.org/...`)，確保本地開發完全不受影響。

## 🛡️ 邊界防禦與原則對齊 (Defensive Checks)
*   **SSOT 絕對遵循**：Token 與設定仍然 100% 由後端的 Supabase `archon_settings` 管理。Vercel 僅作為無狀態的代理層 (Stateless Proxy)，不儲存任何金鑰。
*   **環境回退相容**：若 `FRONTEND_URL` 遺失，系統會依賴 `NetworkConfig` 的預設值 (`https://archon-enduser.vercel.app`) 保底發送。

## 🧪 自動化公證 (Automated Verification)
*   於 `tests/services/test_telegram_persistence.py` (或新建專用測試) 增加以下斷言：
    1.  **路由攔截斷言 (Route Assertion)**：攔截 `httpx.AsyncClient.post`，斷言發送目標網址必須是 `{FRONTEND_URL}/api/telegram`，絕不可出現 `api.telegram.org`。
    2.  **負載完整性斷言 (Payload Integrity)**：斷言 JSON Payload 內確實包含了 `bot_token` 與 `chat_id`，確保憑證順利轉交給 Proxy。
