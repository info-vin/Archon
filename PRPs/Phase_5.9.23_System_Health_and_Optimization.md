# Phase 5.9.23: System Health, SSOT Alignment, and Resource Optimization

## 1. 核心目標 (Core Objectives)
- 根除 System Probe 與 Log Patrol 偵測到的三項技術債。
- 落實「不要硬編碼 (No Hardcoding)」與「單一事實來源 (SSOT)」原則。
- 遵循「不改 A 壞 B」的品質門禁。
- 替前端 Docker 容器進行記憶體減肥，但保留熱重載 (Hot Reload) 開發體驗。

## 2. 診斷與解法 (Diagnostics & Solutions)

### 環境影響對照表 (Local vs HF Impact)
| 問題 | Local 影響 | HF (Hugging Face) 影響 | 修正層級 |
| :--- | :--- | :--- | :--- |
| **A. `AGENTS.md` 遺失** | ❌ 爬蟲與功能異常 | ✅ 正常 (因 Dockerfile `COPY . /app`) | **Local 專屬** (僅修改 `docker-compose.yml`) |
| **B. 向量維度衝突** | ❌ 搜尋 500 崩潰 | ❌ 搜尋 500 崩潰 | **Global (SSOT)** (影響共用的 Supabase DB) |
| **C. Agentic RAG 停用** | ❌ 助理呼叫工具失敗 | ❌ 助理呼叫工具失敗 | **Global (SSOT)** (影響共用的 Supabase DB) |
| **D. 記憶體暴增** | ❌ V8 引擎吃光記憶體 | ➖ (視 HF 容器規格而定) | **Local 專屬** (僅修改 `docker-compose.yml`) |

### A. `AGENTS.md` 實體檔案掛載遺漏 (Local Environment)
- **現象**: 爬蟲服務與 JobBoard 於本地執行時報錯 `[Errno 2] No such file or directory: 'AGENTS.md'`。
- **根因**: HF 環境使用 Dockerfile `COPY . /app` 沒問題，但本機的 `docker-compose.yml` 忘記設定 Volume 掛載。
- **防禦性解法**: 於 `docker-compose.yml` 內的 `archon-server` 新增 `- ./AGENTS.md:/app/AGENTS.md` 掛載點。

### B. 向量維度衝突 (3072 vs 768) 與 SSOT 違規
- **現象**: RAG 搜尋觸發 `different vector dimensions 768 and 3072` PostgreSQL 錯誤。
- **真因**: SSOT (`archon_settings`) 已設定 `EMBEDDING_DIMENSIONS=768`，但後端 `batch_processor.py` 使用 Google Gemini (`gemini-embedding-001`) 時，因相容層與 `output_dimensionality` 未支援舊模型，導致 Google API 原生回傳 **3072 維度** 向量，並直接塞入 768 維度資料庫引發崩潰。
- **物理截斷解法**:
  1. 在 `batch_processor.py` 中，收到向量時增加實體防線 (Physical Truncation)：`emb_vals = emb_vals[:embedding_dimensions]`。
  2. 此防線確保所有外部模型回傳的維度絕對服從 SSOT 設定，達到 **100% Zero Dimension Mismatch**，且不影響向下相容性。

### C. Agentic RAG 被禁用 (HTTP 500)
- **現象**: DevBot 呼叫 `rag_search_code_examples` 遭遇 500 錯誤。
- **根因**: 系統預設關閉此功能，且缺乏對應的開關設定。
- **SSOT 解法**: 將 `USE_AGENTIC_RAG` = `true` 寫入 `archon_settings` 資料表統一由資料庫控管。

### D. 資源減肥 (Resource Diet)
- **後端**: 根據指揮官指示，**保留** `archon-server` 的 `--reload` 參數以維持開發順暢度。
- **前端 (`enduser-ui`)**: Vite 開發伺服器在 V8 引擎下記憶體容易無限膨脹。透過在 `docker-compose.yml` 中注入 `NODE_OPTIONS=--max-old-space-size=512`，強迫 Node.js 提早進行垃圾回收 (Garbage Collection)，在不影響熱重載的前提下壓制記憶體用量。

## 3. 實體公證 (Physical Audit)
> ⚠️ **避免資料清空危機**: 本階段驗證**不使用** `make test-fe` (或任何整合測試)，因為前端 E2E 測試 (`globalSetup.ts`) 會觸發 `/api/test/reset-database` 清空本機資料庫。我們將改為透過專屬 Python 腳本對運行中系統進行防禦性驗證。

- **自動化安全驗證腳本**: 建立 `scripts/verify_phase_5_9_23.py` 腳本，透過 Python 執行以下兩項「無破壞性」的檢查：
  1. 向 Supabase `match_archon_crawled_pages` 發送 768 維度的空向量，斷言回傳成功 (排除 1536 維度衝突)。
  2. 對 `/api/rag/code-examples` 發送測試請求，斷言 HTTP 狀態碼為 200 (確認 `USE_AGENTIC_RAG` 已成功由資料庫啟用)。
- **手動環境驗證**: 確保修改 `docker-compose.yml` 後，執行 `make dev-docker` 服務能正常啟動，並透過 `docker stats` 觀察前端記憶體確實受到 `--max-old-space-size=512` 的限制。
