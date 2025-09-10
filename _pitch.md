# 部署驗證 Spike 學習經驗

**執行分支**: `spike/verify-deployment-pipeline`

## 發現問題

在本地模擬部署 (`docker compose up`) 後，服務容器雖然成功啟動，但 `/health` 健康檢查端點回報了 `{"status":"migration_required"}` 錯誤。

## 根本原因

資料庫的結構 (Schema) 與目前程式碼所預期的不符。這通常發生在有新的資料庫變更（例如：新增資料表欄位）合併到主分支後，但對應的資料庫遷移 (migration) 尚未在目標環境中執行。

## 解決方案與建議

1.  **識別腳本**: 檢查服務日誌或 `/health` 端點的回應，找到需要執行的遷移腳本名稱。在本次驗證中，發現需要執行 `migration/add_source_url_display_name.sql`。
2.  **執行遷移**: 前往 Supabase 專案儀表板的 "SQL Editor"，複製並貼上對應的 SQL 腳本內容，然後執行它。
3.  **重啟服務**: 重新啟動服務後，再次檢查 `/health` 端點，應回傳 `{"status":"ok"}`。

**給團隊的建議**: 應將「執行資料庫遷移」作為部署標準作業流程 (SOP) 的一部分，在部署新版本程式碼 *之前* 執行，以避免服務啟動失敗。
