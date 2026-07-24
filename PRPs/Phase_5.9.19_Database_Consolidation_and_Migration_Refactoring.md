# Phase 5.9.19: Database Consolidation & Migration Refactoring (0.2.3)

## 📌 Executive Summary

本階段（Phase 5.9.19）旨在解決 `migration/0.2.2/` 歷經 Phase 5.1 至 5.8 演進後，累積高達 36 個碎片化 SQL 檔案引發的維護難題。
透過「三層職責分離 (Layered Separation)」與「領域收斂」，我們將 36 個歷史腳本收斂整合至全新的 `migration/0.2.3/` 目錄。

本計畫嚴格遵守 SSOT（單一事實來源）與 `scripts/init_db.py` 底層代碼機制，確保：
1. **0% 資料遺失**：實體線上真實資料備份檔 (160 KB) 被安全隔離並劃分。
2. **0% 自動語法風險**：嚴格維護 `RESET_DB.sql` 與 `seed_*.sql` 的硬編碼名稱防線，防止 Migration 自動排序誤跑或重置崩潰。
3. **100% 行數與位元數數據守恆**：全數 5,592 行 SQL 程式碼對齊守恆。

---

## 🎯 SSOT & `init_db.py` 程式碼硬性限制規範

在進行 0.2.3 資料庫重構時，必須物理遵守 `scripts/init_db.py` 的以下核心邏輯：

1. **`RESET_DB.sql` 檔名不可帶編號**：
   - `init_db.py` 的 `run_migrations()` 寫死排除 `RESET_DB.sql`。若加上數字前綴（如 `08_RESET_DB.sql`），會在常規 Migration 中被自動載入並**誤將資料庫清空**。
   - `main()` 在 `--clean` 模式下寫死讀取 `migration/{version}/RESET_DB.sql`。
2. **`seed_*.sql` 檔名不可帶編號**：
   - `seed_data()` 寫死呼叫 `seed_mock_data.sql`、`seed_blog_posts.sql` 與 `seed_rag_defaults.sql`。若加數字編號，`seed_data()` 會找不到檔案，且會被 `run_migrations()` 視為常規 Migration 誤跑。
3. **`rescue/` 子目錄隔離機制**：
   - `run_migrations()` 使用 `glob.glob("migration/{version}/*.sql")` 只讀取單層。將 160 KB 的真實資料隔離至 `rescue/` 子目錄，可防範自動 Migration 誤跑巨型數據，並提供選擇性還原彈性。

---

## 📐 0.2.3 最終目錄結構與 36 檔對照表 (數據守恆 5,592 行)

```text
migration/0.2.3/
├── 01_schema_core.sql              #  262 行 |  7.47 KB (型別, Enum, Profiles, Core 表)
├── 02_schema_features.sql          #  935 行 | 30.60 KB (CRM, RAG, Ops, Agent, Checkpoints 表)
├── 03_logic_functions.sql          # 1357 行 | 44.04 KB (RPC 函數, 索引, Triggers, 外鍵)
├── 04_logic_security_rls.sql       #  870 行 | 29.71 KB (全資料表 RLS 安全存取政策)
├── 05_seed_system_configs.sql      #  259 行 | 11.45 KB (系統參數, RBAC 矩陣, 爬蟲目標)
├── 06_seed_prompts_core.sql        #  389 行 | 18.20 KB (Supervisor, Marketing 核心提示詞)
├── 07_seed_prompts_assets.sql      #  155 行 | 29.28 KB (大型美術與導航 Icon 提示詞)
│
├── RESET_DB.sql                    # 🔒 343 行 | 13.76 KB (【固定檔名】僅 --clean 時呼叫)
├── seed_mock_data.sql              # 🔒 194 行 |  8.71 KB (【固定檔名】預設假數據)
├── seed_blog_posts.sql             # 🔒 447 行 | 33.36 KB (【固定檔名】部落格假文章)
├── seed_rag_defaults.sql           # 🔒  47 行 |  3.88 KB (【固定檔名】RAG 預設知識庫)
│
└── rescue/                         # 🛠️ 【隔離子目錄】真實資料救援庫 (不被自動 Migration 誤跑)
    ├── leads.sql                   #        -- | 70.58 KB (88 筆真實商機 AI 情資數據)
    ├── prompts.sql                 #        -- |  6.63 KB (自訂 MapReduce & TTS 提示詞)
    └── sources_and_targets.sql     #        -- | 33.11 KB (爬蟲目標與真實 RAG 來源數據)
```

### 📋 36 個舊檔案精確歸納明細 (100% 映射)

| 預計 0.2.3 標的檔案 | 涵蓋的 0.2.2 舊子檔案明細 (共 36 檔) |
| :--- | :--- |
| **`01_schema_core.sql`** | `01_foundation_types.sql`, `02_tables_core.sql`, `25_create_user_game_saves.sql`, `30_alter_archon_prompts_schema.sql` (4檔) |
| **`02_schema_features.sql`** | `03_tables_business.sql`, `04_tables_ops.sql`, `24_create_dynamic_agent_tables.sql`, `28_graphrag_and_mrl.sql`, `33_create_agent_checkpoints_and_approvals.sql` (5檔) |
| **`03_logic_functions.sql`** | `05_logic_functions.sql`, `06_constraints_main.sql`, `07_logic_indexes.sql`, `08_logic_triggers.sql`, `09_constraints_fkeys.sql`, `26_rag_hybrid_match_chunks.sql`, `100_add_tiered_pruning_rpcs.sql` (7檔) |
| **`04_logic_security_rls.sql`** | `10_security_rls.sql`, `27_enable_missing_rls.sql` (2檔) |
| **`05_seed_system_configs.sql`** | `11_seed_config.sql`, `12_seed_rbac.sql`, `18_seed_crawler_targets.sql` (3檔) |
| **`06_seed_prompts_core.sql`** | `19_seed_marketing_group_chat_prompts.sql`, `20_seed_supervisor_agent.sql`, `21_seed_reports_workflow_prompts.sql`, `22_seed_devbot_math_prompt.sql`, `23_seed_agent_system_prompts.sql`, `29_seed_job_board_prompts.sql`, `101_update_supervisor_prompt.sql`, `102_seed_patrol_prompts.sql` (8檔) |
| **`07_seed_prompts_assets.sql`** | `31_seed_art_asset_prompts.sql`, `32_seed_nav_icons_prompts.sql` (2檔) |
| **`RESET_DB.sql`** | `RESET_DB.sql` (1檔) |
| **`seed_mock_data.sql`** | `seed_mock_data.sql` (1檔) |
| **`seed_blog_posts.sql`** | `seed_blog_posts.sql` (1檔) |
| **`seed_rag_defaults.sql`** | `seed_rag_defaults.sql` (1檔) |
| **`rescue/` (隔離目錄)** | `99_rescue_live_data.sql` (1檔，拆分為 `leads.sql`, `prompts.sql`, `sources_and_targets.sql`) |

---

## 🧪 驗證計畫 (Verification Plan)

實作 0.2.3 重構時，必須執行以下驗證關卡：

1. **靜態程式碼與型別掃描**：
   ```bash
   make lint-be
   ```
2. **後端全套單元與整合測試**：
   ```bash
   make test-be
   ```
3. **品質門禁與動態健康度掃描**：
   ```bash
   make phase-audit
   ```
