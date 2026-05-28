# Phase 5.4.4: Supabase 資料庫效能與 Schema 優化計畫 & 執行結果

本計畫旨在說明如何檢測當前 Supabase 資料庫中的資料表、清理或整合未使用的空白資料表、在 `.env` 中配置**會話模式 (Session Mode - 5432)** 與**交易模式 (Transaction Mode - 6543)** 的連線，並在不清空或損壞任何現有資料的前提下，安全地套用效能索引。

## 使用者審查確認

> [!IMPORTANT]
> **資料安全與分支管理（最安全原則）：**
> 1. **建立新分支**：所有變更將在新建的獨立分支 `feature/supabase-db-optimization` 上進行，通過驗證後才合併，確保主分支安全。
> 2. **非破壞性原則**：所有 Schema 與資料表的清理將採用「增量遷移 (Incremental Migrations)」方式執行（透過 `make db-migrate` 執行 `ALTER` / `DROP TABLE IF EXISTS` / `CREATE INDEX IF NOT EXISTS`），而非破壞性的重置（如 `db-reset` 或 `--clean`），以確保線上資料安全無虞。
> 3. **手動備份**：在對生產環境資料庫進行任何清理前，強烈建議先透過 Supabase 控制台或 `pg_dump` 進行手動備份。

## 建議變更與設計

### 第一階段：資料庫 Schema 審計與空白資料表清理
1. **資料表審計與使用率確認**：
   - 建立並執行獨立工具腳本 `scripts/audit_empty_tables.py`，查詢 Postgres 系統目錄 (`pg_stat_user_tables`) 並統計資料列分布，以找出資料列為 `0` 的空白表。
   - 將這些空白表與實際程式碼進行交叉比對（使用 `grep` 搜尋），並分類為作用中與孤立表。

### 第二階段：`.env` 雙連線池模式配置 (基於 Supabase 官方文件規範)
根據 Supabase 官方文件，針對不同的資料庫任務應分流至正確的連線埠：
- **會話模式 (Session Mode - 埠號 5432)**：具備會話狀態，**執行資料庫遷移 (Migrations)、`pg_dump` 備份與 CLI 工具時必須使用此模式**。
- **交易模式 (Transaction Mode - 埠號 6543)**：高併發、無狀態連線複用，適合一般應用程式查詢流量（如 API 伺服器）。
1. **更新 `.env` 與 `.env.example`**：
   - 定義 `SUPABASE_DB_SESSION_URL` (Port 5432) 與 `SUPABASE_DB_TRANSACTION_URL` (Port 6543)。

### 第三階段：效能加固與索引建立
套用目標索引以加速日常查詢（如 Nexus 趨勢看板和 RAG 向量檢索）：
1. **B-Tree 索引**：針對高頻查詢的外鍵與狀態欄位建立複合索引。
2. **RAG 向量檢索加速**：將 `embedding` 向量索引由 ivfflat 升級為 **`HNSW`** 索引，防止全表掃描。
3. **執行方式**：包裝至 `22_add_performance_indexes.sql` 中，並運行 `make db-migrate` 執行。

---

## 執行結果一：Supabase 資料表審計與使用率分析報告

- **審計時間**: 2026-05-28
- **資料來源**: `pg_stat_user_tables` & 靜態代碼掃描

### 所有資料表使用情況總覽

| 資料表名稱 | 資料列數量 | 程式碼引用次數 | 循序掃描 (Seq Scan) | 索引掃描 (Idx Scan) | 寫入次數 (Inserts) | 狀態與建議 |
| --- | --- | --- | --- | --- | --- | --- |
| `archon_code_examples` | 0 | 5 | 38 | 271 | 0 | 🟡 Active (0 rows, referenced in code) |
| `archon_crawled_pages` | 123 | 20 | 2064 | 607 | 372 | 🟢 Active (Has Data) |
| `archon_crawler_targets` | 3 | 6 | 121 | 4 | 3 | 🟢 Active (Has Data) |
| `archon_document_versions` | 255 | 12 | 1448 | 19 | 263 | 🟢 Active (Has Data) |
| `archon_ethics_events` | 0 | 6 | 133 | 1 | 0 | 🟡 Active (0 rows, referenced in code) |
| `archon_extraction_schemas` | 0 | 5 | 57 | 1 | 0 | 🟡 Active (0 rows, referenced in code) |
| `archon_logs` | 1278 | 51 | 707 | 3023 | 1281 | 🟢 Active (Has Data) |
| `archon_project_sources` | 0 | 4 | 256 | 1230 | 0 | 🟡 Active (0 rows, referenced in code) |
| `archon_projects` | 3 | 34 | 2653 | 400 | 131 | 🟢 Active (Has Data) |
| `archon_prompts` | 22 | 3 | 2199 | 574 | 37 | 🟢 Active (Has Data) |
| `archon_roles_permissions` | 7 | 3 | 256 | 215 | 7 | 🟢 Active (Has Data) |
| `archon_settings` | 61 | 28 | 8267 | 10818 | 532 | 🟢 Active (Has Data) |
| `archon_sources` | 32 | 33 | 1604 | 1222 | 271 | 🟢 Active (Has Data) |
| `archon_tasks` | 60 | 24 | 21361 | 34448 | 379 | 🟢 Active (Has Data) |
| `attendance_logs` | 0 | 1 | 7 | 592 | 0 | 🟡 Active (0 rows, referenced in code) |
| `blog_posts` | 12 | 18 | 1667 | 212 | 54 | 🟢 Active (Has Data) |
| `gemini_logs` | 60 | 0 | 19 | 0 | 63 | 🟢 Active (Has Data) |
| `leads` | 78 | 421 | 7093 | 1119 | 559 | 🟢 Active (Has Data) |
| `marketing_trends` | 0 | 2 | 347 | 0 | 0 | 🟡 Active (0 rows, referenced in code) |
| `profiles` | 7 | 91 | 11855 | 11286 | 423 | 🟢 Active (Has Data) |
| `proposed_changes` | 8 | 7 | 53 | 98 | 8 | 🟢 Active (Has Data) |
| `schema_migrations` | 29 | 5 | 82 | 34 | 32 | 🟢 Active (Has Data) |
| `token_usage` | 458 | 16 | 964 | 1317 | 458 | 🟢 Active (Has Data) |
| `vendors` | 2 | 3 | 7 | 4 | 2 | 🟢 Active (Has Data) |
| `visit_logs` | 2 | 6 | 290 | 2 | 6 | 🟢 Active (Has Data) |

### 建議清理的孤立資料表 (Possibly Orphaned)

✅ **未發現任何無程式碼引用且無資料的孤立資料表**。所有的空白資料表均在代碼庫中有對應的引用或系統預留用途，因此本階段不執行任何 `DROP TABLE` 刪除操作，保留完整 Schema。

---

## 執行結果二：Verification Walkthrough

本章節記錄了 Phase 5.4.4 的實作變更與驗證通過狀態。

### 1. 雙連線池模式分流配置
- **`.env` 與 `.env.example`**：配置了 `SUPABASE_DB_SESSION_URL` (Port 5432) 與 `SUPABASE_DB_TRANSACTION_URL` (Port 6543)，並讓 `SUPABASE_DB_URL` 預設回退至 Session 埠以保證相容性。
- **`docker-compose.yml`**：已將雙連線變數傳遞至 `archon-server` 容器。
- **`scripts/init_db.py`**：更新環境變數優先級，強制优先連線 Session Mode。

### 2. 效能加固與索引套用
- 新增非破壞性遷移腳本 `migration/0.2.2/22_add_performance_indexes.sql`：
  - 將 `archon_crawled_pages` 與 `archon_code_examples` 的 `embedding` 索引從 `ivfflat` 升級為 **`HNSW` 索引**，優化 RAG 檢索。
  - 針對高頻查詢條件建立複合 B-Tree 索引：`archon_tasks(assignee_id, status)`、`leads(status, enrichment_score)`、`archon_logs(level, type)`、`token_usage(provider, cost_usd DESC)`。
- 透過 `make db-migrate` 成功執行，現有測試資料無損且完整。

### 3. 自動化與角色門禁驗證
- **`make check`**：通過環境預檢。
- **`make lint`**：Ruff、Mypy、ESLint 與 Biome 100% 通過，無程式碼風格警告。
- **`make test-be`**：**575 個後端單元與整合測試 100% 通過**，零錯誤。
- **`make persona-audit`**：Alice、Bob、Charlie、David 與 AI Agents 實體通訊與 HUD 端點全數 **200 OK**，業務功能暢通。
