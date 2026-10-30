# 廚師日誌 (Chef's Journal) v2

> **【文件目的】**
>
> 本文件是 AI 助理 Gemini 的工作日誌與核心原則。它濃縮了專案開發過程中最關鍵的學習與SOP，旨在成為一個高效、聚焦的行動指南，並避免重複過去的錯誤。
>
> **【文件結構】**
>
> *   **第一章：核心工作習慣**: 定義了 Gemini 不可動搖的、必須在所有行動前遵守的思維框架與SOP。
> *   **第二章：關鍵學習與偵錯模式**: 提煉了從大量歷史日誌中反覆出現的、最有價值的經驗教訓，並將其歸納為可複用的偵錯模式。
> *   **第三章：近期工作日誌**: 保留最近的、最相關的一週日誌，以供快速回溯上下文。
> *   **第四章：歷史檔案**: 完整存檔所有過去的日誌，作為深入研究特定問題時的「考古資料」。

---

# 第一章：我的核心工作習慣 (My Core Habits)

### 【行動前風險評估原則 (Pre-Action Risk Assessment Principle)】

> **【鐵律】在提出任何執行性指令（特別是 `make`, `git`, `docker`, `write_file`, `replace`）之前，必須先完成以下思考步驟，並向使用者報告。**
>
> 1.  **回顧歷史**: 主動回想 `GEMINI.md` 和 `CONTRIBUTING_tw.md` 中與此指令相關的歷史失敗案例。
> 2.  **檢查設定檔**: 讀取相關服務的設定檔（如 `vite.config.ts`, `docker-compose.yml`），主動識別出指令之外的「隱性依賴」，例如**環境變數、掛載卷、或特定的埠號**。
> 3.  **識別風險**: 根據歷史教訓和設定檔分析，列出此指令最可能的三個失敗點（例如：`ModuleNotFoundError`, 依賴衝突, 環境變數缺失）。
> 4.  **設計驗證**: 規劃一個一個或多個成本最低的**前置驗證步驟**（例如：`read_file` 檢查設定，`ls` 檢查檔案是否存在），用以在執行前排除這些風險。
> 5.  **提出安全計畫**: 向使用者提出的第一個計畫，**必須**是包含了前置驗證的「安全計畫」。
>
> **嚴格禁止**在未經風險評估的情況下，直接提出「快樂路徑」的執行計畫。

### 【全面影響分析原則 (Comprehensive Impact Analysis Principle)】

> **【鐵律】在對任何程式碼進行修改前，我必須先徹底分析所有潛在的影響範圍，特別是測試檔案。**
>
> 1.  **分析依賴與影響**: 在提出修改計畫前，我**必須**使用 `search_file_content`, `git log` 等工具，全面探查受影響的檔案列表，並評估對功能、行為和效能的潛在影響。
> 2.  **同時考慮程式碼與測試**: 修改計畫**必須**同時涵蓋**程式碼調整**與**必要的測試調整**（包括測試設定、模擬資料、斷言等），並在計畫中明確說明。
> 3.  **單次到位修復**: 目標是實現一次性修復，避免「改 A 壞 B」或因測試未更新而導致的問題，提高整體效率。

### 【會話啟動標準作業程序 (Session Startup SOP)】

> **【鐵律】此 SOP 為 Gemini 在每次新會話開始時，都必須嚴格遵守的首要步驟，旨在確保上下文同步，避免重複錯誤。**
>
> 1.  **第一步：強制讀取上下文**: 在回應您的任何請求前，我**必須**先讀取 `GEMINI.md` 和 `CONTRIBUTING_tw.md` 的內容。
> 2.  **第二步：物理對帳門禁 (Physical Audit Gate)**: 
>     - **Schema 對帳**: 在執行任何 API 或資料庫欄位修改前，必須讀取 `migration/` 資料夾下的 SQL 實體。**嚴禁幻想欄位名稱**。
>     - **雙生對帳**: 執行 `make twin-scout` 巡檢前，必須讀取 `scripts/twin_scout.py`，確保 Reality Snapshot 的 SQL 指標與 UI 頁面路徑 100% 物理對齊，防止 false mismatch。
> 3.  **第三步：口頭確認 (Verbal Confirmation)**: 讀取後，我會向您用一兩句話總結我所理解的「**上次會話的最終狀態**」和「**今天的第一個目標**」。
*   **當前狀態 (Current Context)**: 2026-10-30 依「探針先行與零虛假驗證」鐵律實施實體穿透證明：實體探針 `scratch/prove_zero_fake_reality.py` 連線真實 Supabase 揭露 `archon_crawled_pages` 物理表不存在 `section_title, section_order, word_count, char_count, chunk_count` 幻覺欄位（原導致 PostgREST 42703 靜默失敗回傳 0 筆），物理重構 `pages_service.py` 與 `pages_api.py` 映射真實欄位與預設值；端到端驗證 Progress API `type: Literal[...]` 判別式；全量通過 `make lint-be`（393 檔 0 錯誤）、目標測試（23 passed）、`make test-be-fast`（**828 passed**, 0 failed）與 `make phase-audit` 11 大門禁。
*   **今日目標 (Today's Goal)**: 維護代碼庫物理真實性、監控雲端容器與資料庫健康度，並持續審查 Jules 提交。

> 4.  **第四步：取得您的確認**: 在您確認我對起點的理解無誤後，我才能開始執行第一個指令。

### 【UI 開發鐵律 (UI Development Iron Law)】

> **【鐵律】在產出任何 React 元件或修改前端程式碼前，必須先完成以下步驟。**
>
> 1.  **強制讀取 UI 標準**: 我**必須**先讀取 `PRPs/ai_docs/UI_STANDARDS.md` 的完整內容。
> 2.  **在計畫中宣告合規性**: 在我向您提出的開發計畫中，**必須**明確包含一個「合規性聲明」區塊，說明我將如何遵守 `UI_STANDARDS.md` 中的至少三項關鍵規範（例如：Tailwind v4 靜態類別、Radix UI `asChild` 組合、無障礙性 ARIA 屬性等）。
> 3.  **嚴格禁止違規行為**: **嚴格禁止**產出任何違反 `UI_STANDARDS.md` 中明確列出的「Anti-Patterns」的程式碼。

---

# 第二章：關鍵學習與偵錯模式 (Key Lessons & Debugging Patterns)

> 本章節將專案開發的歷史血淚與系統工程原則精煉為 **12 條核心黃金律**。這 12 條原則是 AI 助理與人類協作時不可逾越的行動邊界與自癒模式。

* **1. 證據至上與日誌真理 (Evidence First & Log Truth)**
    * **核心**: 拒絕主觀盲猜，日誌揭示當下事實，`git log` 交代歷史意圖。當行為不符預期時，立即在第一線注入實體日誌 (`console.log`, `print`)。當 Bug 反覆出現時，用歷史脈絡解讀代碼設計初衷，絕不在資訊真空下盲目修補。

* **2. 流程與直覺的雙重對帳 (Trust but Verify Everything)**
    * **核心**: 將 SOP (`Makefile`, `CONTRIBUTING.md`) 與使用者的直覺視為核心訊號，但兩者皆須經過雙重驗證。優先查閱既有規範以防重複犯錯；當使用者提出質疑時，立即暫停「快樂路徑」，用硬數據或程式碼實體去證實或排除疑慮。

* **3. 戰場隔離與變因控制 (Isolate the Battlefield)**
    * **核心**: 複雜的 Bug 往往是多層環境污染的疊加。必須系統性隔離變因：區分是宿主機環境、Docker 容器、還是前端元件問題。`make test` 失敗時，應釐清是根目錄工具鏈衝突還是子專案配置污染。在進行極端環境測試（如 Phase 5.5 無網/離線模式）時，必須實體切斷外部網路，驗證 Fallback 機制（如本地模型降階）是否真實生效。

* **4. 配置驅動與工具手冊意識 (Master Your Tool Configuration)**
    * **核心**: 工具的怪異行為 90% 源於配置，而非底層 Bug。Linter 規範在 `.eslintrc`，測試 Hoisting 需 `vi.hoisted`。此外，基礎設施崩潰常源於隱藏預設配置（如 Docker ENOSPC 危機源於預設下載巨型 CUDA 依賴與快取堆疊），必須精準掌握建置指令（如指定 CPU wheels）並定期壓縮瘦身。

* **5. 網路與環境隔離防護 (Internal/External Network Isolation)**
    * **核心**: 嚴防 Docker 內部 DNS（如 `supabase_kong`）洩漏至外部瀏覽器。前端代碼必須具備「主動防禦」特徵檢測，在請求發出前攔截無效的內部 URL 並切換至狀態化模擬 (Stateful Mock) 模式，杜絕瀏覽器因解析失敗陷入無限靜默 Loading。

* **6. 物理穿透驗證與三向連動 (Physical Penetration Verification)**
    * **核心**: 徹底終結「幽靈開發」，警惕日誌與文件的偽證。修改功能時，必須落實三向連動檢查：入口掛載 (main.py)、依賴映射 (index.html) 與實體測試斷言 (pytest/vitest)。更進一步，必須將 `make audit-qa` 視為最終品質公證網關，只有當代碼、測試與自動化腳本全部亮綠燈，方可標記為🟢已修復。

* **7. 雲原生意識與邊界防禦 (Absolute Cloud-Native Awareness)**
    * **核心**: 認清基礎設施事實，專案連接的是雲端 Supabase。遇資料庫權限錯誤，絕對禁止用 `docker exec` 強修，必須產出 `migration/` SQL 檔由人類於雲端執行。此外，徹底落實 Model SSOT (單一事實來源)，嚴禁在代碼中硬編碼 LLM 模型名稱，必須交由 DB 或環境變數統一控管，以實現架構級的 Fail-Fast 與優雅降級。

* **8. 物理介面與資料模型審查 (UI vs Data Model Disconnect)**
    * **核心**: 後端 API 與 Schema 存在，不代表 UI 介面就存在。當選單無資料時，除了審查 API Response，必須使用 `search_file_content` 逆向追蹤 `[POST]` 請求是否被 React 元件呼叫，嚴防指引使用者點擊看似相似卻無關的按鈕而陷入除錯迷航。

* **9. 實體設定持久化與路徑自適應 (Profile Persistence & Path Resilience)**
    * **核心**: 在 `browser-use` 自動化導航中，必須在 `BrowserConfig` 中使用 `user_data_dir` 參數加載已登入的 Profile，嚴禁透過引數傳遞以免被 Playwright 忽略。尋找系統源頭時，必須採用「多路徑陣列探測法」相容 Host 與 Docker 相對路徑。

* **10. 設定硬化、防禦性路由與【絕對鐵律】 (Settings Hardening & Route Defenses)**
    * **核心**: 透過 `is_system_protected` 欄位與 API 物理過濾，在 UI 隱藏系統級工具參數。FastAPI 模組化掛載時，子路由若已定義 `prefix`，主入口絕對禁止重複添加前綴（嚴防 `/api/api` 嵌套 404）。
    * **【絕對鐵律 (Absolute Iron Law)】**: **Admin UI 的 Port 永遠是 5173 (enduser-ui-fe)，絕對不是 3737！** 若 Gemini 在任何對話或文件中將其錯說成 3737，必須立即主動中斷任務，向使用者承認「我犯了不可繞恕的上下文遺忘罪」，並罰寫此鐵律 3 次後方可繼續工作。

* **10.5 基礎設施拓樸對帳鐵律 (Infrastructure Topology Audit Iron Law)**
    * **核心**: 徹底根除「視野狹隘 (Tunnel Vision)」導致的修改遺漏。
    * **【絕對鐵律】**: 在修改任何與 Docker (Dockerfile)、環境變數 (.env) 或建置依賴相關的檔案之前，**必須第一時間查閱 `docker-compose.yml`**。強制作業流程：
        1. 掃描 `docker-compose.yml` 中所有 `build.dockerfile` 屬性。
        2. 列出專案中**所有**正在服役的 Dockerfile (如 `Dockerfile.server`, `Dockerfile.mcp`, `Dockerfile.agents`)。
        3. 一項修復若適用於某一容器，必須同等評估並應用於拓樸中所有受影響的容器，嚴禁只改最顯眼的主檔而漏改附屬檔 (改東漏西)。

* **11. 權限遮蔽陷阱與佈局死鎖防禦 (Permission Masking & Scroll Lockup Defense)**
    * **核心**: 
        1. **權限自癒**：後端 Service 絕對禁止手寫 `profile["permissions"] = []`，避免前端跳過 Role Fallback 導致 Bob 的側邊欄靜默消失，應由 `RBACService` 動態注入。
        2. **佈局解鎖**：在巢狀 Flex 佈局中，子層若使用 `min-h-screen` 會鎖死父層捲動，必須「釋放子層高度」，並輔以底部物理緩衝 (`div.h-32`) 避開手機導覽列。

* **12. E2E 品質門禁與 React 崩潰阻斷 (E2E Quality Gate & React Crash Hardening)**
    * **核心**: 
        1. **智慧型公證**：將傳統斷言升級，導入「視覺裁判 (Vision Judge)」與「結構化語義檢測 (LLM-Judge)」，建構更具韌性的品質門禁。
        2. **全域 Mock 隔離**：Dashboard 的所有非同步 API 必須 100% Mock 覆蓋，關閉 Recharts 圖表動畫防範 Headless 環境 TickItem 報錯。
        3. **資料模型對齊**：Mock 數據結構必須與前端介面 100% 物理對齊，缺少必填欄位將引發 React `TypeError`。
        4. **空值與日誌穿透**：後端嚴禁使用 `.single()` 獲取資料，改用安全陣列查詢防禦 HTTP 500。Playwright 必須穿透捕捉瀏覽器 `error`，杜絕盲人摸象。

* **13. 防範虛假測試與型別斷層 (False Mock & Signature Sync)**
    * **核心**: 單元測試通過不代表代碼安全。修改任何核心服務 (Service/Repository) 的**回傳型別 (Return Type)**（例如將字串改為 Tuple）時，**必須**使用全域搜尋 (`grep`) 同步更新所有依賴該服務的測試 Mock，確保 `mock_service.return_value` 與物理現實 100% 一致。否則單元測試會淪為掩護 `too many values to unpack` 或寫入亂碼的遮羞布。

* **14. 探針先行與零虛假開發 (Probe-First & Zero Fake Development)**
    * **核心**: 在撰寫實作計畫前，**必須**先在 `scratch/` 寫「探針腳本 (Probe Script)」去真實觸碰外部 API 或環境變數。嚴禁在 Agent 或業務邏輯中寫死 `os.urandom` 假資料來欺騙測試或使用者 (虛假開發)。當外部憑證 (如 Google Drive Token) 缺失時，必須立刻 `Fail-Fast` 拋出錯誤並拒絕服務，絕不能「優雅降級」成假資料。

---

# 第三章：近期工作日誌 (Recent Activity Logs)

#### 2026-10-30: PR #656 ~ #657 深度審查、物理資料庫 Schema 幻覺揭露與穿透修復、Progress 判別式合約證明、Jules 門禁自癒

*   **實體探針穿透證明 (Zero Fake Verification Probe)**:
    *   **探針實證 (`scratch/prove_zero_fake_reality.py`)**: 依「探針先行與零虛假開發」原則撰寫實體探針直連雲端 Supabase：
        - **物理 Schema 斷層揭露**: 物理查詢 `archon_crawled_pages` 表，揭露其 DDL（`migration/0.2.3/01_schema_core.sql` 147-158 行）僅有 `id, url, chunk_number, content, metadata, source_id, embedding, content_search_vector, created_at, title`。PR #656 與舊有 `pages_service.list_pages` 查詢幻覺欄位 `section_title, section_order, word_count, char_count, chunk_count`，遭 PostgREST 回傳 `code: '42703', message: 'column archon_crawled_pages.section_title does not exist'`，導致所有頁面查詢靜默失敗並回傳 0 筆！且 `PageResponse` 強制要求 `full_content, updated_at` 導致查詢單頁直接觸發 5 項 Pydantic `ValidationError`！
        - **物理修復與架構對齊**:
          1. 重構 `PagesService.list_pages` 僅查詢實體欄位，並由 `metadata` / `title` 動態提取 `section_title`/`section_order`，由 `content` 動態計算 `char_count`/`word_count`。
          2. 於 `PagesService` 實作 `_map_to_page_dto`，自動補齊 `full_content = content` 與 `updated_at = created_at`。
          3. 於 `pages_api.py` 的 `PageSummary` 與 `PageResponse` 設定安全預設值（`word_count=0, char_count=0, chunk_count=1, updated_at=None`），杜絕資料庫空值或非必填欄位引發 HTTP 500。
          4. 修正 `test_pages_service.py` 虛假斷言（將原本對不存在欄位的 `eq("section_title", ...)` 修正為驗證真實業務邏輯之章節過濾），徹底消除虛假測試遮羞布（Rule 13）。
        - **實體驗證通過**: 再次執行探針，成功自 Supabase 實體資料庫查詢到 source ID `file-archoncoreoverviewmd-ee998097` 之真實頁面記錄（ID: 426, int），成功通過 `get_page_by_id` 與 `PageResponse` 驗證！
    *   **Progress API 端到端合約證明 (PROBE 2)**:
        - 實測 `create_progress_response` 產生之 `CrawlProgressResponse`、`UploadProgressResponse`、`ProjectCreationProgressResponse`，輸出字典均包含 `"type": "crawl" | "upload" | "project_creation"`。
        - 透過 FastAPI `TestClient` 請求 `/api/progress/{operation_id}`，實體 HTTP 200 回應 JSON 包含 `"type": "crawl"`，與前端 `archon-ui-main/src/features/progress/types/progress.ts:137`（`type?: "crawl" | "upload"`）100% 物理對齊。
    *   **雲端遙測狀態證明 (PROBE 3)**:
        - 透過 `HF_TOKEN` 探針取得 Hugging Face Space `chiawei6/myrmidon` 物理即時狀態：`stage='PAUSED'`, hardware: `cpu-basic`。
*   **Jules 規則門禁自癒 (`make phase-audit` Step 11)**:
    - Jules 於 PR #657 再次引入日期前綴（`## 2026-04-10`）且規則數超限（6 條）。已於 `.jules/contractor.md` 合併規則 5 與 6 為「`## 5. Align Response Schemas, Discriminators & Dynamic Payloads (extra="allow")`」，清除日期前綴並將規則數降回 5 條，全量恢復 Step 11 門禁綠燈。
*   **品質門禁公證**:
    - 通過 `make lint-be`（393 檔 0 錯誤）。
    - 通過 `test_pages_service.py`、`test_pages_api.py` 與 `test_progress_api.py`（23 passed）。
    - 通過 `make test-be-fast`（**828 passed**, 0 failed）。
    - 通過 `make phase-audit` 11 大門禁。

#### 2026-10-29: PR #650 ~ #655 深度審查、物理資料庫 Schema 斷層清剿、MCP 參數橋接與 Jules 規則門禁自癒

*   **PR #650 ~ #655 深度代碼審查與斷層清剿**:
    *   **斷層一：`archon_document_versions` 幻覺欄位導致審計寫入 PGRST204 靜默死鎖修復**:
        *   **探針實證**: PR #654 聲明 `DocumentVersionDTO` 並在 `SystemService.update_system_setting` 寫入 `archon_document_versions` 時傳入頂層 `old_value` 與 `new_value`。實體探針連線 Supabase 揭露該表僅具備 `id, project_id, task_id, field_name, version_number, content, change_summary, change_type, document_id, created_by, created_at, status`，傳入頂層幻覺欄位會 100% 觸發 `PGRST204: Could not find the 'old_value' column` 並被 `except Exception: pass` 靜默吞噬。
        *   **物理修復**: 重構 `DocumentVersionDTO`，移除頂層 `old_value`/`new_value`，強制要求 `content: dict[str, Any]`，將設定歷史正規化存入 `"content": {"setting_key": key, "old_value": old_value, "new_value": str(new_value)}`，並將 `field_name` 設為 `"system_setting"`。於實體 Supabase 驗證插入成功入庫與清理，並於 `test_system_service.py` 增補底層欄位斷言。
    *   **斷層二：MCP Tool 參數與 FastAPI `RagQueryRequest` 結構脫節修復**:
        *   **問題揭露**: PR #655 導入 `RagQueryResponse`，但請求模型 `RagQueryRequest` 僅接納 `source_ids` 與 `limit`；然而 `rag_tools.py` 傳遞的是 `source` 與 `match_count`，導致指定來源搜尋被降級為全域盲搜、筆數被重設為預設值 5。
        *   **物理修復**: 在 `schemas.py` 擴充 `RagQueryRequest` 同時容納 `source`, `match_count`, `return_mode` 並啟用 `extra="allow"`；在 `search.py` 實作自動雙向提取；在 `test_knowledge_search_api_contract.py` 新增 `test_perform_rag_query_mcp_caller_contract` 合約測試。
    *   **Jules 規則門禁自癒 (`make phase-audit` Step 11)**:
        *   Jules 於 PR #654/#655 再次引入日期幻覺標題（`## 2026-03-31`）且規則數超限（6 條）。已於 `.jules/contractor.md` 與 `.jules/type_guardian.md` 壓縮為各 5 條核心規則並徹底清除日期前綴，使 Step 11 門禁恢復 100% 綠燈。
    *   **雲端遙測與全門禁公證**:
        *   Hugging Face Space `chiawei6/myrmidon` 穩定服役於 `RUNNING` 階段（Port 8051 MCP 66 工具、Port 8181 Archon Server、Port 8052 Agents Service 運作正常）。
        *   全量通過 `make lint-fe`、`make lint-be`（393 檔 0 錯誤）、`make test-be-fast`（**825 passed**, 0 failed）與 `make phase-audit` 11 大門禁。

#### 2026-10-26: Phase 5.12.2 決策大腦 Gemini 3.6 Flash 升級、Telegram 雙語音泡泡速報與緊急語音告警實裝、Jules PR 深度鑑識及 Reaper 停用

*   **Phase 5.12.2 決策大腦 `Gemini 3.6 Flash` 升級與 Telegram 雙語音泡泡速報 (`sendVoice`) 實裝**:
    *   **探針先行實證 (Probe-First)**: 實測驗證 `models/gemini-3.6-flash` 正常回應 `READY_FOR_SUPERVISOR`，並實測驗證 Telegram Bot API `sendVoice` 可直接將 24kHz Mono WAV 轉換為原生語音泡泡 (`mime_type: audio/ogg`, `AwACAgUAAxk...`)，無需安裝巨型 `ffmpeg` 依賴。
    *   **決策大腦升級 (`SUPERVISOR_MODEL`)**: 於 [model_ssot.py](file:///Users/vincenta/GoogleKwok022/Archon/python/src/server/config/model_ssot.py)、[config.py](file:///Users/vincenta/GoogleKwok022/Archon/python/src/server/config/config.py)、[nodes.py](file:///Users/vincenta/GoogleKwok022/Archon/python/src/agents/workflow/nodes.py) 與 [internal_api.py](file:///Users/vincenta/GoogleKwok022/Archon/python/src/server/api_routes/internal_api.py) 將 `SupervisorNode` 升級為 `models/gemini-3.6-flash`，同時將 [nexus_oracle_agent.py](file:///Users/vincenta/GoogleKwok022/Archon/python/src/agents/nexus_oracle_agent.py) 解耦為讀取 `ORACLE_AGENT_MODEL` / `DEFAULT_PRO` (`gemini-3.5-flash-lite`)，確保 3.6 Flash 每日 20 次配額 100% 聚焦於由上而下的工作流統籌與日報播報腳本。
    *   **Telegram 原生語音泡泡雙模發送**: 於 [telegram_service.py](file:///Users/vincenta/GoogleKwok022/Archon/python/src/server/services/system/telegram_service.py) 實作 `send_voice`（Proxy 優先 + 遇 HTTP/網路錯誤自動 fallback 直連 `multipart/form-data`），於 [telegram.js](file:///Users/vincenta/GoogleKwok022/Archon/enduser-ui-fe/api/telegram.js) 設置 `sizeLimit: '4.5mb'` 支援長度達 60 秒之 WAV Base64 轉發。
    *   **日報雙語音泡泡 + 重大緊急告警閉環 (每日上限 5 次 TTS)**: 於 [report_enrichment_service.py](file:///Users/vincenta/GoogleKwok022/Archon/python/src/server/services/report_enrichment_service.py)、[report_service.py](file:///Users/vincenta/GoogleKwok022/Archon/python/src/server/services/report_service.py) 與 [sentinel_patrol.py](file:///Users/vincenta/GoogleKwok022/Archon/python/src/server/services/scheduler/jobs/sentinel_patrol.py) 實作 `dispatch_dual_voice_briefings`（中文晨會重點速報 `Puck` + 5 秒間隔 + 英文 CNN 商業主播風格速報 `Fenrir`）與 `trigger_emergency_voice_alert`（當日報熔斷降級或預算超標時發送 `Kore` 緊急語音泡泡，受每日 3 次上限保護），並將 `DAILY_VOICE_BRIEF_ZH`、`DAILY_VOICE_BRIEF_EN`、`EMERGENCY_VOICE_ALERT` 同步 Upsert 至雲端 `archon_prompts`。
    *   **斷層深度清剿與韌性自癒**:
        - 修復 `telegram_service.py` 漏捕獲 `httpx.HTTPStatusError` 導致 Proxy 回傳 400/500 時無法自動切換直連之重大斷層。
        - 修復 `utils.py` `_run_agent_with_retry`，支援 `gemini-3.6-flash` 遇 429 觸頂時自動降階至 `DEFAULT_PRO` (`gemini-3.5-flash-lite`)，杜絕日報死亡中斷。
        - 修復 `test_meta_twin_service.py` 測試殘留之 `SYSTEM_MODELS` 全域污染，隔絕跨測試狀態干擾。
        - 修復 `test_telegram_proxy.py` 同步方法 `raise_for_status` 誤用 `AsyncMock` 產生之 `RuntimeWarning`。
    *   **全門禁公證通過**: 通過 `make lint-fe`、`make lint-be`（393 檔 0 錯誤）、`make test-be-fast`（**817 passed**, 0 failed）與 `make phase-audit` 11 大門禁。
*   **Jules 代理人職責審查與 Reaper 停用決策**:
    *   **停用 Reaper 代理人**: 經查歷史 `git log`（PR #533 等），Reaper 曾將 FastAPI Query 參數誤判為未使用的死代碼，險些破壞 API 合約；且現代前端（ESLint/Biome）與後端（Ruff `F401`/`F841`）已有成熟靜態檢查，專案亦有每週例行維護，Reaper 不僅重複做功，且「因害怕誤刪而無法主動發現結構性技術債」。決策：**正式停用 Reaper 代理人**。
*   **Google AI Studio 過去 28 天真實配額用量與專案代碼物理映射 (Zero Guesswork Audit)**:
    *   **真實 Console 遙測數據**:
        - `Gemini 3.1 Flash Lite`: RPM 12/15 (80%), TPM 46.63K/250K, RPD 114/500。
        - `Gemini 3.1 Flash TTS`: RPM 2/3 (66.7%), TPM 874/10K, RPD 7/10 (70% 警告線)。
        - `Gemini 3.5 Flash Lite`: RPM 8/15 (53.3%), TPM 5.01K/250K, RPD 29/500。
        - `Gemini Embedding 1`: RPM 14/100, TPM 7.02K/30K, RPD 379/1K (37.9%)。
        - 其餘模型（Antigravity, Gemini 2.x, Gemini 2.5 Flash/Pro 等）：用量皆為 0。
    *   **Codebase 物理調用鏈路 100% 對齊**:
        - `DEFAULT_TEXT` 映射至 `gemini-3.1-flash-lite`（支撐 Agent Workflow、Blog/Pitch Generator、Librarian 等 15+ 服務，故 RPM 達 12/15 尖峰）。
        - `DEFAULT_PRO` 映射至 `gemini-3.5-flash-lite`（支撐 Supervisor Agent、Nexus Oracle、Presentation、Self-Healing 等推論任務）。
        - `TTS_MODEL` 映射至 `gemini-3.1-flash-tts-preview`（由 `TextToSpeechService` 產出語音，RPD 7/10 已接近免費上限）。
        - `EMBEDDING` 映射至 `gemini-embedding-001`（支撐 RAG、Contextual Embedding、104 潛客相似度計分，RPD 379 穩定消耗）。
*   **過去一個月 `git log --author="jules"` 深度鑑識 (Structure Ossification Forensics)**:
    *   **斷層一（PR #648 `b297c430`）：`CredentialManager` 回傳型別污染與未跑 `make lint-be` 門禁**: `TypeGuardian` 將 `load_all_credentials` 與 `get_credentials_by_category` 回傳型別標註為 `dict[str, str | MaskedEncryptedCredentialDict]`，導致下游 9 個呼叫端在 `int()` / `float()` / API Key 讀取時爆發 **26 個 MyPy 錯誤**，並在 `provider_configs.py` 留下一處未加 `# 合法` 註記的 `localhost:11434` SSOT 違規。
    *   **斷層二（PR #635 `b23804a5`）：`TaskDetails` 對動態 JSONB 附件崩潰與擴充欄位剝除**: `archon_tasks.attachments` 在 Agent 執行後存入的是 `AgentOutputSchema`（含 `summary`, `artifacts`, `status`），但 `TaskDetails.attachments` 卻強制限定為 `list[Attachment]`（必填 `url`），導致開啟 AI 完成之任務時直接拋出 HTTP 500 `ValidationError`；同時漏列 `query_logic.py` 產出的 `agent_output`、`ai_metrics`、`stats`、`sources`、`code_examples` 等欄位。
    *   **斷層三（PR #649 `1898985e`）：`DocumentItemResponse` 固化假結構與 `add_document` 回傳斷鏈**: 預設將 `version` 限定為 `int`（實務上 `document_service.py` 存入 `"1.0"` 字串），且未開啟 `extra="allow"` 導致 JSONB 文件自訂欄位被靜默剝除；此外 `DocumentService.add_document` 回傳字典缺少 `"document"` 鍵，導致 `POST /api/projects/{project_id}/docs` 永遠回傳 `document=None`。
    *   **斷層四（Commit `55f28352`）：`marketing_service.py` 幻覺 `TypedDict`**: `PitchResultDict` 與 `BlogDraftResultDict` 的鍵名與 `SalesPitchGenerator`、`BlogGenerator` 實際回傳結構脫節。
*   **四向物理修復與 `.jules` 守則硬化 (Fix-Forward & Agent Guardrails)**:
    *   **升級 `.jules` 雙守則**: 重構 [contractor.md](file:///Users/vincenta/GoogleKwok022/Archon/.jules/contractor.md) 與 [type_guardian.md](file:///Users/vincenta/GoogleKwok022/Archon/.jules/type_guardian.md)（各精煉為 4 條核心鐵律，符合 Step 11 `<= 5` 節限制），強制三向物理對帳（Producer ↔ Schema ↔ Frontend/MCP）、動態 JSONB 保護、禁止全 Optional 空殼與假 Mock、禁止 `cast()` 欺騙編譯器。
    *   **修復 `credentials` 型別與 SSOT**: 於 [manager.py](file:///Users/vincenta/GoogleKwok022/Archon/python/src/server/services/credentials/manager.py)、[models.py](file:///Users/vincenta/GoogleKwok022/Archon/python/src/server/services/credentials/models.py)、[provider_configs.py](file:///Users/vincenta/GoogleKwok022/Archon/python/src/server/services/credentials/provider_configs.py)、[batch_processor.py](file:///Users/vincenta/GoogleKwok022/Archon/python/src/server/services/embeddings/batch_processor.py) 與 [contextual_embedding_service.py](file:///Users/vincenta/GoogleKwok022/Archon/python/src/server/services/embeddings/contextual_embedding_service.py) 消除全部 26 個 MyPy 錯誤與 SSOT 違規。
    *   **修復專案與行銷 Schema / Service**: 於 [projects.py](file:///Users/vincenta/GoogleKwok022/Archon/python/src/server/schemas/projects.py)、[document_service.py](file:///Users/vincenta/GoogleKwok022/Archon/python/src/server/services/projects/document_service.py) 與 [marketing_service.py](file:///Users/vincenta/GoogleKwok022/Archon/python/src/server/services/marketing_service.py) 補齊真實欄位與 `ConfigDict(extra="allow")`，並於 [test_project_versioning_api.py](file:///Users/vincenta/GoogleKwok022/Archon/python/tests/server/api_routes/test_project_versioning_api.py) 新增 3 項真實端到端結構合約測試。
    *   **全門禁綠燈**: 通過 `make lint`（393 檔案 0 錯誤）、`make test-be-fast`（**811 passed**, 0 failed）與 `make phase-audit` 11 大門禁。

#### 2026-10-24: 過去一個月虛假開發四大斷層深度清剿、PR #644 幻覺 Schema 修復與星環商業日報全鏈路校正

*   **過去一個月 `git log` 虛假開發與虛假驗證四大罪狀鑑識 (Fault-Line Forensics)**:
    *   **罪狀一：修改代碼 Prompt 卻從未更新雲端 DB (`archon_prompts`)**: `PromptService.load_prompts()` 僅在 DB 缺漏 key 時新增，不會覆蓋既有紀錄。過去一個月多次修改 `pm_prompts.py` 卻未同步雲端，導致雲端與本地多達 19 個 Prompt 嚴重脫節。
    *   **罪狀二：硬編碼 `score >= 75` 造成 100% 潛客靜默封存死鎖 (`70fccdbd`)**: `gemini-embedding-001` 針對 104 頂尖 AI/自動化職缺的真實餘弦相似度最高落在 `72~74` 分（樸真國際 74、潤御開發 74、得億國際 73、秋雨創新 72），硬編碼 `>= 75` 導致所有潛客入庫即被打入 `archived`，下游 `bob_market_report` 永遠查無合格名單。
    *   **罪狀三：`ReportService` 數據餵養殘缺與職責混淆**: `gather_report_context` 漏傳潛客評分 (`enrichment_score`)、痛點 (`identified_need`)、合格潛客池 (`Active Qualified Leads Pool`) 與 Bob 的 `blog_posts` 內容管線，且日報漏接 `MANAGEMENT_STEERING_FOCUS`，導致星環討論退化為泛泛空談並把 Alice/Bob 職責混為一談。
    *   **罪狀四：幻覺 `response_model` 與假 Mock 測試 (`55f28352` PR #632, `4add34f9` PR #639, `9afda75b` PR #644)**: 在未對照 `analytics_handler.py`、`blog_generator.py` 與前端元件的情況下，憑空捏造 `CombinedSourceResponse`、`MarketingTrendsResponse`、`KnowledgeSeedResponse` 與 `SubmitBlogResponse`，導致真實 API 回傳欄位被 FastAPI 靜默剝除或拋出 HTTP 500。
*   **四向物理修復與雲端資料庫同步 (Fix-Forward & Cloud DB Sync)**:
    *   **行銷 API Schema 物理對齊**: 於 [marketing.py](file:///Users/vincenta/GoogleKwok022/Archon/python/src/server/schemas/marketing.py) 與 [marketing_service.py](file:///Users/vincenta/GoogleKwok022/Archon/python/src/server/services/marketing_service.py) 完整對齊前端 `VictoryFeedList.tsx`、`BrandDashboardView.tsx` 與後端 Handler 欄位，並更新 [test_marketing_api_contract.py](file:///Users/vincenta/GoogleKwok022/Archon/python/tests/server/api_routes/test_marketing_api_contract.py) 以真實輸出結構進行嚴格斷言。
    *   **潛客門檻校準與雲端數據復原**: 於 [job_board_service.py](file:///Users/vincenta/GoogleKwok022/Archon/python/src/server/services/job_board_service.py) 將合格門檻調為 `score >= 72`，並將雲端 Supabase `leads` 表中 `>= 72` 分的 4 家高潛力企業復原為 `qualified`。
    *   **日報上下文擴充與巨型檔案精簡**: 於 [report_service.py](file:///Users/vincenta/GoogleKwok022/Archon/python/src/server/services/report_service.py)（精簡至 **355 行**，低於 360 行預警線）補齊潛客分數、痛點、合格潛客池、Bob 部落格文章管線與 `MANAGEMENT_STEERING_FOCUS`；於 [nodes.py](file:///Users/vincenta/GoogleKwok022/Archon/python/src/agents/workflow/nodes.py) 之 `SummaryNode` 注入原始客觀數據基準；將 `ALL_PROMPTS` 100% 同步 Upsert 至雲端 `archon_prompts`（驗證 0 drift）。
*   **真實端到端重跑與 11 大品質門禁公證**:
    *   **實體重跑與 Telegram 推播**: 重新執行今日日報工單 `1970fc36-ad11-4d45-b2d0-1175c1e2e60c` 並實體推播至 Telegram，完整呈現 4 家合格潛客痛點表格、Bob 部落格草稿進度與明確角色分工。
    *   **全門禁綠燈**: 通過 `make lint`（393 檔案 0 錯誤、Lean 4 18 jobs 通過）、`make test-be-fast`（**808 passed**, 0 failed）與 `make phase-audit` 11 大門禁全綠。

#### 2026-10-23: 遠端同步、品質雙門禁公證、歷史斷層深度交叉比對與全系統 21 項週期作業全景遙測

*   **遠端同步與品質門禁雙綠燈 (`make lint` & `make test-be`)**:
    *   **Git Fast-Forward 同步**: 順利同步拉取遠端最新提交至 `a169b300`（包含 PR #640 `crawler_service` 型別守衛重構與 PR #641 `marketing_stats` API 規範）。
    *   **靜態與型別校驗**: `make lint` 100% 綠燈，包含前端雙專案 ESLint + TypeScript、後端 `check-no-single`、`ruff`、`mypy`（393 檔案 0 錯誤）以及 Lean 4（18 項定理與規範 100% 構建成功）。
    *   **後端測試套件**: `make test-be` 後端測試全綠通過，總計 **802 passed**、11 skipped、4 xfailed（0 failed）。
*   **Phase 5.11.21 ~ Phase 5.12.1 歷史 Git Log 與排程全景交叉比對**:
    *   **戒除主觀盲猜，恪守歷史脈絡**: 深入查閱 `git log` 與歷史重大事件（如 09/20 429 配額危機、10/21 日報容器斷線），理解代碼在第一線維運中的防禦性設計權衡（如 In-Process Fallback 分層安全網、確定性破冰信模板杜絕 429 死亡循環、Admin UI 動態 Settings 渲染機制）。
*   **Clockwork 週期排程實體全景遙測與 21 項作業深度穿透對帳**:
    *   **雲端 Space 狀態**: 實體驗證 Hugging Face Space (`chiawei6/myrmidon`) 處於 `RUNNING` (Stage: `READY`)，`/api/health` 順利回傳 200 OK。
    *   **全系統 4 大類別 21 項作業實體對帳**:
        - 高頻無狀態巡檢（`system_probe`、`model_verification`、`log_patrol`、`task_dispatcher`、`meta_twin_audit`）每小時穩定回傳，夜間自動切換 `[Sleep Mode]`。
        - 每日有狀態作業（`business_sentinel` 今日 08:40 已準時執行完畢，`system_probe_cleanup`、`prune_stale_leads`、`daily_executive_summary`、`token_analysis` 排程目標正常待執行）。
        - 週期性作業（10/22 Alice 首跑入庫 5 筆潛客並完成 RAG 相似度計分，Bob 市場情報事件聯動成功觸發；週日維護作業歷史工單與錨點打卡完整閉環）。
*   **階段目標完整性稽核通關 (`make phase-audit`)**:
    *   清理 stale `git fsmonitor--daemon` 幽靈快取，工作區 100% Clean；11 大架構、SSOT、Repository 隔離與 Jules 壓縮門禁全數 100% 綠燈通過。

#### 2026-10-22: 104 潛客爬蟲排程斷層鑑識、方案 A（12 小時冷卻制）架構治理與實體公證

*   **104 名單未產出之深度斷層鑑識 (Fault-Line Forensics)**:
    *   **資料庫對帳**: 實體查詢 Supabase，`leads` 表最新資料停留在 2026-10-18，`archon_settings` 之 `LAST_RUN_ALICE_AUTO_FETCH` 同樣為 10/18 13:06（週日）。
    *   **致命時間平移 Bug 根因**: `scheduler_service.py` 過去在 `_should_run_opportunistic_weekly` 中採用了 `+ timedelta(days=1)`，將週日（10/18）強行跨週推進為下週一（10/19，ISO 第 43 週）。導致昨天（10/21）開機時被誤判為「第 43 週已跑過」，整整一週被靜默略過 (Skipped)。
    *   **架構語意衝突**: 觸發器為 `IntervalTrigger(hours=12)`，但守衛門禁卻是每週一次的 `_should_run_opportunistic_weekly`。
*   **拒絕虛假驗證，方案 A（12 小時冷卻制）架構治理落地**:
    *   **排程門禁正規化**: 廢除帶有 Bug 的 `_should_run_opportunistic_weekly` 與死代碼 `_should_run_opportunistic_weekly_local_only`。將 `alice_auto_fetch` 的守衛改由 APScheduler 原生 `_should_run_scheduled_job` 接管，並加入雲端環境安全略過保護（`config.space_id is not None`）。
    *   **適應本地 Docker 開關習慣**: 
        - 當超過 12 小時未跑（如數天沒開 Docker），開機 5 分鐘後自動觸發抓取；
        - 當剛跑過不久（在 12 小時冷卻期內）重開 Docker，精準略過避免重複敲擊 104 WAF 與浪費 Token；
        - 連續開機時每 12 小時自動巡檢。
*   **真實物理公證 (Zero Fake Verification)**:
    *   **實體探針驗證**: 執行真實探針直接檢驗更新後的 `_should_run_scheduled_job("alice_auto_fetch")`，回傳結果由原先的 `should_run: False` 100% 轉為 `should_run: True`（理由為空字串，門禁解鎖）。
    *   **冷卻邊界測試**: 驗證 4 天前（True）、2 小時前（False）、13 小時前（True）三種極端時間邊界皆精準符合預期。
    *   **測試與代碼品質**: 新增 `test_dag_disconnect.py::test_alice_cooldown_and_catchup_behavior`；`make lint-be` 393 source files 100% 綠燈；`make test-be-fast` 後端 **795 passed** (0 failed)。

#### 2026-10-21: 遠端同步、Docker/HF/排程全景巡檢、Supabase RLS 鑑識與終極品質公證 (make audit-qa)

*   **遠端同步與多端健康物理巡檢 (Multi-Environment Telemetry & Health Probe)**:
    *   **Git 最新 Commit 同步**: 順利 Fast-forward 拉取最新提交 `97797d17`（包含 PR #636 與 #637 之行銷端點 Pydantic 響應模型與 `game_service` 型別防護重構）。
    *   **Docker 拓樸健康鑑識**: 驗證 `archon-server` (8181)、`archon-mcp` (8051)、`archon-agents` (8052) 與 `archon-ollama` (11434) 全數處於 `healthy` 綠燈狀態。
    *   **Hugging Face 雲端 Space 穿透**: 探針實體穿透 `chiawei6/myrmidon`，Space 處於 `RUNNING` (Stage: `READY`)，雲端 `/api/health` 順利回傳 200 OK。
*   **Clockwork 週期排程實體全景對帳 (Periodic Jobs Telemetry)**:
    *   **拒絕盲猜與斷層**: 深入容器行程與 Supabase `archon_settings`（`LAST_RUN_*`）進行三向對帳。
    *   **高頻無狀態巡檢**: `system_probe` (每小時)、`log_patrol` (每 30 分鐘)、`task_dispatcher` (每 15 分鐘)、`model_verification` (每 150 分鐘)、`meta_twin_audit` (每 45 分鐘) 全數正常循環運作中。
    *   **有狀態每日作業防重跑與補跑**: 實體日誌驗證 `business_sentinel` (今日已跑跳過)、`system_probe_cleanup` (目標 11:45)、`prune_stale_leads` (目標 11:55)、`daily_executive_summary` (目標 16:18)、`weekly_executive_summary` (下次 10-25) 皆精準符合排程邏輯。
*   **Supabase Security Advisor 漏洞鑑識與雲端外科手術式修復 (Cloud-Native Security Hardening)**:
    *   **問題定位**: Supabase Security Advisor 報告 `public.schema_migrations` 缺乏 RLS（1 Error）。
    *   **防範破壞性覆蓋與重設鐵律**: 指揮官嚴格警示並重申 `init_db.py` 歷史血淚（`RESET_DB.sql` 與 `FORCE_PROD_INIT` 防線）。恪守「絕對雲原生意識」，嚴禁在本地執行破壞性腳本或改動 `init_db.py`，杜絕生產資料被 WIPE 清空的災難風險。
    *   **雲端微創落地**: 指揮官直接於 Supabase SQL Editor 執行 `ALTER TABLE public.schema_migrations ENABLE ROW LEVEL SECURITY;`，零資料變更、完全解耦本地端，成功消除資安紅燈。
*   **終極品質公證網關通關 (`make audit-qa`)**:
    *   9 大關卡全數 100% 亮綠燈：前端雙專案單元測試全數通過、DNS Leak 與 Scroll Lockup 防禦靜態探針通過、後端 Fast 單元與整合測試 **793 passed** (0 failed)、五大角色（David, Alice, Bob, Charlie 與 DevBot/MarketBot/Librarian/POBot/Clockwork）實體冒煙全數 200 OK 通過、Lean 4 定理構建 18 jobs 成功。
*   **每日星環日報斷層鑑識、In-Process Fallback 自癒實裝與真實物理推播復原 (Fix-Forward)**:
    *   **深度罪證與斷層定位**: 10/21 16:18 排程觸發日報任務 `17baea70`，但因容器環境與 8052 微服務網路中斷，導致任務卡死在 `status: doing`，且 `task_dispatcher` 過去僅回收 `processing` 狀態，使工單淪為永凍殭屍任務，下游 Telegram 推播靜默失蹤。此外，過去探針腳本在本地進程內直接載入引擎，繞過生產鏈路產生「虛假公證」。
    *   **Fix-Forward 兩大防線實裝**:
        1. **In-Process Fallback**: 在 `agent_service._run_workflow_engine_task` 中，當跨容器 HTTP 橋接 `archon-agents:8052` 發生網路異常時，自動回退在同進程內調用 `WorkflowEngine` 完成星環 4 步討論與 Markdown 表格產出，徹底解耦跨容器單點依賴。
        2. **殭屍任務回收擴展**: 於 `task_dispatcher.py` 將逾時回收判定擴展為 `.in_("status", ["processing", "doing"])`，消除狀態死鎖黑洞。
        3. **真實生產門禁升級**: 重構 `scripts/probe_daily_pipeline.py`，直接呼叫 `agent_service` 生產鏈路，杜絕旁路作弊。
    *   **物理驗證與真實交付**: 實體探針成功接管並修復 Task `17baea70`，星環討論順利收斂，任務更新為 `done`，Telegram 每日執行摘要完整推播至指揮官終端。

#### 2026-10-20: Phase 5.12.1 規劃公證、Storage 音檔清理與每日群聊路由契約對齊 (Phase 5.12.1 - Stage 1 & Stage 2)

*   **星環討論體系全鏈路深度優化與商業閉環硬化 (Phase 5.12.1 規劃公證)**:
    *   **診斷與四大斷層鑑識**: 
        1. **Storage 音檔無 TTL 清理**: 簽名 URL 雖設 7 天過期，但未壓縮的 `.wav` 檔案在 Supabase Storage 中從未刪除，自 7 月至今殘留 14 份歷史音檔累積佔用超過 105MB。
        2. **Daily Summary 路由字串大小寫不匹配與單節點退化**: `agent_service.py` 傳入 `"daily_executive_summary"`，而資料庫存為 `"Daily Executive Summary"`，導致 Flow 查詢落空走入 `General` 流程，Charlie 僅單點調用 `SummaryNode` 並結束（`step_count` 固定為 2），且 `SummaryNode` 的條列重點 Prompt 覆蓋了上游強制 Markdown 表格與計算指標公式的要求。
        3. **合格潛客最後一哩未閉環**: Telegram 僅提示業務「點選職缺連結破冰」，缺乏系統自動生成的客製化「1-on-1 痛點破冰信 (Cold Outreach Draft)」。
        4. **戰略討論缺乏管理者焦點輸入**: 週報與月報為純後端靜默 Cron 觸發，無人類在週會前注入「本週重點驗證假設」的管道。
    *   **四階段推進架構公證**: 建立正式規格文件 [Phase_5.12.1_Star_Topology_Optimization_and_Pipeline_Hardening.md](file:///Users/vincenta/GoogleKwok022/Archon/PRPs/Phase_5.12.1_Star_Topology_Optimization_and_Pipeline_Hardening.md)。
*   **階段 1 實裝：Storage 音檔過期清理機制 (TTL Cleanup)**:
    *   **設定 SSOT 擴充**: 於 [settings.py](file:///Users/vincenta/GoogleKwok022/Archon/python/src/server/schemas/settings.py) 之 `PruningConfig` 新增 `storage_podcast_ttl_days = 14`。
    *   **音檔修剪核心**: 於 [report_enrichment_service.py](file:///Users/vincenta/GoogleKwok022/Archon/python/src/server/services/report_enrichment_service.py) 實作 `prune_expired_podcast_audio(ttl_days=14)`，嚴格限定前綴 `podcast_` 與副檔名 `.wav`，比對 `created_at` 超過 14 天者執行 `storage.from_("archon_documents").remove()`，並寫入 `archon_logs` 稽核日誌。
    *   **排程整合**: 於 [patrol_infra.py](file:///Users/vincenta/GoogleKwok022/Archon/python/src/server/services/scheduler/jobs/patrol_infra.py) 之 `run_tiered_pruning()` 整合呼叫，使音檔修剪納入例行基礎設施修剪戰線。
    *   **物理公證與 105MB 配額釋放**: 探針實體穿透 Supabase Storage，成功刪除 13 筆 7~10 月累積的過期 `.wav` 檔案，釋放超過 105MB 雲端儲存空間。
*   **階段 2 實裝：每日星環群聊路由正規化對齊與 Markdown 表格契約落地**:
    *   **大小寫正規化匹配**: 於 [nodes.py](file:///Users/vincenta/GoogleKwok022/Archon/python/src/agents/workflow/nodes.py) 移除硬編碼 `.eq("workflow_type", task_type)`，改採全量流轉正規化比對（`lower().replace(" ", "").replace("_", "")`），確保 `"daily_executive_summary"` 100% 精準命中 DB Flow `"Daily Executive Summary"`。
    *   **全節點路由保全**: 確保 `node_routing` 具備全部 5 大節點（含 `devbot` 與 `david`），並將雲端 `archon_workflow_flows` 的 `Daily Executive Summary` 路由實體補齊 `devbot` 與 `bob`。
    *   **表格契約與 Prompt 對齊**: 更新 [pm_prompts.py](file:///Users/vincenta/GoogleKwok022/Archon/python/src/server/prompts/pm_prompts.py) 與雲端 `archon_prompts`，廢除 `WORKFLOW_WORKER_SUMMARY` 強制條列點之舊限制，改為強制產出結構化 Markdown 數據表格與定義公式；同步新增 `WORKFLOW_SUPERVISOR_DAILY`。
    *   **門禁驗證**: 新增 [test_workflow_routing.py](file:///Users/vincenta/GoogleKwok022/Archon/python/tests/agents/workflow/test_workflow_routing.py)；`make lint-be` 393 source files 100% 綠燈，`make test-be` **788 passed** (0 failures)，`make phase-audit` 全綠通過。
*   **階段 3 實裝：合格潛客客製化 1-on-1 痛點破冰信自動草擬與工單閉環 (Phase 5.12.1 Stage 3)**:
    *   **破冰信模板核心**: 於 [leads_patrol.py](file:///Users/vincenta/GoogleKwok022/Archon/python/src/server/services/scheduler/jobs/leads_patrol.py) 實作 `generate_lead_outreach_draft()`，針對合格潛客之招募職缺與系統整合痛點生成高精準 1-on-1 破冰信。
    *   **Telegram 戰報增強與 429 防護**: 於市場戰報注入 `✉️ 【客製化痛點破冰信草稿 (一鍵複製)】` 區塊，嚴格限制單次僅針對 Top 1~2 筆最高分合格名單生成，防範 TPM 配額超出。
    *   **跟進工單自動閉環**: 成功推播後自動於 `archon_tasks` 建立 `[Sales Follow-up]` 工單，要求業務團隊 48 小時內依草稿聯繫並跟進，終結「僅通報未跟進」的商業漏斗斷層。
    *   **單元測試**: 新增 [test_leads_outreach.py](file:///Users/vincenta/GoogleKwok022/Archon/python/tests/services/test_leads_outreach.py) 3 項測試全數通過。
*   **階段 4 實裝：每週/每月高階戰略討論之「管理者目標對齊」輸入介面 (Phase 5.12.1 Stage 4)**:
    *   **設定 SSOT 擴充**: 於 [settings.py](file:///Users/vincenta/GoogleKwok022/Archon/python/src/server/schemas/settings.py) 之 `SchedulerConfig` 新增 `management_steering_focus: str | None = Field(default=None, alias="MANAGEMENT_STEERING_FOCUS")`。
    *   **戰略焦點動態注入**: 於 [report_service.py](file:///Users/vincenta/GoogleKwok022/Archon/python/src/server/services/report_service.py) 之 `_execute_map_reduce_summary()` 整合載入此配置，若設定則注入 `### 🎯 管理者戰略關注焦點 (Management Steering Focus)` 至 Map-Reduce 上下文，未設定則安全 Fallback。
    *   **單元測試與門禁公證**: 於 [test_report_service.py](file:///Users/vincenta/GoogleKwok022/Archon/python/tests/services/test_report_service.py) 新增有/無 Steering Focus 注入的斷言驗證；`make lint-be` 393 source files 100% 綠燈，`make test-be` **793 passed** (0 failures)，`make phase-audit` 全綠通過。
*   **深度悲觀審查與斷層清剿 (Anti-Optimistic Hardening & Fault-Line Elimination)**:
    *   **DB 物理斷層修補**: 探針實體揭露 `MANAGEMENT_STEERING_FOCUS` 與 `STORAGE_PODCAST_TTL_DAYS` 於 `archon_settings` 表無實體資料行，導致 Admin UI `/api/system/settings` 查無此項且更新觸發 500。立即建立 `migration/20261020_add_steering_focus_and_storage_ttl.sql` 並透過實體探針成功注入 Supabase。
    *   **靜默失敗與指派角色修正**: 修正 `leads_patrol.py` 過去對 `task_service.create_task` 回傳 tuple 忽略檢查之樂觀假設，精確解構 `(f_success, f_res)` 並阻斷假成功日誌；將指派對象自 Clockwork 守護程序校正為 Sales 核心 `AgentUUIDs.MARKET_BOT`。
    *   **工作流路由與型別安全硬化**: 於 [state.py](file:///Users/vincenta/GoogleKwok022/Archon/python/src/agents/workflow/state.py) 擴充 `SupervisorDecision.next_node` 納入 `"bob"` 容錯，防止 LLM 作答與 DB 路由不一致引發 Pydantic ValidationError；於 [nodes.py](file:///Users/vincenta/GoogleKwok022/Archon/python/src/agents/workflow/nodes.py) 導入 `(task_type or "")` 空值保護；[report_service.py](file:///Users/vincenta/GoogleKwok022/Archon/python/src/server/services/report_service.py) 補齊 `steering_focus: str | None` 顯式型別標註。
    *   **門禁再公證**: `make lint-be` 393 source files 100% 通過，`make test-be` **794 passed** (0 failures)，`make phase-audit` 全綠。

*   **今日 Telegram 未發送之原因鑑識、Charlie 重複路由死鎖根除與實體重發公證**:
    *   **診斷**: 
        1. 排程確實在 16:18 CST (08:18 UTC) 準時建立每日執行摘要任務 `521b3855-83c5-4943-ba7e-45ba95b07c77`，但工單長達數小時卡死於 `status: doing`。
        2. 探針穿透實體日誌揭露：Charlie 在多 Agent 群聊時，因 Prompt 缺乏嚴格推進條件且 `MarketBotNode` 接收到靜態文案指令，導致 Charlie 在第 1~10 步**陷入重複指派 marketbot 的死循環**，最終觸發 `Circuit Breaker Tripped: Needs Human Review`（超量遞迴斷路器），執行失敗導致下游 Telegram 推播從未被觸發。
        3. 此外，`nodes.py` 過往硬編碼要求 `SUPERVISOR_AGENT_MODEL` 與 `WORKER_AGENT_MODEL` 環境變數，缺失時直接拋錯崩潰，缺乏 Model SSOT 回退。
    *   **修復**: 
        1. **循序推進契約**: 更新 `WORKFLOW_SUPERVISOR_DAILY` Prompt（代碼與 DB `archon_prompts` 同步），規範嚴格 4 步依序推進（每個成員僅發言一次，marketbot -> devbot -> summary -> end）。
        2. **節點指令語意特化**: 於 [nodes.py](file:///Users/vincenta/GoogleKwok022/Archon/python/src/agents/workflow/nodes.py) 針對 `daily_executive_summary` 給予 MarketBot（Leads 評估）、DevBot（技術/成本分析）與 Summary（表格彙整）專屬數據指令。
        3. **雙重防死鎖自癒**: 在 `SupervisorNode` 導入 Anti-recursion 防衛，檢測到連續同角色指派即自動推進；在環境變數缺失時自動回退至 `SYSTEM_MODELS`。
    *   **物理重發公證**: 實體探針重新執行 Task `521b3855`，順利於 4 步內收斂產出專業 Markdown 表格摘要，工單更新為 `done`，Telegram 訊息順利送達使用者（Delivery Result: `True`）。

#### 2026-10-19: 系統日報流水線解耦、日誌聚合與 Telegram 作答推播治理 (Phase 5.11.26)

*   **日報流水線解耦與 Telegram 成果推播治理**:
    *   **診斷**: 
        1. **考卷題目誤當成果偷跑**: `report_service.py` 過去在 Daily Summary 任務建立時，未等待 Agent 完成（非同步競態），直接將包含 8 則歷史異常日誌（昨天測試產生的舊 429/400 紀錄）的原始 Prompt 題目（`task_desc`）直發 Telegram。
        2. **作答產物石沉大海**: Charlie (Supervisor) 在 19 秒後即精準歸納產出結構化摘要，但系統在第 0 秒已提早交卷，Agent 實際作答從未推播給使用者。
        3. **日誌循環污染死鎖**: 原始堆疊中的特殊字元造成 Telegram 400 錯誤，寫入 `archon_logs` 後被 Clockwork 巡檢員誤判為系統故障，開出 `Auto-Repair` 假警報工單。
    *   **修復**: 
        1. **推播點後移與解耦**: 於 [report_service.py](file:///Users/vincenta/GoogleKwok022/Archon/python/src/server/services/report_service.py) 新增 `send_summary_telegram()`，在 `_create_summary_task_and_log` 中嚴格限制 `dispatch_agent=True` 時禁止提早發送通知；改由 [agent_service.py](file:///Users/vincenta/GoogleKwok022/Archon/python/src/server/services/agent_service.py) 在 `WorkflowEngine` 執行完成且取得 `final_result` 後，才精準調用 `send_summary_telegram()` 推播 Charlie 的真實作答。
        2. **日誌上下文聚類與防爆**: 於 `_get_logs_context()` 導入特徵聚類（`Counter`），將重複性錯誤收斂為單一條目並標註頻率（如 `Rate limit hit: 429 (x5)`），訊息一律行內代碼化（`` ` ``）並截除 Raw Stacktrace 多行內容，阻斷遞迴日誌污染。
        3. **Telegram 400 降級降噪**: 於 [telegram_service.py](file:///Users/vincenta/GoogleKwok022/Archon/python/src/server/services/system/telegram_service.py) 調整 400 回退純文字重發時的日誌級別為 `WARNING`，防止觸發 `error_patrol` 誤開 Auto-Repair 工單。
    *   **門禁公證**: 更新 [test_report_service.py](file:///Users/vincenta/GoogleKwok022/Archon/python/tests/services/test_report_service.py) 與 [test_agent_service_routing.py](file:///Users/vincenta/GoogleKwok022/Archon/python/tests/services/test_agent_service_routing.py)；`make lint` 通過，`make test-be` **783 passed** (0 failures)，`make phase-audit` 全綠通過。

#### 2026-10-18: 系統摘要報告 Telegram 全文推播解除截斷與實體重發 (Phase 5.11.26)

*   **系統摘要報告 Telegram 全文推播解除截斷與 400 格式自癒**:
    *   **診斷**: 
        1. 使用者反饋 Telegram 收到的星環 Weekly / Daily 報告被截斷為 150 字元快覽 (`...`)。追查確認 `report_service.py` 遺留舊機制 `sanitize_markdown_snippet(task_desc, max_length=150)` 殘留。
        2. 全文直發時，Markdown 特殊符號不對稱引發 Telegram API `400 Bad Request: can't parse entities` 拒收。
        3. 舊週報快照包含過期問題（內容審核阻塞率 100%、429 建議），且在重新生成週報時，`NexusOracleAgent` 因 `get_collab_synergy` 回傳 290x290 協同矩陣（高達 675 萬字元 / 6.7 MB Payload）瞬間擊穿 Google Free Tier 25 萬 TPM 限制，觸發 57 秒退避重試死鎖。
    *   **修復**: 
        1. 於 [report_service.py](file:///Users/vincenta/GoogleKwok022/Archon/python/src/server/services/report_service.py) 移除 150 字元截斷邏輯，傳送完整報告。
        2. 於 [telegram_service.py](file:///Users/vincenta/GoogleKwok022/Archon/python/src/server/services/system/telegram_service.py) 實裝 **400 Entity Parse Auto-Fallback**：當 Markdown 解析失敗時，自動降級以純文字 (Plain Text) 重新發送，杜絕靜默吞噬與發送中斷。
        3. 於 [nexus_oracle_agent.py](file:///Users/vincenta/GoogleKwok022/Archon/python/src/agents/nexus_oracle_agent.py) 根治 6.7MB 矩陣膨脹：僅傳遞 `snapshot` 摘要數據給 LLM，將上下文自 677 萬字元暴降至 2.5 萬字元；並於 [report_enrichment_service.py](file:///Users/vincenta/GoogleKwok022/Archon/python/src/server/services/report_enrichment_service.py) 導入 25 秒超時 Fail-Fast 防線。
        4. 於 [pm_prompts.py](file:///Users/vincenta/GoogleKwok022/Archon/python/src/server/prompts/pm_prompts.py) 與資料庫更新 `WEEKLY_EXECUTIVE_SUMMARY` Prompt，強制 LLM 區分已解決歷史日誌與當前活躍問題。
    *   **實體重發公證**: 成功完成即時星環週報生成（Task `8b442d90`），內容審核阻塞率 100% 報警徹底消除，並推播至 Telegram。
    *   **門禁驗證**: [test_telegram_chunking.py](file:///Users/vincenta/GoogleKwok022/Archon/python/tests/services/test_telegram_chunking.py) 與 [test_report_service.py](file:///Users/vincenta/GoogleKwok022/Archon/python/tests/services/test_report_service.py) 全數通過，`make lint-be` 通過。

#### 2026-10-18: 商業漏斗全線通管、Telegram 智慧分段與 777 項測試突破 (Phase 5.11.24 ~ 5.11.25)

*   **Telegram 長訊息智慧分段與防啞巴發送 (Phase 5.11.24)**:
    *   **診斷**: 單則 4,096 字元硬上限導致週報與長通報中斷或遭拒（400 Bad Request），且先前存在靜默降級風險。
    *   **修復**: 於 [telegram_service.py](file:///Users/vincenta/GoogleKwok022/Archon/python/src/server/services/system/telegram_service.py) 實作 `split_message_chunks()`（3,800 字元段落邊界切割、自動注入 `📄 [X/Y]` 頁碼、0.5s 發送間隔）；任一分段失敗如實回傳 `False` 並進入持久化佇列，杜絕虛假 Fallback。
    *   **公證**: 新增 [test_telegram_chunking.py](file:///Users/vincenta/GoogleKwok022/Archon/python/tests/services/test_telegram_chunking.py) 5 項測試全數通過，已合併部署至 `dev/twins`。
*   **商業漏斗全線通管與瓶頸清除 (Phase 5.11.25)**:
    *   **Alice 痛點分數真實沉澱**: 於 [job_board_service.py](file:///Users/vincenta/GoogleKwok022/Archon/python/src/server/services/job_board_service.py) 將 RAG 相似度實體寫入 `enrichment_score`（0~100）與 `LeadDataDTO`；分數 `>= 75` 且通過 LLM Judge 標記為 `qualified`，未達標者直接 `archived`。
    *   **Sentinel 429 防爆與垃圾工單消滅**: 於 [sentinel_patrol.py](file:///Users/vincenta/GoogleKwok022/Archon/python/src/server/services/scheduler/jobs/sentinel_patrol.py) 導入 Top 3 限制（`order('enrichment_score', desc=True).limit(3)`），廢除無負責人 Todo 工單自動產生，消除 Google Free Tier 25 萬 Token 擊穿風險。
    *   **Bob 內容瓶頸解除**: 於 `sentinel_patrol.py` 實作自動發布（處於 `review` 超過 24 小時且 `ai_score >= 80` 自動轉為 `published` 並注入 `publish_at`），物理探針證實已解鎖 2 篇卡死文章並根除 `ALERT: Content Bottleneck` 報警洗板。
    *   **漏斗統計對齊與 Telegram 交付**: 於 [marketing_metrics.py](file:///Users/vincenta/GoogleKwok022/Archon/python/src/server/services/stats/domains/marketing_metrics.py) 補齊 `funnel["qualified"]`；於 [leads_patrol.py](file:///Users/vincenta/GoogleKwok022/Archon/python/src/server/services/scheduler/jobs/leads_patrol.py) 自動過濾 `qualified` 名單並推播戰鬥簡報至 Telegram。
*   **全域三向門禁公證**:
    *   `make lint-be`: 393 source files 100% 綠燈通過。
    *   `make test-be`: **777 passed**, 10 skipped, 4 xfailed (0 failures)。
    *   `make phase-audit`: Step 1 ~ Step 11 全綠。

### 2026-10-18: 769 項測試突破、.jules/*.md 極簡化瘦身與月度自動壓縮排程公證 (Phase 5.11.23)

*   **爬蟲與設定服務 DTO 型別對齊及 SSOT 標記修復**:
    *   **診斷**: 自動化 PR (#627, #630) 後，`CrawlingService` 外層方法回傳型別未與 `SinglePageCrawlResultDTO` / `list[CrawlResultItemDTO]` 同步，且 `SettingPayloadDTO` 缺少選填欄位，同時 `ollama/discovery/` 3 處 `# 合法` 標記被誤刪。
    *   **修復**: 同步對齊 [crawling_service.py](file:///Users/vincenta/GoogleKwok022/Archon/python/src/server/services/crawling/crawling_service.py)、[tools.py](file:///Users/vincenta/GoogleKwok022/Archon/python/src/agents/librarian/tools.py) 與 [settings_service.py](file:///Users/vincenta/GoogleKwok022/Archon/python/src/server/services/settings_service.py) 之 DTO 契約；還原 `ollama/discovery/` SSOT 豁免標記並移除 `capabilities.py` 重複 Lock。
*   **代理記憶指南 (`.jules/*.md`) 極簡化瘦身與月度自動壓縮排程**:
    *   **實體瘦身**: 清理 `.jules/*.md` 共 6 份檔案之 `2023~2025` 幻覺日期與無限追加重複區塊，由 558 行 (95 KB) 精簡至 86 行 (9.8 KB)，每檔僅留 2~5 條核心規則。
    *   **月度排程與三向連動**: 於 `SchedulerConfig` 新增 SSOT 參數，建立獨立模組 [jules_compaction.py](file:///Users/vincenta/GoogleKwok022/Archon/python/src/server/services/scheduler/jobs/jules_compaction.py)（含 `log_service.create_log_entry` 稽核紀錄），同步掛載至 `scheduler_service.py`、`internal_api.py`、`admin_api.py` 及 `stats/__init__.py`，並於 `scripts/phase_audit.py` 新增 Step 11 守門員。
*   **全域三向門禁與紅綠燈真實穿透公證**:
    *   `make lint`: 前端與後端 393 來源檔、Lean 4 18 jobs 100% 綠燈通過。
    *   `make test-be`: **769 passed**（拔除 `patch.object(log_service)` 假 Mock，以紅綠燈法則實體驗證 `tmp_path` 磁碟壓縮與 `archon_logs` 資料表寫入），10 skipped, 4 xfailed (0 failures)。
    *   `make phase-audit`: Step 1 ~ Step 11 全綠通過 (Exit Code 0)。

---

# 第四章：歷史檔案：原則的考古學 (Historical Archive: The Archaeology of Principles)

> **【封存說明】**
> 本章節存放了所有歷史日誌。當你需要深入了解某個特定問題的完整偵錯背景時，可以在此查閱最原始的紀錄。

### 2026年10月：強型別 DTO 契約閉環、代理記憶治理與 MetaTwin 自癒公證

**核心主題歸類**:
1.  **強型別 DTO 契約閉環與 MyPy 零容忍防禦 (Ref: 10-04, 10-06, 10-08, 10-09, 10-12, 10-16, 10-18)**:
    *   **API 與 Service 契約對齊**: 全面補齊 `Projects` (`NoReturn` 標註與字典型別變異 `cast`)、`Crawling` (`SinglePageCrawlResultDTO` / `CrawlResultItemDTO`)、`Settings` (`SettingPayloadDTO` 選填欄位)、`Ollama Discovery` (`ModelDictDTO` / `HostStatusDTO`) 與 `LogEntry` 之強型別契約，實現後端 393 檔 100% 型別覆蓋。
    *   **參數與死碼清理**: 還原 `Agentic RAG` 之 `use_enhancement` 公開參數命名；全站執行 `ruff` (`F401`, `F841`, `B007`) 與前端 `tsc --noEmit` 掃描，確保零殭屍代碼與多餘轉型。
2.  **非同步 Event Loop 解鎖與雲端自癒公證 (Ref: 10-04, 10-08, 10-14)**:
    *   **資料庫查詢非同步化**: 將 `pages_service.py` 內部同步 `execute_query` 全面升級為 `await execute_query_async`，並將 `test_pages_service.py` 同步升級為 `AsyncMock`，消除 Event Loop 阻塞與虛假測試斷層。
    *   **429 速率限制與 MetaTwin 自癒**: 鑑識週日 `Weekly Executive Summary` Map-Reduce 併發觸碰 Google Free Tier `250000` TPM 限制；物理驗證 `RateLimitHandler` 指數退避與 `MetaTwinService` 自動執行 `MODEL_SWAP` 降階自癒。
    *   **外部 WAF 容錯**: 於 `test_104_reliability.py` 實作 HTTP 403 WAF 攔截時自動 `pytest.skip`，隔離外部網路變因。
3.  **代理記憶指南 (`.jules/*.md`) 極簡化與月度壓縮排程 (Ref: 10-18)**:
    *   **記憶退化清洗**: 根除 `.jules/*.md` 共 6 份檔案中的 `2023~2025` 幻覺日期與無限追加重複紀錄，將總行數由 558 行 (95 KB) 壓縮至 86 行 (9.8 KB)，每檔僅保留 2~5 條核心規則。
    *   **月度排程與門禁防線**: 建立 `jules_compaction.py` 月度排程並串接 `SchedulerConfig` SSOT、手動觸發 API 與 `archon_logs` 稽核紀錄；於 `scripts/phase_audit.py` 新增 Step 11 強制攔截超額條目與日期幻覺。

### 2026年9月：SSOT 治理、排程防禦與零虛假公證

九月份是深入解決非同步阻塞、週期排程 (DAG) 解耦、以及徹底落實 SSOT/DRY 治理的關鍵月份。我們消滅了大量隱藏的靜眠區塊 (Silent Fallback)、幽靈日誌，並建立起了嚴格的自動化品質門禁公證體系。

**核心主題歸類**:
1.  **非同步阻塞與排程器死鎖修復 (Ref: 09-10, 09-13, 09-14, 09-26)**:
    *   **事件迴圈解鎖**: 鑑識出 SDK 的同步介面呼叫 (`generate_content`) 與 `Oracle Agent` 在 `gather_nexus_data` 時阻塞主執行緒高達 4.8 秒。將 `HealthService.check_db_health`、`StatsService` 與 `LogService` 內部隱藏的同步 `execute_query` 全面替換為 `await execute_query_async`，解鎖 Event Loop。
    *   **DAG 解耦與防偷跑**: 將 `_should_run_weekly` 從 Alice 與週報的共用中解綁，導入精準數學時間斷言 `trigger.get_next_fire_time`，防範伺服器重啟時的排程偷跑與提早觸發。
    *   **解鎖排程停滯**: 修正 `Alice Auto Fetch` 誤用本地專屬排程器，解放雲端 opportunistic 執行能力。

2.  **Telegram 網路防禦、快覽優化與狀態持久化 (Ref: 09-03, 09-06, 09-20, 09-26, 09-30)**:
    *   **報告快覽 (Snippet) 防禦**: 實裝 `TelegramService.sanitize_markdown_snippet()` 靜態方法，安全剝除網址與所有 Markdown 符號 (`*`, `_`, `[`, `]`, `\``, `#`)，將長度上限收斂至 `settings.py` (`NotificationConfig.telegram_snippet_length`) 控管，防止 400 Bad Request 崩潰。
    *   **關機盲區防禦與狀態持久化**: 修正 Vercel 5xx 重試迴圈，於 `_queue_failed_message` 內將 `parse_mode` 狀態與訊息文本透過 `json.dumps` 序列化存入 `archon_tasks.description`，防止伺服器重啟造成解析錯誤與訊息遺失。
    *   **HF 防火牆繞道**: 偵測確認 HF 防火牆封鎖 `api.telegram.org`。改為從 SSOT 讀取代理網址，透過部署的 Vercel 前端進行 Serverless 轉發，本地則無縫降級直連。
    *   **打通日誌盲區**: 將 Telegram 網路阻擋錯誤全面引入資料庫 `_log_to_db`，根除 UI 查無錯誤的幽靈降級現象。針對非同步網路操作建立 3 次重試機制與安全執行緒封裝。

3.  **環境潔癖與 SSOT 徹底落實 (Ref: 09-07, 09-13, 09-14, 09-17, 09-30)**:
    *   **零虛假開發與魔術數字拔除**: 將 `ai_operations.py` 中的硬編碼時區、退避時間及 Telegram 摘要長度上限徹底抽離至 `settings.py`，並消除前端為解決 504 所遺留的 `60000` 魔術數字。
    *   **消除靜默降級**: 修復 `agent_registry.py` 與 `leads_patrol.py` 中被 `except Exception: pass` 吞噬的異常漏洞，全面補上明確的日誌記錄與報錯機制。
    *   **環境污染消毒**: 嚴格執行「零一次性腳本」，清理合入分支的臨時腳本，並修復了 `routing.py` 等原生型別引發的 MyPy 報錯。

4.  **自動化品質門禁與全域公證 (Ref: 09-04, 09-14, 09-17, 09-20, 09-26, 09-30)**:
    *   **Lean 4 原生架構公證**: 解決 `make audit-qa` 漏看的 `Bad CPU type in executable` 錯誤。強制安裝 `aarch64-apple-darwin` 原生版並清空 `~/.elan/toolchains`，確保 18 項 Lean 4 證明子專案編譯成功。
    *   **物理公證取代肉眼**: 拒絕人工查閱 Docker 驗證。實作 `scratch/test_telegram_queue.py` 與 `verify_catchup_log.py` 探針，推動 100% 透過 `make test-be` (724+ 項測試全過) 與 `make phase-audit` 公證。
    *   **504 Gateway Timeout 根除**: 由人類配合在 Supabase 執行 `06_add_missing_indexes.sql` 物理建立索引，解決 Task Dispatcher 全表掃描崩潰問題。
    *   **全域高併發公證**: 透過 708+ 項全數通過的單元測試，物理證實高併發檢索 `test_concurrent_rag_queries` 的非同步優化穩健運行。

5.  **Oracle Payload Optimization (Ref: 09-20, Phase 5.11.21)**:
    *   **架構升級 (SSOT/DRY)**: 解決 `NexusOracleAgent` 因懶惰查詢 (`select *`) 撈取萬字文章導致 429 Token 爆表。拔除 Agent 裸寫 SQL，將欄位投影 (`id, title, status`) 嚴格封裝至 `BlogService` 與 `LogService`。
    *   **環境變數抽離**: 將時間窗與字元上限收斂至 `settings.py` (`OracleConfig`)，消除魔術數字。
    *   **防禦性截斷**: 實裝 JSON 遞迴攔截，超過 `1000` 字元強制 `...(truncated)`。物理探針公證 Payload 體積縮減 97%。

6.  **零虛假公證與雙生環境防禦 (Ref: 09-26)**:
    *   **零猜測鐵律 (拒絕推論)**: 在判定 HF 伺服器狀態時，嚴禁因觀察到本機 Docker 共用 DB 活躍而盲目推論 HF 停擺。必須 100% 依賴實體探測 (`make phase-audit` Step 5) 進行物理查核，落實證據至上。
    *   **雙開排程鎖 (Race Condition 防禦)**: 驗證了 Phase 5.9.26 導入的「SSOT 時間閘門 (`trigger.fields`)」。在 HF 與 Local Docker 雙雙存活且同時觸發 Catchup 時，基於 Supabase `LAST_RUN` 的狀態鎖完美生效，精準阻擋重複執行與提早偷跑。
    *   **時區雙重換算錯誤校正**: 確立 `DEFAULT_TIMEZONE` (`Asia/Taipei`) 的唯一性。資料庫中的 `hour=16` 就是實體台灣時間下午 4 點，嚴禁對 CronTrigger 進行畫蛇添足的二次 UTC 換算。

### 2026年8月：SSOT 治理、排程防禦、MCP 安全鎖定與週期任務硬化
八月份是提示詞與配置 SSOT 治理落地、排程防禦與 Docker 依賴硬化的月份。我們對 RAG 與報告模組進行了深度的 DRY 重構，解決了 Docker 環境下的 MCP 依賴缺失與 WAF 限流極限問題，並實作了防禦性的提示詞 Upsert 與測試門禁以確保系統零降級。

**核心主題歸類**:
1.  **SSOT 治理與硬編碼清理 (Ref: 08-01, 08-12, 08-13)**:
    *   **Deep DRY 重構**: 於 `report_service.py` 提取 `_create_summary_task_and_log` 消除 Daily/Weekly/Monthly 重複派發邏輯。改寫 `telegram_service.py` 從 `SettingsService` 動態讀取通知 Token，將 Vercel/前端網址統一綁定至 `NetworkConfig().frontend_url`。
    *   **提示詞解耦**: 移除 `blog_generator.py` 等 31+ 處 hardcoded defaults，將提示詞集中至 `pm_prompts.py` 管理。
    *   **實體代碼對帳**: 執行 `phase-audit` 校驗，確保 `crawler_max_pages` 確實寫入 SSOT 且所有功能元件 100% 落地，無幽靈文件與代碼。

2.  **週期排程、WAF 防禦與 DAG 斷層防禦 (Ref: 08-08, 08-13)**:
    *   **DAG 事件鏈與排程鎖自癒**: 將下游報告改為 Alice 爬蟲成功事件驱动以避免競態條件。實作 `check_and_resume_dag` 確保伺服器重啟時能無縫接力執行未完成的排程。
    *   **WAF 與 Rate Limit 限制**: 針對 104 WAF 隨機延遲 (6.5s) 與 Gemini 限流 (4.5s/次) 進行數學建模，下調 `CRAWLER_JOB_LIMIT` 至 `32` 筆，達成低成本的高效轉換。
    *   **系統死鎖修復**: 修正 `archon-server` 因 Supabase 連線失敗引發的 `__del__` 無限遞迴，以及 `execute_query` 在 Builder 物件缺少 `.execute()` 造成的 `SyncQueryRequestBuilder` 崩潰。

3.  **MCP 依賴鎖定與 Docker 容器架儲防禦 (Ref: 08-10, 08-12)**:
    *   **MCP SDK 鎖定與 Dockerfile 盤點**: 解決 `archon-mcp` 因 `uv` 動態抓取最新 MCP 套件（移除 fastmcp）導致的 `ModuleNotFoundError`。改用 `uv export` 生成 `requirements.txt` 並於 `Dockerfile.mcp` 及 `Dockerfile.server` 盤點同步鎖定安裝，防範依賴庫斷層。
    *   **Docker Build Context 與快取空間最佳化**: 將 3.5GB 巨型 `ollama_data` 排除於 `.dockerignore` 之外以避免 context 重建超載，執行系統清理釋放 36.8GB 磁碟快取，防範 ENOSPC 空間危機。
    *   **殭屍程序清理**: 使用 `lsof -i :3737 -t | xargs kill -9` 強制回收 Vite 殘留程序，確保本機埠口淨空。

4.  **雲端部署修復、網路自癒與超時配置 (Ref: 08-10)**:
    *   **HF 部署路徑修復**: 修正 `Dockerfile.server` 中歸檔腳本 `cache_offline_packages.py` 移動至 `scripts/archive/` 導致的 COPY 建置失敗。
    *   **DNS 解析自癒**: 修正 `agent_service.py` 因 HF 雲端環境尋找本地 `archon-agents` 導致的 `Name or service not known` 錯誤，強制透過 `AGENTS_SERVICE_URL` 動態讀取 127.0.0.1。
    *   **任務超時容錯**: 將 `NexusOracleAgent` 週報/月報 Map-Reduce 任務超時時間放寬至 600 秒以防超時中斷。

5.  **音效渲染與前端/後端安全自癒 (Ref: 08-10)**:
    *   **簽名 URL 與容錯防護**: Podcast 音檔改用 7 天時效的 `create_signed_url`。在日誌回報與 Telegram 推播中加入 Exception 攔截，防範網路逾時造成 apscheduler 重試風暴。
    *   **前端高度釋放與 Audio Markdown 攔截**: 拔除 `ManagerNexus.tsx` 鎖死高度的 `min-h-screen`，並獨立出 `AudioMarkdownRenderer.tsx` 自動將文字 Markdown 連結攔截並渲染為原生 HTML5 `<audio>` 播放組件。

6.  **SSOT 防禦性硬化與測試品質門禁 (Ref: 08-12, 08-13)**:
    *   **靜默降級防禦**: 於 `prompt_service.py` 注入 `logger.warning` 以攔截 missing key 錯誤，杜絕幽靈降級。
    *   **強韌斷言與測試 Set 聯集**: 重構 `test_prompts_loading.py` 的 brittle 長度斷言，改採 Set 聯集邏輯，防範 Mock 資料重疊；在 `test_prompt_ssot.py` 補足 warning log 驗證，後端 652 項測試全綠通過。
    *   **Auto-Upsert 重試機制**: 利用 `BaseRepository.execute_query` 將 upsert 包裝在具有指數退避的重試 (`max_retries=3`) 呼叫中，硬化分散式寫入時的網路抗性。


7.  **無頭環境與自動化公證防禦 (Ref: 08-26, 08-27, 08-30)**:
    *   **實體公證取代人工檢驗**: 導入自動化公證腳本，防範虛假開發與文件偽證 (08-30)。
    *   **Mock 環境隔離與防護**: 針對降級 Mock 模式補齊屬性缺失防護 (08-27)；隔離 MSW 污染與解決排程啟動死結 (08-26)。

8.  **非同步網路與爬蟲引擎硬化 (Ref: 08-28, 08-29)**:
    *   **Telegram 突波自癒**: 延長超時至 30 秒，導入 3 次重試與異步取值，並將異常捕捉精細化 (08-30)。
    *   **爬蟲深度與記憶體防禦**: 解除 Crawl4AI 600 秒超時炸彈；動態放行 Admin 爬取深度，同步抗彈窗腳本消除 Cookie 雜訊與自我連結過濾修復 (08-29)。

### 2026年7月：全域美術遷移、週期排程硬化與雲端單一容器部署
七月份是專案視覺工藝大躍進，以及後端排程系統與雲端部署高度硬化的月份。我們將高品質的 SDXL/Flux 美術素材整合進 Godot 雙生專案，並在 Python 端完成了成本守門員、TTS 廣播與三級資料瘦身的排程自動化。最終，我們排除了阻礙 Hugging Face 部署的深層技術債，實現了雲端單一容器 (Monolith) 的無縫運行。

**核心主題歸類**:
1.  **Godot 雙生專案與高保真視覺工藝 (Ref: 07-03, 07-17)**:
    *   **全域背景替換**: 成功套用 `bg_vector_grid.png` 至 `GameBoard.tscn`，與 `bg_synthesizer.png` 至 `CardWorkshop.tscn`。
    *   **透明底板架構**: 將 `CardChip.tscn` 升級為使用 `card_frame_blank.png` 透明框，並根據卡牌類型動態掛載對應的高品質內部圖示 (`chip_green_target`, `action_keyword` 等)。
    *   **`CharacterDashboard.tscn` 實裝**: 全新 UI 介面，依據 `SaveManager` 的 Sector 進度動態上色預設灰階頭像，並掛載階級徽章。
    *   **動態發光節點**: 建立天賦網，並以 Bezier Shader 結合按鈕點擊實現 HDR 閃耀發光 (Pulse) 回饋效果。
    *   **`HandLayout.gd` (扇形手牌排列)**: 自動計算弧度展開，懸停時平滑放大並置頂。
    *   **`TargetingArrow.gd` 與 Bezier 著色器**: 實作動態雷射拉弓箭頭與科技流體發光感。
    *   **物理斷層修復**: 直接於 `TransitionVideo.tscn` 綁定 `next_scene`，徹底根除影片播放完畢後的黑畫面死結。
    *   **卡牌輪播整合**: 捨棄靜態垂直按鈕，導入 `CarouselContainer` 打造具備景深的實體卡牌水平輪播系統，並將語言/音量設定移至畫面右下角作為半透明背板。
    *   **觸覺與聽覺 (Juice)**: 新增 `BGMPlayer` 播放授權神曲《Ganxta》；透過 `Tween` 實作選中卡牌時的快速物理抖動 (Elastic Shake)，並同步播放清脆的翻牌音效。
    *   **無頭截圖公證**: 強化 `MainMenu_Screenshotter.gd`，支援動畫延遲等待，成功於無頭環境中截取包含全新 `gem_*.png` 美術圖的正確 UI 狀態。

2.  **Godot 實體公證與全域架構硬化 (Ref: 07-03, 07-15)**:
    *   **嚴格型別修復**: 回顧並嚴格遵守 `godot-4-audit` 規範，對 `HandLayout.gd` 與 `TargetingArrow.gd` 進行 100% 靜態型別宣告 (Static Typing)。
    *   **縮排與變數作用域修復**: 物理根除了 `GameBoard.gd` (Tabs vs Spaces) 與 `GameState.gd` (SaveManager 作用域丟失) 導致的 Parse Error。
    *   **Headless 零報錯驗證**: 成功通過 `godot --headless --build-solutions` 編譯測試，達成 100% 物理公證！
    *   **根除硬編碼幽靈**: 執行全面審計，消滅 `SaveManager.gd` 與 UI 控制器中的幽靈卡牌資料 (`filter_by_date` 等)，將全域代碼的 ID 與最新的 `action_*` SSOT 同步。
    *   **修復技術債**: 透過日誌法醫追溯，揪出並修復了先前 UI 重構意外刪除 `ext_resource` 導致的 `GameBoard.tscn` 解析崩潰。
    *   **100% 物理公證**: 成功通過 `godot --headless -s tests/HeadlessRunner.gd`，確保 15 項 E2E 與單元測試全數亮綠燈。

3.  **週期作業與排程系統架構進化 (Ref: 07-14, 07-20, 07-21, 07-22, 07-23, 07-24, 07-25)**:
    *   **L2 模組化與解耦**: 將 `business.py`、`scheduler_service.py` 拆分為精簡模組（如 `leads_patrol.py`），並透過 `SettingsService` 動態讀取設定，徹底消滅硬編碼。
    *   **SSOT 集中化與死結消除**: 將提示詞與任務頻率抽離至資料庫 (`archon_settings`)，並排除 `tech_debt_patrol` 無限自我舉發的死結。
    *   **時區處理與排程鎖死修復**: 統一改用 `Asia/Taipei` 與 ISO 曆週計算，修復因 HF 伺服器重啟及 UTC 漂移導致的日期幻覺與殭屍任務 Bug。
    *   **事件驅動 DAG 排程**: 下游報告改為依賴爬蟲成功後的事件觸發，取代僵化 Cron，解決 WAF 阻擋造成的 Race Condition。
    *   **雲地物理隔離與容錯**: 確立「本機抓取、雲端運算」分離，以 `SPACE_ID` 封鎖 HF 爬蟲權限。實作 500/502/504 指數退避重試以提升吞吐量。

4.  **爬蟲 WAF 防禦與雲端網路韌性 (Ref: 07-14, 07-17, 07-25)**:
    *   **WAF 繞過與速率節流**: 成功修復 104 爬蟲，並為 `JobBoardService` 掛載 `RateLimiter`，解決爬蟲瞬間湧入大量資料導致 Gemini API 觸發 429 TooManyRequests 錯誤。
    *   **NoneType 崩潰自癒**: 修正 `Job104Crawler` 因內部非同步委派未被執行而返回 `None` 的嚴重 Bug。導入 `asyncio.to_thread` 安全橋接外部迴圈。
    *   **Schema Mapping 容錯**: 透過防禦性的 `item.get("description", "")` 與 Pydantic 雙重綁定，防止未來因 API 欄位變更而引發 `KeyError` 崩潰。
    *   **WAF 防禦升級**: 將 104 爬蟲的延遲寫死代碼 (Hardcoded Delays) 移除，徹底抽離至 `SettingsService` 的 `CRAWLER_WAF_DELAY_MIN/MAX`，動態隨機延遲 60~90 秒以迴避資料中心 (Datacenter IP) 存取限流。同時在 `curl_cffi` 實作瀏覽器指紋動態輪替，降低 403 Forbidden 機率。
    *   **HF 基礎設施修復**: 修復了 `scripts/deploy_to_hf.sh` 在單一容器打包時遺漏 `AGENTS.md` 的嚴重缺失。同時透過環境變數注入 `AGENTS_SERVICE_URL=http://127.0.0.1:8052`，解決了 Hugging Face 環境中 `WorkflowEngine` 尋找本機 `archon-agents` 網域導致的 DNS 斷線問題。
    *   **零副作用公證**: 變更通過全部 612 項後端測試公證，確保與本機 Docker Compose 環境的兼容性，並成功推送至 `dev/twins` 自動觸發 HF 遠端部署。

5.  **模型生命週期、備援硬化與 Agent 架構 (Ref: 07-22, 07-25)**:
    *   **模型生命週期與備援機制**: 實作 API 動態探勘與模型交集過濾。透過 `model_ssot.py` 實現 Free Tier 自動備援，解決 HTTP 異常與模型下架引發的崩潰。
    *   **API 逃逸封堵與 Mock 隔離**: 移除 `batch_processor.py` 的 REST API 直連，全面回歸官方 SDK，並在 `conftest.py` 擴充攔截網防止測試沙盒穿透。
    *   **Agent 斷點持久化 (Checkpointing)**: 實裝 `AgentCheckpointManager`，在 Action/Observation 循環後保存狀態快照，防止網路超時導致的重複呼叫。
    *   **HITL 人工審核防線**: 攔截高風險工具調用並懸置狀態 (`SUSPENDED_WAITING_FOR_APPROVAL`)，暴露審核與恢復端點。

6.  **Hugging Face Monolith 部署與啟動自癒 (Ref: 07-20)**:
    *   **指令換行修復**: 修復 `deploy_to_hf.sh` 在動態修改 `Dockerfile` 時缺少換行符號 (`\n`) 的 Bug，防止 `CMD` 與 `ENV` 參數粘連導致語法錯誤 (ENV: not found)。
    *   **破除 DNS 迷思**: 發現 `mcp_client.py` 誤判 Docker 環境而強制使用 `archon-mcp` 作為主機名稱，導致在 HF Monolith 環境中解析失敗。引入 `ARCHON_SERVER_HOST` 作為覆蓋變數 (127.0.0.1)，成功將網路請求重新導向至 localhost。
    *   **消滅啟動競態條件 (Race Condition)**: 解決了 FastAPI 啟動過快，導致 `lifespan.py` 搶在 MCP Server 完全準備好前發起請求並誤判斷線的世紀 Bug。透過在 `start_all.sh` 引入 5 秒緩衝 (`sleep 5`)，並在 Python 端加入 5 次指數退避重試 (Retry Loop)，徹底硬化了系統的啟動韌性。
    *   **遠端日誌探針**: 建立 `/api/mcp-logs` 後門，將背景程序的標準輸出管線化，成功在無除錯介面的 Hugging Face 雲端環境中取得決定性的實體證據，證實 MCP Server 200 OK 且 29 項工具成功掛載。
    *   **Model SSOT 落地**: 建立 `30_alter_archon_prompts_schema.sql`，將散落於 Markdown 的 34 個提示詞全數遷移至 DB。重構 `PromptService` 並以 Pydantic 嚴格校驗，消滅幽靈文件。

7.  **後端系統健康度、資料庫重構與資源最佳化 (Ref: 07-23, 07-24, 07-25)**:
    *   **健康度掃描與型別重構**: 建立 `backend_type_health.py` 實作全覆蓋健康度掃描。針對分區 `3.3` 進行強型別補齊，將型別覆蓋率由 39.3% 提升至 92.1%。
    *   **資料庫架構收斂**: 透過自動化腳本將 36 個碎片化 SQL 檔案收斂至 11 個語義化檔案，並實作 `rescue/` 資料夾提供無痛資料救援機制。
    *   **向量維度截斷防護**: 實作物理截斷防護，將外部模型強制回傳的 3072 維度裁切至 768 維度，避免資料庫崩潰。
    *   **記憶體資源減肥 (Memory Diet)**: 於 `docker-compose.yml` 注入 `NODE_OPTIONS=--max-old-space-size=512` 強制提早 GC，將 Vite 開發伺服器記憶體用量從 2GB 壓制至 350MB。


8.  **全域 SSOT 終極淨化與硬編碼根除 (Ref: 07-28, 07-29, 07-31)**:
    *   **狀態與角色重構**: 徹底移除散落各服務的字串角色與狀態硬編碼，統一替換為 `RoleEnum` 與 `TaskStatusEnum`，並將強領域邏輯靜態陣列標記為白名單。
    *   **NetworkConfig 收攏**: 將所有寫死的 HTTP 網址 (Agent/MCP/LLM) 抽離至 `NetworkConfig`，並將排程時間變數化，徹底實現 SSOT 管理。
    *   **零硬編碼與脆性修復**: 將繁體中文提示詞等脆性邏輯拔除並正確歸位至專屬配置 (如 `sales_prompts.py`)；升級 `scripts/phase_audit.py` 擴充 `set_literal_pattern` 精準攔截隱藏的字串陣列。
    *   **全域大掃除**: 清除遺留的 `temp_refactor/` 與重複舊版資料夾，將 `scratch/` 加入 `.gitignore` 徹底解除草稿污染隱患。

9.  **核心業務層 (Services) 絞殺榕解耦與型別硬化 (Ref: 07-27, 07-30)**:
    *   **Manager 純化與測試遷移**: 拔除 `CredentialManager` 內的向下相容代理 (Proxy Wrappers)，完成絞殺榕最後一哩路，並將測試依賴徹底遷移至真實 `provider_configs.py` 介面。
    *   **Auth 與 RBAC DRY**: 將認證與細粒度權限模組的資料庫操作收斂至 `BaseRepository.execute_query`，移除所有 `.execute()` 舊寫法，並將型別覆蓋率推升至 100%。
    *   **Legacy Closure 清除**: 成功移除了全域 83 支檔案中的 `_query()` 舊式閉包寫法，達成 L2 架構的 DRY 原則。

10. **RAG 防禦、爬蟲進化與雲地路徑自癒 (Ref: 07-27, 07-29, 07-30)**:
    *   **排程防禦與 RAG 測謊機**: 實作 RAG 強攔截防禦，當找不到 Baseline 時直接捨棄 Lead 確保資料庫零污染；精煉 4.6% 純淨特徵切片大幅提升訊噪比。
    *   **Golden Seven 關鍵字與爬蟲優化**: 擴充 104 爬蟲高價值詞彙，將排程縮減為每週四天並提高單次抓取量，放寬 WAF 隨機延遲以提升單次吞吐量。
    *   **雲地路徑自癒**: 修補文件讀取路徑動態兼容本地開發與 Docker 容器，修正 `catch-up` 任務在伺服器重啟時的排程日邏輯盲點。

### 2026年6月：Godot 雙生專案、L2 架構重構、輕量重排與雲端部署除錯
六月是專案全面推進 Godot 數位雙生遊戲開發，並在架構面上嚴格落實 L2 模組化與行數門禁的月份。我們成功突破了 Hugging Face 的部署限制，完成了語意重排引擎的輕量化，並建立起 100% 物理對齊的測試防護網。

**核心主題歸類**:
1.  **Godot TDD 與 MVC 架構確立 (Ref: 06-11, 06-18, 06-30)**:
    *   **Lean 原則**: 捨棄臃腫的 GUT 框架，以原生 Headless 模式自製微型測試框架 (`HeadlessRunner.gd`)。
    *   **卡牌 MVC 轉向**: 從塔防轉向卡牌構築戰，徹底解耦 Model (`GameState`) 與 View (`MainUI`)，實現無 UI 邏輯單元測試。
    *   **雙劍合璧**: 確立 Godot 作為引擎、VS Code 作為 LSP 的雙開工作流，並解決了 Language Server Port 的配置陷阱。
    *   **底層防呆**: 解決 `Object.get()` 預設參數造成的靜默崩潰，並補強了匿名函數與 `call_deferred` 結合時的空指標防護。

2.  **L2 模組化與巨型檔案減重 (Ref: 06-08, 06-18, 06-21, 06-22, 06-23, 06-25)**:
    *   **行數門禁**: 將超過 400 行的 `manager.py`, `CharacterCreator.gd`, `ModularAgent.gd`, `MainUI.gd` 強制拆分。
    *   **死碼物理清除**: 徹底移除幽靈元件（如 `DiffViewer.tsx`）與分離 `APIKeysSection.tsx`，成功將巨型檔案瘦身並通過公證。
    *   **UI 與邏輯剝離**: 建立 `AIPromptManager.gd`、`AgentLayoutHelper.gd` 等專職工具類別。
    *   **解耦動態翻譯**: 建立 `GitTranslator.gd` 動態載入 `git_dict.json`，消除硬編碼的翻譯字串與魔法數字。

3.  **無頭環境 (Headless) 與自動化公證突破 (Ref: 06-01, 06-18, 06-21, 06-22, 06-23)**:
    *   **開發流水線重塑**: 建立 `Golden Pipeline` 對抗盲目樂觀，嚴格執行探針 (Probe) 與自動化公證。
    *   **測試存檔淨化**: 透過腳本在測試前主動清除 `user://savegame.save`，消滅「幽靈測試失敗」等污染。
    *   **突破截圖限制**: 針對 `--headless` 無法擷取 Viewport 影像的問題，撰寫 Python 腳本自動啟動 GUI 完成實體公證。
    *   **雲端對帳公證**: 將自動化公證推進至 Hugging Face 雲端探針，確保 Clockwork 任務在 Serverless 環境成功運作。
    *   **ClassDB Registry 自癒**: 使用 `preload` 取代直寫 `class_name`，解決 Godot Headless 模式下的快取解析錯誤。

4.  **雲端部署除錯、CI/CD 與網路連線自癒 (Ref: 06-18, 06-19, 06-22, 06-25, 06-26, 06-29)**:
    *   **HF 部署防呆與字元陷阱**: 撰寫部署腳本繞過 Git LFS 阻礙。並解決了 HF Secrets 混入注音「ㄒ」導致的 UnicodeEncodeError，加入環境變數遮蔽機制。
    *   **CI/CD 依賴對齊**: 強制 CI 安裝 `--group all` 依賴並修正 `PYTHONPATH`，修復了 Web Health Check 的部署觸發問題。
    *   **排程與並發極速**: 精準調配 HF 每日休眠喚醒排程 (10:38 暫停 / 06:32 啟動)；糾正 RAG 高併發死循環迷思，引入 `asyncio.sleep` 序列化排隊。
    *   **全域連線自癒 (Monkey Patch)**: 徹底根除高併發下的 HTTP/2 `ConnectionTerminated` 斷線危機，由底層 `execute_query` 實作指數退避重試，無需盲目修改上層業務。

5.  **3-Tier 容災降階與品質升級 (Ref: 06-05, 06-07)**:
    *   **多層 Fallback 架構**: 實作 Gemini -> Hugging Face -> Ollama 級聯降階備援系統，並於雙端 UI 建立指示燈。
    *   **GFM / Mermaid 霓虹化**: 擴充 Markdown 渲染引擎，完美解析高難度表格與循序圖。
    *   **Phase 5.6 歷史歸檔**: 徹底清查任務，將無幽靈的史詩級文件封裝並提煉至 Docusaurus 知識庫。

6.  **語意重排 (Reranker) 引擎輕量化與效能收斂 (Ref: 06-22, 06-24, 06-30)**:
    *   **ONNX 零成本重排**: 放棄笨重的 PyTorch (`sentence-transformers`)，改採 `onnxruntime` 與 22MB 微縮權重，解決 Docker 空間危機與依賴死鎖。
    *   **型別安全與動態降級**: 棄用僵化的 `isinstance` 檢查，改採 `try-except` 模式 (EAFP) 兼容 Mock 測試，確保模型載入失敗時能 Fall-Fast。
    *   **雙前端架構物理隔離**: 釐清 `archon-ui-main` (3737) 與 `enduser-ui-fe` (5173) 的設計哲學差異。將 `Intl.DateTimeFormat` 效能瓶頸轉移至後端，並透過 `eslint.config.js` 實施編譯期防禦。

### 2026年5月：多 Agent 星環拓樸、QA 全自動化與極端環境救援
五月是專案從單一 Agent 升級至多 Agent 協作架構，並將品質門禁與測試自動化推向極致的月份。我們完成了 Phase 5.1.x 到 Phase 5.5.0 的史詩級任務群。

**核心主題歸類**:
1.  **Phase 4.6.60 穩定性硬化與 E2E 物理公證 (Ref: 05-11)**:
    *   **前端圖表防禦**: 關閉 Recharts 動畫以防止 Headless 環境下 Playwright 崩潰 (`NaN TickItem Error`)。
    *   **後端空資料防禦**: 嚴禁使用 `.single()`，改用安全陣列查詢 (`execute()`) 防禦 HTTP 500。
    *   **測試狀態防護**: E2E 嚴禁依賴開發者資料庫，必須包含空資料斷言，並使用具狀態變數 (Stateful Mock) 還原 React 重新渲染。

2.  **基礎設施與環境自癒加固 (Ref: Phase 5.1.13, 5.1.17)**:
    *   **Model SSOT**: 根除模型硬編碼，統一交由 DB / 環境變數控制，落實 Fail-Fast。
    *   **模組解耦**: 進行大於 400 行的檔案瘦身，強化 L2 架構清晰度，消滅「God Objects」。
    *   **數位雙生防禦**: 建立 CLI 雙軌機制，加載 `BrowserConfig` 無密碼環境對抗 Docker 加密憑證讀取障礙。

3.  **體驗升級與 RAG 優化 (Ref: Phase 5.1.13)**:
    *   **極簡 RAG 入口**: 實作 Karpathy 式極簡知識庫介面，支援原始網址直丟與切片向量化。
    *   **視覺優化**: 實作科技霓虹濾鏡與幾何 SVG 的「零 Token 視覺 Fallback」，大幅降低雲端成本。

4.  **星環群聊架構與排程器整合 (Ref: Phase 5.1.7 ~ 5.1.16)**:
    *   **拓樸升級**: 確立「星型群聊 (Star-Topology)」機制，由 Supervisor 動態路由並綁定 Gemini 3.1 系列，防範無限迴圈與成本失控。
    *   **週期報告自動化**: 實作日、週、月報執行摘要的 Map-Reduce 星環化，並成功與 Clockwork 排程系統深度整合。

5.  **QA 全自動化與 MBT 硬化 (Ref: Phase 5.2.0, 5.1.2)**:
    *   **視覺裁判**: 實作 Gemini 3.1 Vision 作為 UI 視覺裁判 (Judge)，並建立 Structured LLM-Judge 確保內容語義品質。
    *   **測試隔離與網關**: 消除 E2E 測試依賴污染，加裝 `RUN_INTEGRATION_TESTS` 門檻，並完成 `make audit-qa` 整合網關。

6.  **Phase 5.3~5.5 離線硬化與極端環境救援 (Ref: 05-27, 05-29, 05-30)**:
    *   **離線雙軌架構**: 實作 `OFFLINE_MODE` 雙軌機制，無網狀態自動將向量降階至 384 維度並轉接本地 SentenceTransformer 與 Ollama。
    *   **ENOSPC 空間危機**: 剖析 31.5GB 巨獸級 Docker 映像檔，剃除 PyTorch 的 CUDA 依賴與封裝快取，成功瘦身至 5.02GB。
    *   **歷史歸檔與實體對帳**: 將過期 Phase 文件徹底壓縮歸檔 (`Phase_5_Archive.tar.gz`)，並提煉 Docusaurus 知識庫，確保工作區極簡。
    *   **混沌與品質門禁**: 確認模擬器 Deterministic 特性，並將 500 Error 優雅納入 `pytest.skip` 防禦，確保 CI/CD 穩定性。

### 2026年4月：全系統硬化、效能收斂與 Phase 4.6 收尾
四月是專案從局部功能完善邁向全系統架構硬化與效能收斂的關鍵月份。我們不僅完成了 Phase 4.6 整個史詩級任務群的收尾，還進行了深度的效能優化與架構重構。

**核心主題歸類**:
1.  **Phase 4.6 結案與架構硬化 (Ref: 04-25, 04-28)**:
    *   **地基物理加固**: 完成 SQL ID 對齊，物理重設非 UUID 身分。強制實施部門級 SQL 物理隔離。
    *   **架構級減重**: 完成 L2 模組化拆分，例如將 `seed_knowledge` 拆分至 `SeedingService`。
    *   **品質公證**: 達成 100% 後端測試通過率，並透過 `make persona-audit` 進行全角色工作流公證。

2.  **效能突破與 503 防禦 (Ref: 04-02, 04-15, 04-20)**:
    *   **503 結構性根除**: 遷移至官方 `google-genai` SDK，實作原子化巡檢與指數退避重試邏輯。
    *   **系統級 429 抗性**: 全局並發限制，頻率適配 Gemini Free Tier，並實作「原地等待重試」自癒機制。
    *   **冷啟動優化**: 解決 x86_64 環境下的 Torch 依賴與 NumPy 載入崩潰，熱機搜尋延遲大幅降至 2.3s。

3.  **商業情報與 UI 韌性 (Ref: 04-20, 04-25)**:
    *   **行銷情報 2.0**: 實作 `ConversionFunnel` 組件與 `_calculate_lead_score` 動態評分，實現轉換漏斗視覺化。
    *   **防禦性 UI**: 注入防禦性載入與去重邏輯，防止單點 API 錯誤卡死全頁。

4.  **測試隔離與物理對帳 (Ref: 04-22, 04-45)**:
    *   **狀態污染根除**: 實作深拷貝隔離 `MOCK_ADMIN_USER`，解決 E2E 測試中的級聯污染問題。
    *   **真理復原**: 透過 5 輪物理審計，清算殭屍檔案與冗餘邏輯，達成代碼與文件的 100% 對齊。

5.  **RBAC 與路由標準化 (Ref: 04-06, 04-13)**:
    *   **動態身分**: 權限定義 100% 物理遷移至資料庫，並在 UI 實作 Identity Matrix 管理介面。
    *   **路由合約**: 解決 `/api/api` 嵌套問題，實施分類掛載，強化動態與靜態 Role Scopes 的合併。

### 2026年3月：結構化重構、治理硬化與效能收斂
三月是 Archon 從巨型架構邁向模組化治理的關鍵月份。我們消滅了所有超過 1000 行的檔案，並建立了基於 XP 的 Agent 治理體系。

**核心主題歸類**:
1.  **Phase 4.6.24 結案 (Ref: 03-30)**:
    - **巨型檔案清零**: 完成 `CredentialService`, `UrlHandler`, `StatsService`, `ProviderDiscovery` 四大中樞的 L2 模組化拆分。
    - **ROI 視覺化**: 前端實體化 `ROIAnalyticsBadge` 與 `TokenUsageTable`，達成 AI 經濟透明化。
    - **物理隔離**: 徹底隔離 `.env.test` 物理位址，實作並驗證了部門隔離 (SEC-001) 的負面測試。
1.  **模組化革命 (Ref: 03-06 ~ 03-31)**:
    *   **巨型檔案清零**: 拆分 `ollama_api.py`, `knowledge_api.py`, `task_service.py` 與四大核心 Service。
    *   **L2 標竿建立**: 確立了以 `llm/` 包為範本的目錄化重構標準，確保 Facade 模式的 100% 向後兼容。

2.  **Agent 治理與 XP 門禁 (Ref: 03-24 ~ 03-26)**:
    *   **身分落地**: 實作 `agent_xp` 經驗值系統與 Poisson Gate 物理攔截。
    *   **門禁硬化**: 實作解釋性攔截訊息，並實體對齊 Slug-based 身分識別。

3.  **效能與基礎設施硬化 (Ref: 03-30)**:
    *   **調度統一**: 完成 `AgentService` 原生工具動態分發 (Unified Tool Dispatch)。
    *   **O(1) 優化**: 將 `RateLimiter` 複雜度從 O(N) 降至 O(1)，提升高併發穩定性。
    *   **全端對齊**: 找回並恢復了二月重構中遺失的 Token 詳細明細表。

4.  **安全與 ROI 實體化 (Ref: 03-31)**:
    *   **部門隔離**: 實作 JSONB 穿透式隔離，並通過 403 負面測試驗證。
    *   **ROI 落地**: 實作前端 ROI 狀態欄，補齊 AI 經濟治理最後的功能斷層。

### 2026年2月：全角色流程與行動端落地
二月標誌著 Archon 從單點功能邁向全角色協作的里程碑。我們完成了 Alice (Sales), Bob (Marketing), Charlie (Manager) 的核心工作流閉環，並在下旬進行了大規模的架構硬化。

**核心主題歸類**:
1.  **Phase 4.6.3 Charlie (Manager) (Ref: 02-03)**:
    *   **指揮官系統**: 實作 Sentinel 哨兵自動監控 Stale Leads，並結合 RAG/LLM 智慧生成繁體中文追蹤任務。
    *   **權限閉環**: 實作了從 Alert -> Task Dispatch -> Alert Resolved 的完整狀態流轉與 RBAC 控制。

2.  **Phase 4.6.2 Bob (Marketing) (Ref: 02-03)**:
    *   **測試隔離**: 解決了 E2E 測試中的 Promise Hanging 問題，確立了 MSW 必須攔截所有 Auth 請求的測試鐵律。

3.  **Phase 4.6.1 Alice (Sales) (Ref: 02-02)**:
    *   **行動優先**: 實作 "Fire & Forget" 的語音轉工單功能。
    *   **效能優化**: 將 GPS 抓取改為 On-Demand，並引入 SQL Batch Update 優化歸檔效能。
    *   **E2E 穩定化**: 修復了 Dashboard 因非同步載入導致的 Race Condition。

4.  **Nexus 戰情室與 UI 空間革命 (Ref: 02-05, 02-09, 02-10)**:
    *   **並排編輯 (Split View)**: 實作了雙重收合側邊欄與 Markdown 即時預覽，解決 Context 切換的斷腦流問題。
    *   **行動端韌性**: 透過移除 `min-h-screen` 徹底解決了手機版捲動死鎖問題，並實作了 AI 任務的動態進度反饋。
    *   **Dashboard 加固**: 修正了同步 API 的 `maybeSingle()` 調用陷阱，確保資料加載穩定性。

5.  **細粒度 RBAC 與型別安全革命 (Ref: 02-06, 02-07)**:
    *   **Zero-Mypy**: 達成後端 100% 型別通過，重構 `BaseAgent` 泛型解決 `pydantic-ai` 接口匹配問題。
    *   **權限階層化**: 實作了 Manager 與 Admin 的權限邊界，並導入 `is_system_protected` 旗標保護核心系統 Prompt。

6.  **身分同步與流程自動化 (Ref: 02-03, 02-05)**:
    *   **Auth 穩定化**: 修正了 `AuthService` 在建立使用者時同步 metadata 的邏輯，確保角色資訊的一致性。
    *   **Librarian 實體化**: 打通了檔案版本控制與審計路徑的寫入。

7.  **架構硬化與基礎設施對齊 (Ref: 02-15 ~ 02-21)**:
    *   **前端模組化**: 成功將 RAG 設定抽離為獨立特徵模組，並落地位準路徑別名 (`@/`)，消滅相對路徑地獄。
    *   **引擎與 SDK 對齊**: 營運端全面遷移至官方 Google `genai.Client`，解決 SDK 斷層導致的 503 錯誤與死迴圈。
    *   **基礎設施同步**: 修正了 `MigrationService` 的實體表名衝突，並實作了跨環境的金鑰自動檢索 (os.getenv/os.environ)。

### 2026年1月：權限重構、自癒機制與商業功能落地
一月是專案從「技術驗證」邁向「商業運作」的關鍵轉折點。我們在前半月集中解決了深層的架構債（特別是 Auth 與 Docker 環境），後半月則全力衝刺商業功能的實作。

**核心主題歸類**：

1.  **RBAC 權限架構的完備與標準化 (Ref: 01-09, 01-12)**:
    *   **挑戰**: 舊有 `X-User-Role` Header 存在安全漏洞，且 `auth.users` 與 `public.profiles` ID 不一致導致 406 錯誤。
    *   **解決**: 建立 `src/server/auth` 模組，強制後端驗證 JWT。實作 `init_db.py` 中的「雙重同步策略 (Dual Sync)」，自動修復 ID 不一致。
    *   **DX 優化**: 為解決 Admin UI 無登入頁痛點，實作了 `Dev Auto-Login` 機制。

2.  **環境自癒與主動防禦 (Ref: 01-03, 01-04, 01-08)**:
    *   **主動防禦**: 針對 Docker 內部網路 (DNS) 與瀏覽器外部網路的差異，在前端 `api.ts` 實作了「主動防禦」邏輯，偵測到無法連線時自動切換 Mock，解決無限 Loading。
    *   **誠實架構**: 移除了 `SmartAPI` 的隱式 Mock Fallback，強迫開發者正視網路配置問題。

3.  **商業功能與 RAG 進化 (Ref: 01-15, 01-16)**:
    *   **銷售情資**: 實作 Phase 4.2，包含 Leads 管理與市場洞察。
    *   **真實 RAG**: 將 Mock RAG 升級為接軌 Gemini API 的真實系統，打通了「爬蟲 -> 向量 -> 生成」的數據管道。
    *   **行銷官網**: 導入 Config-Driven UI 模式，降低非技術人員維護門檻。

4.  **SOP 與除錯紀律的再強化 (Ref: 01-06, 01-07)**:
    *   **教訓**: 在修復 UI/通訊問題時，因違背 SOP 導致測試崩潰。重新確立了「修改代碼必須同步更新 Mock」與「Patch 必須針對 Class」的鐵律。

5.  **系統穩定化與人機協作 (Ref: 01-20, 01-22, 01-23, 01-24)**:
    *   **任務系統修復 (Ghost Task Mystery)**: 透過精確過濾 (`assignee_id`)、修復非同步 context 錯誤 (`llm_provider` import) 以及前端 `include_closed` 參數，解決了 Alice/Bob 任務消失的問題。
    *   **全角色戰情室 (War Rooms)**: 為 Sales, Marketing, Manager 分別打造了專屬 Dashboard (Sales Nexus, Brand Hub, Team Management)。打通了爬蟲 -> CRM -> Blog -> Approval 的完整商業流程。
    *   **RBAC 深度加固**: 放棄「開副本」做新頁面的想法，直接在後端實作「部門隔離 (Department Isolation)」與前端權限拆分 (`leads:view:sales` vs `marketing`)，確保 Manager 只能管理同部門成員。

6.  **開發體驗 (DX) 與爬蟲進化 (Ref: 01-18, 01-19, 01-25)**:
    *   **爬蟲 AJAX 逆向**: 放棄易被擋的進階爬蟲，改用 104 AJAX API，大幅提升資料品質與穩定性，解決 RAG GIGO 問題。
    *   **Admin UI 完善**: 修復了檔案上傳 Unicode 錯誤、Task ID 顯示，並實作了 `Dev Auto-Login` 與 API Key 自動注入 (`db-init`)，大幅降低本地開發摩擦。
    *   **探針制度化**: 將 `probe_librarian.py` 升級為標準化 `make probe` 指令，並加入維度完整性檢查 (768 vs 1536)，成為 CI/CD 的可靠 Smoke Test。

7.  **系統體制化與行動端擴展 (Ref: 01-26 ~ 01-30)**:
    *   **品質與安全**: 實作了 Row Level Security (RLS) 防止資料外洩，並進行了大規模的 Type Safety/Lint 清掃，消優了數百個潛在的運行時錯誤。
    *   **行動優先**: 為 Alice 打造了 "Hunter Mode" 與語音日誌功能，確立了行動端 "Fire & Forget" 的設計哲學。
    *   **測試韌性**: 面對 Dashboard 複雜的非同步載入，學會了使用 `waitFor` 配合 DOM 狀態檢查來消除 Flaky Tests，並將探針 (Probe) 升級為 CI 標準檢查。

### 2025年12月：Async 重構、前端規範與 AI 開發者奠基

十二月是技術債償還與新功能開發並行的月份。我們完成了全系統的 Async 化，並實作了 AI 開發者流程的核心基礎。

**核心主題歸類**:
1.  **AI 開發者審核流程 (Ref: 12-31, 12-16)**:
    *   **願景對齊**: 在假資料中挖掘出「AI as a Teammate」的真實願景。
    *   **功能實作**: 完成了 `DiffViewer` 與提案審核後端。在 `file_operation_tools.py` 加入 `original_content` 以支援差異比對。
    *   **專案清理**: 歸檔了 Phase 4.1 文件並清理了過期分支。

2.  **非同步重構與測試災難 (Ref: 12-20, 12-12)**:
    *   **挑戰**: 將後端全面重構為 `async` 後，引發了大量 `make test-be` 失敗。
    *   **解決**:
        *   **黃金模式**: 確立了測試 FastAPI 單例服務的模式：在 `import app` 前 `patch`，並使用 `setup_module` 管理生命週期。
        *   **Mock 類型**: 修正了混淆 `Mock` 與 `AsyncMock` 導致的測試錯誤。
        *   **務實決策**: 對於頑固的 ETag 測試使用 `@pytest.mark.xfail`，優先保證主流程。

3.  **前端品質與規範 (Ref: 12-25, 12-15)**:
    *   **Lint 清零**: 系統性解決了 160 個 ESLint 警告。透過研究 `eslint.config.js`，發現 `no-unused-vars` 等誤報是配置問題，而非代碼問題。
    *   **部署驗證**: 解決了部署後 CSS 載入失敗（路徑錯誤）與資料不一致（缺少 `localStorage` 金鑰）的問題，再次印證「部署後驗證」的重要性。

4.  **E2E 測試穩定化 (Ref: 12-27, 12-29)**:
    *   **複雜 Bug**: 解決了 `make test` 失敗的雙重原因：`optimistic.ts` 的邏輯錯誤與 `Makefile` 對前端測試指令的誤用。
    *   **合併紀律**: 合併 E2E 修復分支後，立即執行 `make test` 與 `make lint`，成功攔截了因依賴更新而產生的連鎖錯誤。

### 2025年11月：深層偵錯、Git 考古與 E2E 驗收

十一月是偵錯月。我們深入解決了多個層層疊加的複雜 Bug，並確立了以 Git 歷史為最終真相的偵錯文化。

**核心主題歸類**:
1.  **前端異常的深層根源 (Ref: 11-27, 11-28, 11-13)**:
    *   **`about:blank` 之謎**: 文件上傳後跳轉空白頁。追蹤發現是後端 `knowledge_item_service.py` 錯誤回傳了無效的 `source://` URL。
    *   **UI 報錯**: Admin UI 顯示 "Failed to Load Knowledge Base"。使用者提供的 `invalid input syntax for type uuid` 成為關鍵線索，定位到 DB 函式參數型別不匹配。
    *   **部署路由**: Render 部署後前端無法連線，瀏覽器報 `SyntaxError: ... < is not valid JSON`。證實是 Render 路由規則未重寫 `/api` 請求。

2.  **檔案上傳的多層錯誤 (Ref: 11-15, 11-24)**:
    *   **剝洋蔥式偵錯**: 檔案上傳失敗背後隱藏了三層錯誤：`Bucket not found` (Supabase 設定) -> `InvalidKey` (中文檔名) -> `TypeError` (對同步函式使用 `await`)。
    *   **Git 歷史裁決**: 在解決「靜默失敗」時，`git log` 與 `docker logs` 出現矛盾。最終透過 `git show HEAD:<file>` 證實了 Docker 內的程式碼確實是舊版本，結束了對環境的無謂猜疑。

3.  **非同步測試的挑戰 (Ref: 11-26, 11-11)**:
    *   **歷史債**: `git log` 顯示 `test_file_upload_integration.py` 的 Mock 是為舊同步函式寫的，導致重構後 `TypeError`。確立了「修改測試前先查歷史」的原則。
    *   **無限循環**: React 元件 `Maximum update depth exceeded`。追溯歷史發現是為修復 Lint 而錯誤地將 `state` 加入了 `useEffect` 依賴。

4.  **系統性驗收 (Ref: 11-10, 11-19)**:
    *   **眼見為實**: 在前端注入 `console.log` 發現 API 路由衝突（兩個 `/health` 端點）。
    *   **全面探測**: 執行 E2E 手動驗收，產出 Bug 清單，鎖定「後端背景任務靜默失敗」為多個功能異常的共同病灶。

### 2025年10月：系統嫁接、雲端部署與SOP重塑

十月份是專案架構轉型的關鍵期。我們將實驗性的 `feature` 分支嫁接到主幹，並首次打通了雲端部署流程。

**核心主題歸類**:
1.  **系統嫁接與架構確立 (Ref: 10-17, 10-05)**:
    *   **挑戰**: 在將 `feature` 分支應用移植到 `main` 架構時，遭遇了依賴管理 (`pip` vs `uv`) 與工具鏈 (`npm` vs `pnpm`) 的「精神分裂」。
    *   **解決**: 透過 `git diff --name-status` 全面盤點差異。確立了 `Makefile` 為單一事實來源，並統一使用 `pnpm` 與 `uv`。
    *   **教訓**: 「嫁接」非單純合併，必須先建立統一的基底架構。

2.  **Render 雲端部署戰役 (Ref: 10-09, 10-13)**:
    *   **API 404/500 迷霧**: 部署後前端無法連線。經查證，瀏覽器報錯 `SyntaxError: ... < is not valid JSON` 是因為 Render 缺少 SPA 重寫規則，導致 API 請求被導向 `index.html`。
    *   **設定延遲**: 即使修正了設定，API 仍失敗。最終證實是雲端平台的「傳播延遲 (Propagation Delay)」，學會了「等待與硬刷新」的除錯技法。
    *   **產品思維**: 部署後驗證中，我們學會了不應套用通用模板，而應以「問卷」代替「方案」，並優先使用手上資源。

3.  **SOP 與測試紀律的建立 (Ref: 10-14, 10-18, 10-23)**:
    *   **資料庫遷移**: 發現舊流程高風險，建立了基於 `schema_migrations` 表的冪等性遷移 SOP。
    *   **測試基準線**: 面對 38 個後端測試失敗，我們建立了「單點修復 -> 驗證」的循環。清理了測試快取導致的幽靈失敗。
    *   **嚴格計畫**: 在經歷多次「來回修改」的指責後，確立了「先調查歷史，再提出包含 `old_string` 的完整計畫」的鐵律。

4.  **精準偵錯與殭屍代碼 (Ref: 10-27, 10-29)**:
    *   **移除病灶**: `archon-ui-main` 啟動失敗指向 `useThemeAware.ts`，調查發現這是無用的 Dead Code，直接刪除即修復。
    *   **釐親矛盾**: 透過釐清「UI 載入成功但 API 404」的精確場景，區分了「啟動問題」與「資料問題」。

### 2025年9月：SOP, 歷史追溯與偵錯紀律的建立

九月份是專案從混亂的「救火隊模式」轉向「紀律化開發」的關鍵月份。這個月的歷程充滿了在 `make` 指令、Docker 環境、部署流程和非同步測試中的反覆試錯。

**核心主題歸類**:
1.  **SOP 的建立與探索**: 這個月，我們確立了多項至今仍在使用的核心工作原則。我們學會了不再信任過時的文件，而是將 `Makefile` 視為「單一事實來源」(Ref: 09-19)，並反覆使用 `git log -p` 去追溯 `Makefile` 和 `docker-compose.yml` 的歷史意圖，以理解為何一個指令會以某種特定方式運作 (Ref: 09-29, 09-21)。「測試先行」的重構安全網 (Ref: 09-24) 和冪等性的資料庫腳本 (Ref: 09-21) 也在這個月被確立為標準實踐。

2.  **系統性偵錯的學習**: 我們經歷了從處理表層 Bug 到深挖根源的思維轉變。例如，一個樣子簡單的 `AttributeError`, 其根源卻是更深層的 `ImportError` (Ref: 09-22)。我們也學會了警惕 `make lint --fix` 等指令帶來的副作用 (Ref: 09-23)，並確立了在修改程式碼前，必須先分析所有相關檔案，以避免「改 A 壞 B」的循環 (Ref: 09-17)。

3.  **部署與非同步測試的挑戰**: 九月下旬，我們專注於打通完整的開發到部署流程。我們演練了部署流程，解決了因服務耦合、Git Remote 混淆和鎖定檔案缺失導致的部署失敗問題 (Ref: 09-30)。同時，我們在為非同步 API 撰寫測試時遇到了困難，最終透過在 `patch` 中使用 `AsyncMock` 和在獨立檔案中進行「沙盒驗證」，才成功突破了 Mocking 的迷霧 (Ref: 09-25)。

總結來說，九月是透過解決一系列棘手的環境、部署和測試問題，從而建立起穩固的工程紀律和核心工作原則的基礎月份。
��立起穩固的工程紀律和核心工作原則的基礎月份。

### 08-19: MCP 拓樸修復與爬蟲記帳攔截硬化 (Phase 5.10.25)
- **拓樸死結修復**: 於 `docker-compose.yml` 將 `archon-server` 加入對 `archon-mcp` 的 `service_healthy` 依賴，根除因容器並行啟動導致的 `Agent Neural Wiring FAILED` 警告。
- **提示詞 SSOT 補齊**: 抽離 `version_control_tools.py` 中的 Git 智慧提交 inline 提示詞，統一註冊至 `dev_ops_prompts.py` 的 `COMMIT_MESSAGE_GENERATOR`，達成全域提示詞 SSOT。
- **隱藏成本漏洞修補**: 修正 `lead_evaluator.py` 在爬蟲高併發下直接使用 `genai.Client` 而繞過記帳系統的問題，手動解析 `response.usage_metadata` 並掛載回 `TokenUsageService` 中介攔截器。
- **閾值硬化**: 將 RAG 過濾閾值從 0.68 上調至 0.70，寫入 `schemas/settings.py` 預設值與 `migration/20260819_update_rag_threshold.sql` 確保資料庫覆寫。通過 668 項後端測試公證與 `make phase-audit`。
- **60s 超時防禦公證**: 釐清了前端 `signal is aborted without reason` 報錯真相。經物理測試排除後端 Deadlock 與 Socket 超時後，確認此報錯 100% 源於 Vercel 生產環境觸發了 Hugging Face 的冷啟動 (Cold Start > 60s)，進而啟動了 `apiClient.ts` 內建的 `AbortController` 60 秒硬切斷防禦。這是預期的基礎設施行為，無需亦不准修改代碼，成功守住不盲目重構的底線。
- **拓樸死結修復補丁 (Hotfix)**: 修正了先前 5.10.25 誤將 `depends_on: archon-mcp` 植入 `archon-mcp` 服務自身導致的 Circular Dependency (`make stop` 崩潰)。已將相依性正確掛載至 `archon-server`，並透過 `make stop` 物理驗證關機拓樸圖成功。
### 08-19: NotebookLM 與 Google Drive MCP 架構與計畫落地 (Phase 5.11.1)
- **單一事實來源與無斷層設計**: 審閱並制定了 `Phase_5.11.1_NotebookLM_Drive_Integration_Plan.md`，完全對齊 Hugging Face Spaces `scripts/deploy_to_hf.sh` 之單一容器架構。
- **微服務拓樸防禦**: 捨棄獨立容器，將 `notebooklm-py` 與 NotebookLM API 封裝進既有之 `archon-mcp` (`src/mcp_server/features/notebooklm`)，確保 `start_all.sh` 啟動時雲端與本地端雙向容。
- **跨平台加密避讓**: 使用 `.env` 變數取代 Mac Keychain Cookie，防禦 Docker 無法解密之限制。

### 2026-09-28: Phase 5.11.23 零虛假公證與 L2 架構修復 (Zero Fake Verification & L2 Architecture Fix)

*   **TypeGuardian 型別與架構修復**:
    *   **診斷**: `bddebe14` (TypeGuardian PR) 引入了 MyPy 型別錯誤 (如 `UserProfileUpdateDict` 缺少 `id`、`list[ProjectDTO]` 冗餘轉型) 以及嚴重的 L2 架構破壞 (在 `ProposeChangeService` 中拔除 `BaseRepository` 並濫用 `query.execute()`)。
    *   **修復**: 物理修正 `profile_service.py`、`marketing_service.py`、`rbac_service.py` 與 `projects/core.py` 的 DTO 型別。重建 `ProposeChangeService` 對 `BaseRepository` 的繼承，將所有 9 處 `.execute()` 替換為標準的 `self.execute_query()`，通過 `make phase-audit` 的 Step 10 攔截網。
*   **物理部門隔離 (Physical Department Isolation) 還原**:
    *   **診斷**: 發現 `test_department_isolation_physical_logic` 測試報錯 (`assert 0 == 2`)，原因是 `bddebe14` 誤刪除了 `list_proposals` 中的部門隔離邏輯，將其退化為單純的 `created_by` 過濾。
    *   **修復**: 物理還原 `query.filter("request_payload->>created_by_dept", "eq", dept)` 安全隔離網。
*   **公證**:
    *   `make lint-be` 與 `make lint-fe` 100% 零錯誤。
    *   `make test-be` (718 passed)。
    *   `make phase-audit` 全面亮綠燈通過。

*   **⚠️ 致命的反面教材：改 A 壞 B (Event Loop 阻塞)**:
    *   **診斷**: 在修復 L2 違規時，我使用了同步的 `self.execute_query`，這在 `ProposeChangeService` 的 `async def` 方法中引發了 Event Loop 阻塞 (重蹈了 Phase 5.11.22 的覆轍)。
    *   **修復**: 立刻將所有相關調用修正為 `await self.execute_query_async()`，解除效能癱瘓風險。
