# Phase 5.3.2: 行銷工作台影片播放器渲染與訊號源排序功能修復計畫

## 📋 核心願景與 5.3.2 增訂目的
本計畫繼承並解決了 Phase 5.3.1 自動化驗收中所暴露的數項關鍵系統整合與效能問題（特別是 Bob 的行銷工作台 RAG 知識庫中影片無法播放、訊號來源未照時間排序導致找不到卡片，以及 Rerank 導致 API 超時而被瀏覽器中斷等問題）。

**在 5.3.2 中，我們完成了以下核心修復，實現了雙用途行銷管道的完全閉環：**
1. **RAG 向量檢索 `source` 欄位遺失修復**：
   原先後端 RAG 執行器 (`rag_pipeline_executor.py`) 回傳的向量匹配結果中，其 `metadata` 內缺少 `source` 欄位，導致前端在載入 `SourceContextPane.tsx` 時 `ref.metadata.source` 為 `undefined`，進而無法觸發 `<video>` 播放器的渲染。我們在此版本中加入了自動回填邏輯，若 `metadata` 中沒有 `source`，則自動使用 `result.url` 作為來源。
2. **Victory Feed 訊號來源列表排序與分頁 Bug 修復**：
   在 `analytics_handler.py` 中，原先對 `leads` 的查詢是直接執行 `limit(10)` 後再於 Python 端與 tasks, blogs 進行混合排序。這導致如果資料庫有超過 10 筆 leads 時，近期新增的 lead（如我們 seeded 的 `Neogence` 德典生技）會因為無排序 limit 而被舊資料排擠，無法出現在 Bob 的 Sources 清單中。我們在此版本中將其修復為在資料庫查詢層級即使用 `order("created_at", desc=True).limit(10)`，確保 Bob 的工作台永遠顯示最新的行銷訊號。
3. **消除 CPU-only 本地環境下 Rerank 導致的 API 10秒超時中斷**：
   由於本地 Docker 架構通常為 CPU 執行環境，執行遠端 ML 重新排序（Reranking）需要 10~12 秒。然而，前端 `apiClient.ts` 對 API 連線設有 10 秒硬性超時保護。這導致 RAG 請求在後端完成前就被前端 Abort。我們在資料庫 `archon_settings` 中將 `USE_RERANKING` 設為 `false`，避開此效能瓶頸，使 RAG 查詢降低至 0.3 秒，成功避免超時。
4. **前端影片路徑過濾與正則表達式容錯**：
   修復了 `RAGCitation.tsx`、`EditorBody.tsx` 和 `SourceContextPane.tsx` 的路徑解析邏輯，使其能夠相容包含 `#chunk=0` 等 RAG 雜湊片段的影片 URL，並將 `file:///` 本地文件系統路徑動態替換為前端公共資源路徑 `/assets/videos/auto_demos/`，使 `<video>` 標籤能夠成功載入播放。

---

## 🔍 技術標準與邊界限制
1. **RAG Metadata 物理回填**：
   確保 `execute_rag_pipeline` 中，回傳的 metadata 一定包含 `source` 欄位，指向原始文件的存取路徑或 URL。
2. **資料庫層排序 (Database-level Sorting)**：
   為了避免在應用程式層進行 partial limit 導致的資料遺失，所有 Victory Feed 的資料庫查詢（Leads、Tasks、Blogs）必須先在資料庫端執行 `order("created_at", desc=True)` 排序，再進行 `limit(10)` 截斷。
3. **前端 API 超時與 Abort 防禦**：
   前端 `apiClient.ts` 保留 10 秒超時機制，在 CPU 瓶頸環境下，應透過關閉後端 reranking 策略來達成 latency 優化，而非盲目放寬前端超時限制。

---

## 🛠️ 具體實作步驟 (Actionable Plan)

### 第一步：後端 RAG 結果 Metadata 欄位補全
*   **目標檔案**: [rag_pipeline_executor.py](file:///Users/vincenta/GoogleKwok022/Archon/python/src/server/services/search/rag_pipeline_executor.py) [MODIFY]
*   **實作細節**:
    *   在組合 RAG 搜尋結果的迴圈中，檢查並回填 `source` 屬性：
        ```python
        res_metadata = result.get("metadata", {})
        if "source" not in res_metadata and result.get("url"):
            res_metadata = {**res_metadata, "source": result.get("url")}
        ```

### 第二步：後端 Combined Sources 時間戳記降序排序修復
*   **目標檔案**: [analytics_handler.py](file:///Users/vincenta/GoogleKwok022/Archon/python/src/server/services/marketing/analytics_handler.py) [MODIFY]
*   **實作細節**:
    *   在 `get_combined_sources` 內，將 `leads`, `tasks`, `blogs` 的 Supabase 查詢加上 `.order("created_at", desc=True)`。
    *   確保 Bob 的 Sources 清單能夠拉取到最新的 `Neogence` 等 Lead 資訊。

### 第三步：前端影片標籤路徑處理與正則擴展
*   **目標檔案**: 
    *   [RAGCitation.tsx](file:///Users/vincenta/GoogleKwok022/Archon/enduser-ui-fe/src/features/marketing/components/RAGCitation.tsx) [MODIFY]
    *   [EditorBody.tsx](file:///Users/vincenta/GoogleKwok022/Archon/enduser-ui-fe/src/features/marketing/components/workbench/EditorBody.tsx) [MODIFY]
    *   [SourceContextPane.tsx](file:///Users/vincenta/GoogleKwok022/Archon/enduser-ui-fe/src/features/marketing/components/workbench/SourceContextPane.tsx) [MODIFY]
*   **實作細節**:
    *   將正則匹配從 `/\.(mp4|webm)$/i` 擴展至 `/\.(mp4|webm)(#.*)?$/i`，以容錯 RAG 片段標記。
    *   將 `src` 屬性中的 `file://` 協定及內部 Docker 掛載路徑轉換為前端能對外存取的公共資源路徑，並移除雜湊 fragment。
        ```typescript
        src={url.replace(/^file:\/\/.*\/(public|frontend_public)\//, '/').split('#')[0]}
        ```

### 第四步：自動化錄製驗證場景更新
*   **目標檔案**: [check_workbench_video.yaml](file:///Users/vincenta/GoogleKwok022/Archon/scripts/twin_scenarios/check_workbench_video.yaml) [MODIFY]
*   **實作細節**:
    *   將步驟 5 點擊側邊欄第一筆卡片的模糊定位改為精準點擊 Neogence Lead 卡片：
        ```yaml
        - action: "click"
          selector: 'h4:has-text("Neogence")'
        ```
    *   更新 `system_prompt` 以告知 AI 視覺裁判，只要畫面上出現包含影片控制按鈕（如播放鍵、進度條）的播放器元件，即算作成功，不需等待影片實際播放，避免因靜態截圖被判斷為 failure。

---

## ⚠️ 前置風險評估 (Pre-Action Assessment)
1. **Docker 與宿主機環境差異**：
   在執行 `twin_scout.py` 自動化驗證時，若是在 host 端執行，應指定 `--mode action` 以跳過其他 container DNS 無法解析的 audit 巡檢階段，避免因 `enduser-ui:5173` 無法解析而卡死。
2. **服務發現與 Rerank 配置更新滯後**：
   直接在 Supabase 修改 `USE_RERANKING` 設定後，`archon-server` 的內存 cache 不會即時更新。必須重啟 `archon-server` 容器，以確保 Lifespan 重新初始化並加載最新的 settings。
