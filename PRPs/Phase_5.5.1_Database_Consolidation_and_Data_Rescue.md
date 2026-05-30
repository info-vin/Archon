# Phase 5.5.1: 資料庫整併、活體資料救援與種子現代化計畫 (Database Consolidation & Data Rescue)

## 核心目標 (Objective)
承接 Phase 5.5.0 的「離線硬化」架構，為了讓系統能在無網環境下快速、乾淨地啟動本地資料庫，我們必須對臃腫的資料庫遷移檔 (Migrations) 進行大整併。
在執行破壞性的「資料庫重置與整併」之前，本階段的首要任務是**救援線上真實資料 (Live Data Rescue)**，並全面**現代化種子資料 (Seed Data Modernization)**，以確保離線啟動後的系統具備足夠的壓力測試樣本。

---

## 1. 活體資料救援 (Live Data Rescue)
在重建資料庫前，我們實作了 `99_rescue_live_data.sql` 來安全備份並轉移生產環境中具備商業價值的真實設定與資料。

* **商業線索 (Business Leads) 提取**：成功從 Live DB 救援 88 筆真實世界的商業線索，避免因重置而丟失業務進度。
* **AI 提示詞與設定保留**：保留了使用者自定義的 MapReduce 與 TTS (文字轉語音) AI Agent 提示詞。
* **爬蟲與 RAG 來源**：儲存了使用者配置的爬蟲目標 (例如 `fate.windada.com`) 與 RAG 知識庫來源設定。
* **型別安全與垃圾過濾**：
  - 修正了在匯出/匯入過程中的 Array 欄位型別轉換問題 (Type Casting)。
  - 依照使用者指示，主動過濾掉包含測試 UUID 的營運表單 (如 Tasks, Logs)，確保新資料庫的純淨度。

---

## 2. 種子資料現代化與壓力測試 (Seed Data Modernization)
為了配合 Phase 5.5.0 導入的本地視覺評判官 (Gemma 4:e4b) 與離線 RAG，種子資料必須升級以提供足夠的測試深度。

* **視覺公證壓力測試 (Visual Judge Stress Test)**：
  - 新增了第 8 篇極度複雜的部落格文章，內含 Markdown 表格、程式碼區塊 (Code Blocks) 與數學公式 (Math blocks)。
  - 目的：用於在 `make twin-simulator` 時，極限測試離線多模態模型判斷複雜排版是否跑版的能力。
* **資料擬真度提升**：
  - 將陳舊的假資料公司名稱 (如 'Stale Corp') 現代化為 'Apex Logistics Solutions' 與 'Nexus Financial Group'。
  - 新增高階主管任務：`Marketing Data Deep Dive - Q4 Campaign ROI`。
* **權限修復 (RBAC Recovery)**：恢復了在先前的 Patch 中意外遺失的 Manager 權限（包含 `agent:trigger:dev`, `code:approve` 等），確保身分隔離測試的正確性。
* **模型設定清理**：移除了已棄用的 `gemini-3.1-flash-lite-preview` 相關後綴，統一對齊正式版設定。

---

## 3. 資料庫遷移檔大整併 (Migration Consolidation)
*此部分對應目前 `git status` 中正在進行的未提交變更。*

* **基底表單吸收 (Base Table Absorption)**：將散落的修補程式（Patch 13 至 Patch 23，包含效能索引、租戶硬化、任務重排序等）直接整併回核心的基底 SQL 檔案（`02_tables_core.sql` 到 `10_security_rls.sql`）。
* **清理冗餘檔案**：刪除 `13_optimize_task_reordering.sql` 到 `23_multi_tenant_and_rls_hardening.sql` 等多餘的遷移檔，大幅降低本地 PostgreSQL 初始化時的 I/O 負擔。
* **降維相容 (Dimensionality Downscaling)**：配合離線版 `embeddinggemma` 模型，清除了原有的高維度向量資料，準備將 `embedding` 欄位全面降階為 384 維度，並主動 `DROP` 與 `CREATE` `hnsw` 索引確保相容性。
* **Schema 瘦身與技術債清理 (Schema Pruning)**：
  - 透過自製的清理腳本 (`patch_cleanup.py`)，從 `06_constraints_main.sql`、`09_constraints_fkeys.sql` 與 `10_security_rls.sql` 中徹底拔除了已廢棄表單（`customers`, `market_insights`, `subscriptions`）的關聯約束 (Constraints)、外鍵 (Foreign Keys) 與 RLS 安全策略。
  - 此舉徹底移除了無用表的歷史包袱，讓離線資料庫更為輕量。

---

## 4. 後端代碼品質與穩定性 (Backend Code Quality)
在配合離線化資料庫的同時，也對後端引擎進行了代碼層級的微調：
* **型別安全修正**：在 `batch_processor.py` 中處理 SentenceTransformer 向量生成時，為 `zip(texts, embeddings_np)` 補上了 `strict=False` 參數，以符合最新的 Python PEP 型別規範，消除 Linter 隱患。
* **生命週期優化**：微調了 `lifespan.py` 中的 `migration_service` 載入順序。

---

## 5. 基礎設施瘦身與測試防護 (Infrastructure Slimming & Test Hardening)
在審查過去 10 次的 Git Commit 歷史後，我們發現此階段除了資料庫重整，還包含了針對 CI/CD 基礎設施與測試環境的關鍵硬化：
* **徹底解決 Docker Image Bloat (ENOSPC 危機)**：
  - 移除了 `Dockerfile.server` 中錯誤的 `COPY --from=builder /root/.cache` 語法，防止高達 8GB 的無用快取被封裝。
  - 在下載離線 Wheel 腳本 (`cache_offline_packages.py`) 中強制加入 `--extra-index-url https://download.pytorch.org/whl/cpu`，剃除高達數 GB 的 Nvidia CUDA 驅動依賴，成功將系統映像檔從 31GB 壓制到 5GB。
* **E2E 測試交叉污染防護**：
  - 修復了前端 E2E 測試的基礎設定 (`enduser-ui-fe/tests/e2e/e2e.setup.tsx`)。
  - 實作在 `afterEach` 階段強制重置 `getCurrentUser` Mock 狀態，徹底解決了因身分狀態殘留導致的「測試交叉污染 (Cross-test pollution)」，確保每一輪 RBAC 隔離測試的準確性。
* **開發者規範同步**：將上述 ENOSPC 危機與 Docker.raw (Sparse File) 的底層坑洞，正式寫入 `CONTRIBUTING_tw.md` 與 `GEMINI.md` 的「第一章：核心工作習慣」中，避免未來團隊重蹈覆轍。

---

## 驗證指標 (Acceptance Criteria)
1. 執行完整的 DB Init 腳本後，88 筆真實 Leads 與自定義 Agent 提示詞必須完好存在於資料庫中。
2. 系統啟動時，Migration 應只需執行核心的 01~12 腳本，不再需要執行 13~23 的零碎補丁。
3. 執行 `make twin-simulator` 時，視覺評判官必須能正確解析包含數學公式與表格的第 8 篇部落格文章，不會發生解析崩潰。