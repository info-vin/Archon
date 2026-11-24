# Phase 5.13: 資安權限加固、金鑰零中斷輪換與白名單排程實作計畫 (PRP)

## 1. 背景與目標 (Background & Objectives)

本計畫針對以下 6 項系統安全與營運決策，整合代碼庫實體盤點結果，制定「零中斷、不改 A 壞 B」的執行藍圖，並明確區分 **程式自動化修復 (Code Changes)** 與 **外部平台人工操作檢查點 (Manual Ops Checkpoints)**：

| # | 決策項目 | 程式現況實證 | 本計畫對策 |
| :--- | :--- | :--- | :--- |
| **1** | 關閉開放註冊＋修補假冒管理員漏洞 | [dependencies.py](file:///Users/vincenta/GoogleKwok022/Archon/python/src/server/auth/dependencies.py#L102-L113) 在找不到 `profiles` 時信任 `user_metadata.get("role")`；[AuthPage.tsx](file:///Users/vincenta/GoogleKwok022/Archon/enduser-ui-fe/src/pages/AuthPage.tsx) 仍留有死掉的註冊切換 UI。 | **程式**：移除 `user_metadata["role"]` 權限提升路徑與死註冊 UI。<br>**人工**：於 Supabase Dashboard 關閉 Allow new users to sign up。 |
| **2** | 換資料庫鑰匙時 AI 功能 0 中斷 | [crypto_utils.py](file:///Users/vincenta/GoogleKwok022/Archon/python/src/server/services/credentials/crypto_utils.py#L16-L27) 直接使用 `SUPABASE_SERVICE_KEY` 衍生 Fernet 金鑰；[manager.py](file:///Users/vincenta/GoogleKwok022/Archon/python/src/server/services/credentials/manager.py#L154-L161) 解密失敗直接回傳 `None` 且未走環境變數 fallback。 | **程式**：將加密金鑰解耦為獨立 `CREDENTIAL_ENCRYPTION_KEY`，支援雙金鑰解密 fallback 與環境變數降級保護，並提供一次性重加密腳本。 |
| **3** | 13 個舊網站部署清理時機 | 舊部署屬於外部託管平台資源，無法透過本地程式碼直接刪除。 | **人工**：依「先換完鑰匙 → 驗證線上服務正常 → 再刪除 13 個舊部署」順序執行。 |
| **4** | 順便換掉 Telegram 與 4 把 AI 金鑰 | 金鑰由 `credential_service` / 環境變數讀取。 | **人工**：至外部平台撤銷重發後，更新 `.env`、GitHub Secrets、HF Space Secrets 與 DB。 |
| **5** | 找客戶評分（員工人數 / 第二標註人 / 104 授權） | [lead_evaluator.py](file:///Users/vincenta/GoogleKwok022/Archon/python/src/server/services/crawling/lead_evaluator.py) 與 [lead_handler.py](file:///Users/vincenta/GoogleKwok022/Archon/python/src/server/services/marketing/lead_handler.py) 尚無 `employee_count` 欄位與規則；[job104_client.py](file:///Users/vincenta/GoogleKwok022/Archon/python/src/server/services/crawling/clients/job104_client.py) 為 `curl_cffi` 直連爬蟲。 | **人工＋程式銜接**：待人工補查約 60 家公司人數後再實作匯入與評分規則；建議以「主標註＋AI 固定 Rubric 盲測複核」替代第二位真人；建議向 104 申請正式授權並維持低頻 WAF 延遲。 |
| **6** | 白名單定期爬蟲（只抓 Google 2 頁） | `archon_crawler_targets` 已有 3 筆資料（農民曆 `update_frequency='manual'`、Google 2 頁為 `'bi-weekly'`），但 [scheduler_service.py](file:///Users/vincenta/GoogleKwok022/Archon/python/src/server/services/scheduler_service.py) 無對應排程任務。 | **程式**：新增白名單排程任務，依 `is_active=True` 且 `update_frequency != 'manual'` 條件定期抓取並更新 `last_crawled_at`。 |

---

## 2. Pre-Action Risk Assessment & Comprehensive Impact Analysis

### 2.1 潛在風險點與防禦設計
1. **金鑰切換空窗期導致解密失敗 (`InvalidToken`)**：
   - 若直接將 `CryptoUtils.get_encryption_key()` 改為讀取 `CREDENTIAL_ENCRYPTION_KEY`，而資料庫 `archon_settings` 仍存放舊 `SUPABASE_SERVICE_KEY` 加密的密文，會導致所有 AI 服務讀不到金鑰。
   - **防禦**：實作「主金鑰＋備援金鑰（舊鑰匙）」雙金鑰解密機制，並於輪換 `SUPABASE_SERVICE_KEY` **之前**執行 `scripts/reencrypt_credentials.py` 完成資料重加密。
2. **移除 `user_metadata["role"]` 影響既有整合測試**：
   - 依 `git grep` 盤查，包含 `test_phase49_rbac.py`、`test_x3_no_unverified_jwt_fallback.py`、`test_auth_api.py` 等測試均依賴 `get_current_user` 行為。
   - **防禦**：修改前先檢視所有 `get_current_user` 相關測試，確保找不到 `profiles` 時仍回傳最低權限 `"employee"`（或依測試預期處理），僅阻斷從 `user_metadata` 讀取任何特權角色（`admin` / `system_admin` / `manager`）。
3. **移除前端註冊 UI 破壞 `AuthPage.test.tsx`**：
   - `enduser-ui-fe/src/pages/AuthPage.tsx` 移除了 `register` 切換後，需同步檢查 `AuthPage.test.tsx`、`useAuth.tsx` 與 `services/api/auth.ts` 的引用與型別。

---

## 3. 分階段實作步驟 (Implementation Plan)

### Track A：金鑰解耦與零中斷輪換前置（優先執行）
1. **修改 [config.py](file:///Users/vincenta/GoogleKwok022/Archon/python/src/server/config/config.py)**：
   - 讀取可選環境變數 `CREDENTIAL_ENCRYPTION_KEY` 與 `PREVIOUS_SUPABASE_SERVICE_KEY`（供雙金鑰過渡期使用）。
2. **修改 [crypto_utils.py](file:///Users/vincenta/GoogleKwok022/Archon/python/src/server/services/credentials/crypto_utils.py)**：
   - 加密 (`encrypt_value`)：優先使用 `CREDENTIAL_ENCRYPTION_KEY`（若未設定才退回 `supabase_service_key` 衍生，維持本地開發相容）。
   - 解密 (`decrypt_value`)：依序嘗試 `[CREDENTIAL_ENCRYPTION_KEY, supabase_service_key, PREVIOUS_SUPABASE_SERVICE_KEY]`，全部失敗才拋出異常。
3. **修改 [manager.py](file:///Users/vincenta/GoogleKwok022/Archon/python/src/server/services/credentials/manager.py#L154-L173)**：
   - 當 `CryptoUtils.decrypt_value` 失敗時，記錄 `logger.error` 後**不直接 `return default`**，改為繼續往下執行 `os.getenv(key)` 環境變數 fallback，確保服務不中斷。
4. **新增 `scripts/reencrypt_credentials.py`**：
   - 掃描 `archon_settings` 中 `is_encrypted = True` 的資料列，使用舊金鑰解密後，以 `CREDENTIAL_ENCRYPTION_KEY` 重新加密並寫回（支援 `--dry-run` 預覽）。
5. **人工操作檢查點 (Checklist)**：
   - [ ] 產生一組獨立的 `CREDENTIAL_ENCRYPTION_KEY` 並寫入本機 `.env`、GitHub Secrets、HF Space Secrets。
   - [ ] 部署 Track A 程式碼，執行 `uv run python scripts/reencrypt_credentials.py` 完成資料庫密文轉換。
   - [ ] 至 Supabase Dashboard 輪換 `SUPABASE_SERVICE_KEY`（與 anon key 視需求），更新 `.env` / Secrets。
   - [ ] 至 Telegram `@BotFather` 與 4 家 AI 服務商輪換金鑰，更新 `.env` / Secrets / `archon_settings`。
   - [ ] 確認線上 `/health` 與 AI 服務正常後，**刪除 13 個舊網站部署**。

---

### Track B：關閉開放註冊與修補權限提升漏洞
1. **修改 [dependencies.py](file:///Users/vincenta/GoogleKwok022/Archon/python/src/server/auth/dependencies.py#L102-L113)**：
   - 刪除讀取 `auth_user.user_metadata.get("role")` 的邏輯。
   - 當 `profiles` 表查無該 `user_id` 時，強制固定 `fallback_role = "employee"`（嚴禁從 `user_metadata` 賦予任何管理員或高權限角色），並記錄安全告警日誌。
2. **修改前端註冊 UI（`enduser-ui-fe`）**：
   - [AuthPage.tsx](file:///Users/vincenta/GoogleKwok022/Archon/enduser-ui-fe/src/pages/AuthPage.tsx)：移除 `isLogin` 切換與「Create a new account / Sign up」表單（遵循 `UI_STANDARDS.md` 與移除 dead code 原則）。
   - [useAuth.tsx](file:///Users/vincenta/GoogleKwok022/Archon/enduser-ui-fe/src/hooks/useAuth.tsx) / [auth.ts](file:///Users/vincenta/GoogleKwok022/Archon/enduser-ui-fe/src/services/api/auth.ts) / [AuthPage.test.tsx](file:///Users/vincenta/GoogleKwok022/Archon/enduser-ui-fe/src/pages/AuthPage.test.tsx)：同步清理無效的 `register` 呼叫並更新單元測試。
3. **人工操作檢查點 (Checklist)**：
   - [ ] 至 Supabase Dashboard → Authentication → Sign In / Providers 關閉 **Allow new users to sign up**。

---

### Track C：白名單定期爬蟲排程（只抓 Google 2 頁）
1. **新增 `python/src/server/services/scheduler/jobs/crawler_patrol.py`**：
   - 查詢 `archon_crawler_targets` 中 `is_active = True` 且 `update_frequency != 'manual'` 的目標（自然排除 `'manual'` 的農民曆，僅涵蓋 `'bi-weekly'` 的 2 頁 Google Gemini 官方文件）。
   - 依據 `last_crawled_at` 與 `update_frequency`（如 `daily` = 1 天、`weekly` = 7 天、`bi-weekly` = 14 天、`monthly` = 30 天）判斷是否到期。
   - 到期目標呼叫 `CrawlingService().orchestrate_crawl(...)` 抓取並更新 `last_crawled_at`。
2. **修改 [scheduler_service.py](file:///Users/vincenta/GoogleKwok022/Archon/python/src/server/services/scheduler_service.py)**：
   - 在 Category 4 註冊週期性排程 `_run_whitelist_crawler_patrol`，依 `SchedulerConfig` 定期檢查並執行到期白名單目標。

---

### Track D：客戶評分人工補查與標註銜接（待外部資料就緒後展開）
1. **資料與規則銜接**：待您人工補查約 60 家公司員工人數並提供清單後，檢查 `leads` 表結構並新增 `employee_count` 欄位（如有需要）及將規模篩選/權重接進 `lead_handler.py` / `lead_evaluator.py`。
2. **標註與授權建議**：
   - 第二標註者：採用「您為主標註＋AI 依固定 Rubric 盲測複核分歧點」流程。
   - 104 授權：向 104 提出正式合作/授權詢問；未獲授權前維持低頻率與 WAF 隨機延遲。

---

## 4. 驗收標準與品質門禁 (Acceptance Criteria)
- [x] **後端靜態檢查**：`ruff check`（針對所有修改與新增檔案）與 `mypy src/`（397 檔）0 錯誤。
- [x] **後端單元測試**：全量非整合單元測試通過 **807 passed**（排除離線沙盒無法解析 DNS 之 `external/test_104_reliability.py` 與待 `uv sync` 升級 `supabase 2.18.0` 之 `test_supabase_client_construction.py`），且包含：
  - `CryptoUtils` 獨立金鑰加解密與舊金鑰 fallback 單元測試。
  - `CredentialManager` 解密失敗時仍能 fallback 至環境變數之測試。
  - `get_current_user` 忽略 `user_metadata.role = "system_admin"` 強制回傳 `"employee"` 之安全測試。
  - `crawler_patrol` 過濾 `update_frequency == "manual"` 並只執行到期目標之單元測試。
- [x] **前端檢查與測試**：`enduser-ui-fe` `tsc --noEmit`（0 錯誤）與 `AuthPage.test.tsx`（3/3 passed）。
- [x] **系統公證**：`scripts/phase_audit.py` Step 5.5、7、8、9、10、11 全門禁通過。
