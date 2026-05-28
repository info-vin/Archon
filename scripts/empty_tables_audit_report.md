# Supabase 資料表審計與使用率分析報告

- **審計時間**: 2026-05-28 15:34:12
- **資料來源**: pg_stat_user_tables & 靜態代碼掃描

## 1. 所有資料表使用情況總覽

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

## 2. 建議清理的孤立資料表 (Possibly Orphaned)

✅ 未發現任何無程式碼引用且無資料的孤立資料表。
