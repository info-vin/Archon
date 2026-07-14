# Phase 5.9.2: 成本守門員與基礎設施巡檢 (Cost Sentinel & Infra Patrol)

## 🎯 階段目標 (Phase Goal)
建立嚴格的 API 成本監控防線，並針對系統三大核心基礎設施 (Vercel, Supabase, Hugging Face) 實作自動化物理巡檢，確保系統穩定並杜絕意外的預算超支。

## 📝 實作細節 (Implementation Details)

- `[x]` **Telegram 成本守門員 (Cost Sentinel)**:
  - 於 `business.py` 實作 `analyze_token_usage`。
  - 每 7 天為一週期，自動計算總 Token 消耗與換算金額 (USD)。
  - 若一週總花費超過 **$0.05 USD**，立即透過 `TelegramService` 發送緊急告警。
  - 實體對帳：使用資料庫的 `token_usage` 紀錄進行物理計算，絕不盲猜。

- `[x]` **基礎設施巡檢 (Infrastructure Patrol)**:
  - 於 `patrol.py` 實作 `run_infrastructure_audit`。
  - **Vercel**: 發送 HTTP GET 請求至前端 URL，確保無 500+ 錯誤。
  - **Supabase**: 執行原生 SQL (`pg_stat_activity`) 計算活躍連線數，避免連線數爆表 (>50 觸發警告)。
  - **Hugging Face**: 定期呼叫 Endpoint，防止 Serverless 機制陷入深眠導致 503/504 Timeout。
  - 於 `scheduler_service.py` 註冊為每日自動執行之常駐工作。

## 🛡️ 驗證與公證 (Verification)
- `[x]` 撰寫 `test_telegram_cost_sentinel.py` 確保 Telegram 告警邏輯與金額計算門檻正確。
- `[x]` 撰寫 `test_patrol_infra.py` 確保三大基礎設施的巡檢邏輯皆能正確捕捉例外狀態 (Mocked API)。
- `[x]` 通過 `make test-be` 與 `make phase-audit`，確保無代碼斷層與技術債。
