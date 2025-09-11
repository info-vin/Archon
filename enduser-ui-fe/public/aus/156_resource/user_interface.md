<img src="https://r2cdn.perplexity.ai/pplx-full-logo-primary-dark%402x.png" style="height:64px;margin-right:32px"/>

# 產生使用者設定的規則與畫面說明文件, 附上流程圖,讓後端工程師可以清楚的知道有哪些功能需要開發

以下文件描述使用者設定規則與畫面流程，並附上設定流程圖，後端工程師可據此了解需開發的功能模組與順序。

# 使用者設定功能需求文件

## 總覽

本系統允許使用者以單一電子郵件帳號註冊並設定多項AI服務（ChatGPT、Claude、Perplexity、Llama、Gemini、AgentZero），自動驗證並配置各服務憑證，檢視免費額度，最後完成設定儲存。

<流程圖>
chart:62

## 功能模組

### 1. 使用者帳號與郵件驗證

1. 顯示「輸入電子郵件地址」畫面
2. 前端：輸入欄位 + 驗證按鈕
3. 後端API：`POST /api/users/initiate_verification`
    - 參數：`email`
    - 回傳：`verification_id`
4. 顯示「驗證碼輸入」畫面
5. 後端API：`POST /api/users/verify_email`
    - 參數：`verification_id`, `code`
    - 回傳：`user_id`, `token`

### 2. 服務選擇

1. 顯示已支持的AI服務清單，含多選核取方塊
2. 前端：核取方塊UI，動態載入服務圖示與名稱
3. 無狀態API：`GET /api/services`
    - 回傳：`[{service_id, name, icon_url, description}]`

### 3. 憑證配置

1. 依選中服務，顯示對應憑證設定欄位（如API Key）
2. 前端：輸入欄位 + 說明文字
3. 後端API：`POST /api/users/{user_id}/credentials`
    - 參數：`service_id`, `credentials`
4. 驗證憑證有效性：
    - 伺服器端呼叫各服務API進行驗證

### 4. 免費額度檢視

1. 讀取並顯示各服務剩餘的免費額度
2. 後端API：`GET /api/users/{user_id}/quotas`
    - 回傳：`[{service_id, used, total, reset_date}]`
3. 前端：進度條 + 剩餘文字描述

### 5. 設定確認與儲存

1. 顯示所有已配置項目摘要
2. 按下「確認並儲存」後
3. 後端API：`PUT /api/users/{user_id}/settings`
    - 參數：`services_settings`
4. 回傳：`success` 或 `error`
5. 成功後導向「設定完成」畫面

## 畫面清單

| 畫面名稱 | 路由 | 主要元件 |
| :-- | :-- | :-- |
| 輸入電子郵件 | /settings/email | EmailInput, VerifyButton |
| 驗證碼輸入 | /settings/email/verify | CodeInput, SubmitButton |
| 服務選擇 | /settings/services | ServiceCheckboxList, NextButton |
| 憑證配置 | /settings/services/credentials | CredentialFormList, ValidateButton |
| 免費額度檢視 | /settings/quotas | QuotaProgressBars, InfoTooltip |
| 確認與儲存 | /settings/summary | SummaryList, ConfirmButton |
| 設定完成 | /settings/done | SuccessMessage, GoHomeButton |


***

以上文件與流程圖可協助後端工程師快速了解需實作的API端點與邏輯流程，並與前端協同完成畫面開發。

