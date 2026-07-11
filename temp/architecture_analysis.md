# Archon 系統架構與數據分析報告

本報告基於專案內 `GEMINI.md`、`CONTRIBUTING_tw.md`、`README.md`、`Makefile` 及相關程式碼檔案（符合單一事實來源 SSOT）撰寫，專注於系統的環境與基礎設施配置、Prompt Manager 與 RAG 模組的實作現況，並提出具備防禦性考量的架構升級計畫。

---

## 第一部分：數據分析與現有模組功能

### 1. 數據分析 (基於 SSOT 萃取)

*   **環境變數 (Env)**:
    *   **核心配置**: 系統高度依賴 `.env`，包含 `HOST`、`PORT`、`HF_TOKEN`、`HF_EMBEDDING_MODEL` 等。
    *   **防禦性限制**: 後端會**強制檢查** `SUPABASE_SERVICE_KEY` 的 JWT Role，若誤用 `anon` (Public) Key 系統將直接崩潰 (CRITICAL)；必須使用 `service_role` (Secret) Key（出處：`CONTRIBUTING_tw.md`）。另外，對於 `HF_TOKEN`，環境曾爆發過「注音輸入法陷阱（如結尾混入 `\u3112`）」導致 `UnicodeEncodeError` 的嚴重災難，需確保變數純淨無污染。
*   **套件管理與執行緒 (uv / uvicorn)**:
    *   **uv**: 作為依賴管理的核心（取代 pip/poetry）。在十月的歷史中（`GEMINI.md`），曾發生過 `pip` vs `uv` 的架構混亂，最終確立統一使用 `uv`，如 `uv sync`、`uv run python`。
    *   **uvicorn**: 後端透過 FastAPI 驅動，在 `render.yaml` 的啟動指令中宣告為 `python -m uvicorn src.server.main:app --host 0.0.0.0 --port $PORT --workers 1`。在本地開發 (`docker-compose.yml`) 則會開啟 `--reload` 熱重載。
*   **Makefile**:
    *   被確立為專案的**單一事實來源 (SSOT)**，所有關鍵自動化流程皆透過 `make` 執行。
    *   核心指令：`make check` (基於 `check-env.js` 驗證環境)、`make db-init` (具備 `schema_migrations` 冪等性防護的初始化腳本，會自動對齊 Auth UUID 與 Public ID 解決 406 Error)、`make probe` (執行功能煙霧測試)。
*   **YAML 配置 (docker-compose & render)**:
    *   `docker-compose.yml`: 利用 `UV_NO_INDEX` 和 `UV_FIND_LINKS` 環境變數支援離線與緩存 (`/app/offline_wheels`) 構建。
    *   `render.yaml`: 定義了雲端部署規則。前端 SPA (如 `archon-ui-main`) **必須嚴格遵守**兩條路由規則順序：先設定 `/api/*` 導向後端，再設定 `/*` Fallback 至 `/index.html`。若順序錯亂或缺失，將導致 API 404 錯誤或解析異常 (`< is not valid JSON`)。

### 2. 模組功能說明

#### A. Prompt Manager (提示詞管理器)
*   **當前實作**：由 `PromptService` (`python/src/server/services/prompt_service.py`) 與 `AgentRegistry` 組成。
*   **功能架構**：提供系統內所有 Agent (如 Alice, Bob, Charlie, DevBot 等) 的角色與系統提示詞管理。採用「本地記憶體 Dict 快取 (`_prompts`) + Supabase DB (`archon_prompts` 表) 同步」的雙層架構。
*   **防禦性設計**：`get_prompt()` 中實作了嚴格的例外處理，並對 DB 回傳的 `res.data` 進行了型別驗證（避免 `MagicMock` 污染測試），若發生失敗則會退回 `default` 提示詞，確保系統不會因 DB 斷線而完全癱瘓。

#### B. RAG (檢索增強生成引擎)
*   **當前實作**：核心由 `RagService` 與 `DocumentStorageFacade` 驅動。
*   **功能架構**：文件經過智慧切塊 (`chunking_utils.py`) 後，利用 `huggingface_hub` HTTP 呼叫外部 API (`https://router.huggingface.co/...`) 進行向量化 (Embedding)，最終儲存至 Supabase Vector。支援混合搜尋 (Hybrid Search) 以及透過資料庫 RPC (`graph_reasoning_n_hop`) 進行多跳圖推理。
*   **防禦性設計**：整合了 `progress_tracker.py` 以 Server-Sent Events (SSE) 即時追蹤長時任務，避免前端因 Loading 過久引發 Race Condition。要求通過 `make probe` (Health Check) 確認 Vector Extension 運作正常才能上線。

---

## 第二部分：UML 架構與防禦性升級計畫比較

### 1. 現有架構 UML (Mermaid)

```mermaid
flowchart TD
    subgraph Frontend [前端應用 (Render SPA)]
        UI[UI Components]
    end

    subgraph Backend [後端 FastAPI (Uvicorn)]
        API[API Router]
        Agent[Agent Registry & Service]

        subgraph Services [核心服務]
            PM[PromptService <br> In-memory Cache]
            RAG[RagService <br> DocumentStorageFacade]
        end
    end

    subgraph External [外部依賴]
        HF[HuggingFace <br> API Router]
        DB[(Supabase DB <br> archon_prompts & Vectors)]
    end

    UI -- HTTP /api/* --> API
    API --> Agent
    Agent --> PM
    Agent --> RAG

    PM -- "1. Read Cache" --> PM
    PM -- "2. Sync/Fetch (RPC/Query)" --> DB

    RAG -- "HTTP POST (Timeout 10s)" --> HF
    RAG -- "Store / RPC graph_search" --> DB
```

### 2. 架構升級計畫與比較表 (防禦性視角)

此計畫**排除樂觀路徑**，專注於解決現有架構在分佈式部署、外部依賴不穩定與歷史技術債（如編碼錯誤、快取不同步）下的弱點。

| 模組 | 現狀架構設計 (Current) | 擴充與升級計畫 (Defensive Upgrade Plan) | 欲解決的問題與風險 |
| :--- | :--- | :--- | :--- |
| **Prompt Manager** | 單例模式 (Singleton) 搭載本機 `dict` (`_prompts`) 作為快取。 | **1. 快取一致性防護**：引入分散式 Pub/Sub (如 Redis) 或 Webhook 機制。當 Admin UI 修改 Prompt 寫入 DB 時，主動廣播失效事件給所有水平擴展的 Uvicorn 實例 (Workers)。<br>**2. 版本回溯機制**：在 `archon_prompts` 加入 `version_history`。 | 若未來 Render 部署超過 1 個 Worker 或多重實例，本機 `dict` 快取會導致節點間狀態不同步 (Split-brain)；缺少歷史紀錄將導致誤改無法輕易復原。 |
| **RAG (Embedding Pipeline)** | 透過 `httpx.AsyncClient` 同步呼叫 HuggingFace API，若遇到奇怪字元（如注音 `\u3112`）會引發致命的 `UnicodeEncodeError` 導致後端崩潰。 | **1. 字元純淨化中介層 (Sanitization Middleware)**：強制攔截並清洗寫入 HF API 標頭與內文的非標準 ASCII/UTF-8 異常控制字元。<br>**2. 斷路器與 Fallback 策略 (Circuit Breaker)**：若 HF API 發生 503 或超時，觸發斷路器並自動 Fallback 使用本機輕量級 ONNX 模型（若存在）。 | 根除 `GEMINI.md` 中記錄的輸入法剪貼簿陷阱；防止外部 HF 節點擁塞導致系統連鎖掛點 (Cascading Failure)。 |
| **部署路由與基礎設施** | 依賴開發者手動於 Render 儀表板設置 `/api/*` 與 `/*` 的 Rewrite 規則，常因人為疏失導致 404 或 `index.html` JSON 解析錯誤。 | **基礎架構即程式碼 (IaC) 強制綁定**：完全透過 `render.yaml` 的 `routes` 屬性來鎖死前端靜態站點的重定向規則，不再依賴手動點擊儀表板配置。 | 消除「傳播延遲」與「人為配置疏忽」，確保環境部署具備與 `make db-init` 等同的物理冪等性。 |
| **Database Sync** | 於 `init_db.py` 中執行「雙重同步 (Dual Sync)」對齊 Auth UUID 與 Public ID。 | **非同步背景自癒守護進程 (Self-healing Daemon)**：不只依賴啟動時 `make db-init` 修復，而在背景任務 (`background_task_manager.py`) 建立定期對帳巡檢機制。 | 防止運行中途前端直接向 Auth 註冊，但 Profile 尚未對齊所導致的偶發性 406 Error 復發。 |
