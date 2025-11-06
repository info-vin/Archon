# 專案食譜 (Project Cookbook)

> 歡迎來到 Archon 廚房！本食譜記載了我們團隊合作的最佳實踐與標準作業流程 (SOP)。
> 
> 本文件旨在提供清晰、可執行的指南。所有關於「為什麼」的歷史決策與背景故事，都已被整理至 **附錄 A**，以保持本食譜的簡潔與易用性。

---

## 第一章：核心心法 (Core Mindset)

| 原則 | 解釋 |
| :--- | :--- |
| 1. **警惕「副本任務」陷阱** | 分析是為了解決「主線任務」，而不是為了開啟無止盡的調查循環。在得到分析結果後，應回頭思考如何將此結果應用於完成最初的目標。 |
| 2. **驗證而非假設** | 不要「幻想」一個可運行的環境或完美的程式碼狀態。永遠要透過指令或工具進行驗證，並在最後進行「眼見為實」的視覺化驗收。 |
| 3. **精準修改，避免副作用** | 修復 Bug 或修改程式碼時，應採取最小、最精準的修改。使用 `replace` 時務必提供足夠的上下文，以避免「改 A 壞 B」。 |
| 4. **徹底理解工具** | 永遠不要假設一個指令的行為。在使用 `make` 或其他腳本前，先閱讀其源碼，理解其是否包含 `--fix` 等有副作用的參數。 |
| 5. **撰寫冪等的資料庫腳本** | 所有資料庫遷移腳本都應具備「冪等性」，確保其可以安全地重複執行。應大量使用 `DROP ... IF EXISTS` 和 `CREATE ... IF NOT EXISTS`。 |
| 6. **`Makefile` 是唯一指令來源** | 文件應引用 `make <command>`，而不是直接複製貼上底層 shell 指令，以確保文件與腳本永遠同步。 |
| 7. **安全地修改與復原** | 複雜修改應使用 `write_file` 一次性覆寫。當修改後測試失敗，應立即用 `git checkout -- <file>` 還原，而不是在錯誤的基礎上繼續修補。 |

---

## 第二章：環境設定 (Environment Setup)

### 2.1 本地開發環境啟動 SOP (混合模式)

**目標**: 在本地成功啟動一個用於日常開發的混合模式環境。

**核心架構**:
- **後端 (Backend)**: 在 Docker 中運行 (`archon-server`, `archon-mcp`, `archon-agents`)。
- **前端 (Frontend)**: 在**本機**手動運行，以利用熱加載功能。
    - `archon-ui-main` (管理後台) -> Port `3737`
    - `enduser-ui-fe` (使用者介面) -> Port `5173`

**執行步驟**:

1.  **清理環境 (若有需要)**:
    ```bash
    make stop
    ```

2.  **啟動後端服務 (終端機 1)**:
    ```bash
    make dev
    ```
    *(此指令只會啟動 Docker 中的後端服務)*

3.  **啟動管理後台 (終端機 2)**:
    ```bash
    # 首次執行或依賴變更時，需先安裝依賴
    make install-ui
    # 啟動開發伺服器
    cd archon-ui-main && pnpm run dev
    ```

4.  **啟動使用者介面 (終端機 3)**:
    ```bash
    # 首次執行或依賴變更時，需先安裝依賴
    make install
    # 啟動開發伺服器
    cd enduser-ui-fe && pnpm run dev
    ```

**最終驗證**:
當所有服務都成功啟動後，您可以在瀏覽器中分別打開 `http://localhost:3737` (管理後台) 和 `http://localhost:5173` (使用者介面)。

### 2.2 後端依賴與環境管理

- **`uv.lock` 管理**: `python/uv.lock` **必須**被加入到 `.gitignore`。每位開發者應在本地生成，不應提交共享。
- **依賴組安裝**: `Makefile` 中的 `make test-be` 和 `make lint-be` 會自動使用 `--group` 參數安裝 `test` 和 `dev` 的依賴，無需手動操作。

### 2.3 全 Docker 環境手動驗證 SOP

**原因**：此流程旨在提供一個最徹底、最乾淨的本地驗證方法，模擬生產環境，適用於偵錯複雜的啟動問題或驗證重大變更。它能完全排除舊容器、資料卷或建置快取的干擾，確保測試的準確性。

**詳細步驟**：

1.  **徹底清理 (Clean Slate)**：
    *   **指令**：`make clean`
    *   **說明**：此指令會徹底移除所有容器、網路和**資料卷**。執行時會出現 `(y/N)` 確認提示，請務必輸入 `y`。這是確保完全乾淨狀態的關鍵。

2.  **驗證清理 (Verify Cleanup)**：
    *   **指令**：`docker ps -a`
    *   **說明**：執行此指令後，應看不到任何與本專案相關的容器，列表應為空。

3.  **重新建置 (Rebuild)**：
    *   **指令**：`docker compose --profile backend --profile frontend --profile enduser --profile agents build`
    *   **說明**：此指令會根據最新的程式碼，為所有服務建立全新的 Docker 映像檔。

4.  **前景啟動與觀察 (Foreground & Observe)**：
    *   **指令**：`docker compose --profile backend --profile frontend --profile enduser --profile agents up`
    *   **說明**：在前景啟動所有服務 (注意**沒有** `-d` 旗標)。所有服務的日誌將會即時輸出到目前的終端機，讓您可以直接觀察啟動順序和任何潛在的錯誤訊息。

---

## 第三章：測試指南 (Testing Guide)

### 3.1 通用測試指令

| 目的 | 指令 | 範例 |
| :--- | :--- | :--- |
| **執行所有測試** | `make test` | `make test` |
| **僅執行後端測試** | `make test-be` | `make test-be` |
| **測試特定前端專案** | `make test-fe-project project=<name>` | `make test-fe-project project=enduser-ui-fe` |
| **測試特定前端檔案** | `make test-fe-single project=<name> test=<pattern>` | `make test-fe-single project=enduser-ui-fe test="TaskModal"` |

### 3.2 後端 API 測試：模擬資料庫

所有後端 API 測試都**嚴格禁止**連線到真實的資料庫。專案在 `python/tests/conftest.py` 中使用 `pytest fixture` 和 `patch` 自動模擬了 `SupabaseClient`。您只需在測試函式簽名中加入 `client` 和 `mock_supabase_client` 即可使用。

### 3.3 前端測試常見問題 (FAQ)

| 問題 | 原因 | 解決方案 |
| :--- | :--- | :--- |
| **`Failed to resolve import`** | `package.json` 中缺少開發依賴。 | 在該專案目錄下執行 `pnpm install --save-dev <package-name>`。 |
| **找不到純圖示按鈕** | 按鈕缺少無障礙文字描述。 | 為按鈕加上 `aria-label="描述"` 屬性。 |
| **`required` 表單提交測試** | `userEvent.click` 會被瀏覽器預設行為攔截。 | 使用 `fireEvent.submit(submitButton)` 直接觸發提交事件。 |
| **`vi.mock` 變數提升錯誤** | `vi.mock` 的工廠函式使用了在頂層宣告的變數。 | 將 `vi.mock` 需要的變數直接定義在工廠函式**內部**。 |

---

## 第四章：貢獻與部署流程 (Contribution & Deployment)

### 4.1 Git 工作流程

- **分支策略**: 所有工作都**必須**在 `feature/...` 分支上進行。部署也**必須**從 `feature/...` 分支進行。`main` 分支請勿使用。
- **`cherry-pick` 卡住**: 若 `git cherry-pick --continue` 卡住，請改用 `git cherry-pick --continue --no-edit --no-gpg-sign`。

### 4.2 部署標準作業流程 (SOP)

此流程的最終目標，是成功將一個穩定的 `feature/...` 分支部署到 **Render**。

1.  **階段一：部署前本地檢查**
    此步驟提供兩種流程選項：
    *   **流程一 (快速檢查)**: 至少執行 `make test` 與 `make lint`。
    *   **流程二 (完整驗證)**: 執行「[2.3 全 Docker 環境手動驗證 SOP](#23-全-docker-環境手動驗證-sop)」，以進行最徹底的檢查。

2.  **階段二：資料庫遷移 (Database Migration) - v2 (Tracked)**

    此流程的最終目標是安全、可追蹤地更新資料庫結構。

    **核心原則**:
    *   **冪等性**: 所有遷移腳本都必須是冪等的 (`IF NOT EXISTS`)。
    *   **版本註冊**: 每個腳本都必須在執行成功後，將自己的版本號註冊到 `schema_migrations` 表中。

    **開發新遷移腳本的流程**:
    1.  **建立檔案**: 建立一個新的 SQL 檔案，並使用下一個可用的數字作為前綴 (例如 `003_add_new_feature.sql`)。
    2.  **撰寫冪等 SQL**: 使用 `ALTER TABLE ... ADD COLUMN IF NOT EXISTS ...` 或 `CREATE TABLE IF NOT EXISTS ...` 等語法。
    3.  **註冊版本**: 在腳本的結尾，加上註冊指令：
        ```sql
        -- 註冊此遷移腳本的版本
        INSERT INTO schema_migrations (version) VALUES ('003_add_new_feature') ON CONFLICT (version) DO NOTHING;
        ```
        *(請將 `'003_add_new_feature'` 替換為不含 `.sql` 副檔名的檔名)*

    **執行遷移的SOP (部署時)**:
    1.  登入 Supabase 儀表板並進入 **SQL Editor**。
    2.  **首次設定**: 若 `schema_migrations` 表不存在，請先執行 `migration/002_create_schema_migrations_table.sql` 以建立遷移紀錄表。
    3.  **依序執行**: 依序手動執行所有本次部署涉及的**新**遷移腳本。由於冪等性與版本註冊，重複執行舊腳本是安全的，但為了清晰起見，建議只執行新的。

        **本地開發首次設定SOP (從零開始)**:

    

        > **⚠️ 注意：此為手動流程**

        >

        > 本地首次設定資料庫需要**手動**在 Supabase SQL Editor 中依序執行以下 6 個腳本。專案目前**沒有**提供 `make db-reset` 等快捷指令。

    

        當您需要在本地建立一個全新的、乾淨的資料庫時，請遵循此流程。**此流程會刪除所有資料**。
    1.  登入 Supabase 儀表板並進入 **SQL Editor**。
    2.  將下列腳本的內容，**依序**複製貼上並執行：
        1.  `migration/RESET_DB.sql` (清空所有舊資料)
        2.  `migration/000_unified_schema.sql` (建立基礎結構)
        3.  `migration/001_add_due_date_to_tasks.sql` (追加欄位更新)
        4.  `migration/002_create_schema_migrations_table.sql` (建立版本追蹤表)
        5.  `migration/seed_mock_data.sql` (填充核心假資料)
        6.  `migration/seed_blog_posts.sql` (填充部落格假資料)

3.  **階段三：執行部署**
    1.  確認 Render 儀表板監控的是正確的 `feature/...` 分支。
    2.  將本地變更推送到 GitHub: `git push origin <your-branch>`
    3.  Render 會自動偵測到新的提交並開始部署。

4.  **階段四：部署後驗證**
    1.  在 Render 儀表板監控所有服務的部署日誌。
    2.  存取後端服務的 `/health` 端點，確認回傳 `{"status":"ok"}`。
    3.  打開前端服務的公開網址，進行功能驗證 (Smoke Test)。

---

## 附錄 A：重要架構決策與歷史紀錄

本附錄記載了專案開發過程中的關鍵決策背景與歷史教訓，以時間順序排列。

### 2025-10-07: 首次部署的歷史調查

- **情境**: 為了釐清首次部署時，為何 `enduser-ui-fe` 成功，而 `archon-ui-main` 失敗。
- **調查結論**: 兩個獨立事件同時發生：
    1.  **成功的 `enduser-ui-fe`**: 當時的部署目標只有 `enduser-ui-fe`。雖然遇到了 `pnpm-lock.yaml` 缺失的問題（並透過 `--no-frozen-lockfile` 臨時繞過），但最終成功部署並設定了正確的 API URL。
    2.  **失敗的 `archon-ui-main`**: `archon-ui-main` 的程式碼當時寫死了一個已被後端重構移除的 API 端點 (`/api/projects/health`)，導致其本地和線上都無法連線，這與部署流程本身無關。
- **確立原則**: 此調查確立了在除錯時，必須區分「部署流程問題」與「應用程式自身 Bug」的重要性。

### 2025-09-30: Render 部署流程確立

- **情境**: 在部署演練中，`git push render` 指令失敗，回報 `repository not found`。
- **決策理由**: 經查證，Render 提供的 URL 是一個「Deploy Hook」，只能被 `curl` 等工具觸發，而不能作為 Git remote。因此，專案的部署流程**不應**使用 `git push render`。
- **確立原則**: 確立了正確的部署流程：將程式碼 `push` 到 Render 所監控的 `origin` (GitHub) 分支，依靠 Render 的 GitHub App 自動觸發部署。

### 2025-09-29: `Makefile` 意圖的最終仲裁

- **情境**: `make test` 指令緩慢且包含所有前後端測試，與 `ci.yml` 中僅測試後端的行為產生矛盾。
- **決策理由**: 直接修改 `Makefile` 是危險的。透過 `git log -p -- Makefile` 深入分析提交歷史，發現開發者曾短暫嘗試過快慢測試分離，但很快就手動還原了該修改。這證明了 `make test` 的「緩慢但完整」是**刻意為之**的選擇。
- **確立原則**: 當文件、程式碼、CI/CD 腳本之間出現矛盾時，`git log -p` 是揭示真實意圖的最終仲裁者。

### 2025-09-27: 測試背景任務的 API

- **情境**: 為 `/documents/upload` 這個啟動背景任務的端點編寫單元測試時，不知如何斷言。
- **決策理由**: 單元測試應專注於被測單元的「職責」，而非其「依賴的實作細節」。此端點的職責是「接收請求並正確啟動任務」，而不是「完成任務」。
- **確立原則**: 確立了測試此類端點的最佳實踐：模擬 (Mock) `asyncio.create_task` 本身，並驗證它是否被以正確的參數呼叫。測試中出現的 `RuntimeWarning: coroutine ... was never awaited` 是此策略下預期內且無害的副作用。

### 2025-09-23: 「自動修復」的陷阱

- **情境**: 執行 `make lint-be` 驗證程式碼，卻導致大量不相關的檔案被自動修改，汙染了工作區。
- **決策理由**: 閱讀 `Makefile` 後發現，`lint-be` 指令包含了 `--fix` 參數，使其從一個「檢查工具」變成了「修改工具」。
- **確立原則**: 確立了處理此類工具的安全工作流程：「先用唯讀模式 (`ruff check`) 分析 -> 將所有修改一次性用 `write_file` 寫入 -> 最後再用原指令 (`make lint-be`) 進行純粹的驗證」。

### 2025-09-22: `Makefile` 與 `pyproject.toml` 的矛盾

- **情境**: `make test-be` 失敗，因為 `Makefile` 中的 `uv sync --extra` 指令與 `pyproject.toml` 的 `[dependency-groups]` 結構不符。
- **決策理由**: 透過 `git log -p -- Makefile` 追溯歷史，發現專案曾刻意選擇 `[dependency-groups]` 結構，從而確認了 `Makefile` 需要被修正以使用 `--group` 參數，而不是反過來修改 `pyproject.toml`。
- **確立原則**: 再次印證了「追溯 `git log` 以理解歷史意圖」的重要性。

### 2025-09-21: 資料庫腳本的冪等性

- **情境**: 執行資料庫遷移腳本 `000_unified_schema.sql` 時，因 `policy ... already exists` 錯誤而中斷。
- **決策理由**: 遷移腳本的穩定性與可重複執行性，比微不足道的效能更重要。
- **確立原則**: 所有資料庫遷移腳本都必須具備「冪等性」。對於不支援 `CREATE ... IF NOT EXISTS` 的物件（如 `POLICY`），在 `CREATE` 之前必須先使用 `DROP ... IF EXISTS`。

### 2025-09-19: `Makefile` 作為單一事實來源

- **情境**: 專案中的 `README.md` 記載了與 `Makefile` 不一致的啟動指令，導致開發者遵循文件操作時發生錯誤。
- **決策理由**: 可執行的腳本是指令的最終真理，文件應作為其說明而存在。
- **確立原則**: 確立了 `Makefile` 作為所有專案指令的「單一事實來源」。所有 `.md` 文件在指導操作時，都應引用 `make <command>`，而不是複製貼上其底層指令。

---

## 附錄 B：系統分析與比較 (System Analysis & Comparison)

### `make dev` vs `make dev-docker` 比較分析

這份表格是基於對 `Makefile` 內容的直接分析得出的「單一事實」。

| 特性 | `make dev` (混合開發) | `make dev-docker` (全 Docker 開發) | 差異原因分析 |
| :--- | :--- | :--- | :--- |
| **啟動模式** | 混合模式 | 全 Docker 模式 | `dev` 模式旨在為前端開發提供最佳體驗，因此只在 Docker 中運行後端，而在本地直接運行前端以利用熱重載(Hot Reload)功能。`dev-docker` 則模擬一個更接近生產的環境，所有服務都在 Docker 容器中運行。 |
| **Docker Profiles** | `--profile backend --profile agents` | `--profile backend --profile frontend --profile enduser --profile agents` | `dev` 模式只啟動後端相關的 `backend` 和 `agents` profiles。`dev-docker` 額外啟動了 `frontend` (archon-ui-main) 和 `enduser` (enduser-ui-fe) 兩個前端 profile，將它們也容器化。 |
| **前端服務** | 在本地主機上通過 `pnpm run dev` 啟動 `archon-ui-main`。 | `archon-ui-main` 和 `enduser-ui-fe` 都在 Docker 容器內運行。 | `dev` 模式讓前端開發者可以直接在本地編輯器中修改程式碼，並立即在瀏覽器中看到結果，無需重新建置 Docker 映像。`dev-docker` 則將前端作為獨立的容器化服務來管理。 |
| **`enduser-ui-fe`** | **不啟動** | 在 Docker 容器內啟動 | `dev` 模式的設計目標是專注於 `archon-ui-main` (管理後台) 的開發，因此沒有包含 `enduser-ui-fe`。而 `dev-docker` 則會啟動包括 `enduser-ui-fe` 在內的所有服務。 |
| **主要用途** | 專注於**管理後台 (`archon-ui-main`)** 的前端開發，同時需要後端 API 支持。 | 進行**全系統整合測試**，或當開發者不需要頻繁修改前端程式碼，只想啟動一個完整的、隔離的本地環境時使用。 | 兩種模式為不同的開發場景提供了優化。`dev` 專注於效率，`dev-docker` 專注於環境一致性。 |

### SQL 資料庫結構 vs. 工作時序圖 差異分析

此分析基於對 `migration/000_unified_schema.sql`、`CONTRIBUTING_tw.md` 和 `TODO.md` 的交叉比對。

**1. 資料庫實體盤點**

*   **`000_unified_schema.sql` 中定義的表格 (共 14 個)**:
    *   **核心任務管理**: `archon_projects`, `archon_tasks`
    *   **知識庫 (RAG)**: `archon_sources`, `archon_crawled_pages`, `archon_code_examples`
    *   **系統設定**: `archon_settings`, `archon_prompts`
    *   **使用者與內容**: `profiles`, `blog_posts`
    *   **版本與紀錄**: `archon_project_sources`, `archon_document_versions`, `gemini_logs`
    *   **其他業務**: `customers`, `vendors`
*   **`TODO.md` 時序圖中隱含的實體**:
    *   `tasks` (在步驟 3 和 10 中被更新)
    *   `Storage` (在步驟 8 中被寫入)

**2. 差異比較表**

| 項目 | `000_unified_schema.sql` 中定義的表格 | `TODO.md` 時序圖中隱含的實體 | 差異分析 |
| :--- | :--- | :--- | :--- |
| **核心任務管理** | `archon_projects`, `archon_tasks` | `tasks` | **一致**。時序圖的核心是更新任務 (`tasks`)，這與 `archon_tasks` 表格直接對應。`archon_projects` 作為其父級，也是一致的。 |
| **知識庫** | `archon_sources`, `archon_crawled_pages`, `archon_code_examples` | *未提及* | **存在差異**。時序圖聚焦於「任務執行與檔案上傳」，並未描繪 Agent 執行任務時與知識庫（RAG）的互動細節。因此，與知識庫相關的表格沒有在圖中出現是合理的，這代表時序圖的抽象層級較高。 |
| **系統設定** | `archon_settings`, `archon_prompts` | *未提及* | **存在差異**。時序圖並未包含系統讀取設定或 Prompt 的步驟，因此這些表格沒有出現。 |
| **使用者與內容** | `profiles`, `blog_posts` | *未提及* | **存在差異**。`profiles` 和 `blog_posts` 主要由 `enduser-ui-fe` 使用，而時序圖主要描繪的是 `archon-ui-main` 的核心任務流程，因此未被提及。 |
| **版本與紀錄** | `archon_document_versions`, `gemini_logs`, `archon_project_sources` | *未提及* | **存在差異**。這些屬於系統內部紀錄與版本控制的表格，在高級別的用戶工作流程圖中通常會被省略。 |
| **其他業務** | `customers`, `vendors` | *未提及* | **存在差異**。這些是後來在 `feature` 分支中添加的實驗性表格，與當前的核心工作時序圖無關。 |
| **檔案儲存** | *不適用 (由 Storage 管理)* | `Storage` | **一致**。時序圖明確區分了 `DB` 和 `Storage`。步驟 8 `將檔案上傳至 Storage` 描述的是檔案儲存，而非資料庫表格操作，這與 SQL 結構中沒有專門儲存檔案實體的設計是一致的。 |

**3. 結論**

資料庫的實際結構遠比時序圖複雜。這是一個**正常且健康的現象**。時序圖的目的是為了**溝通核心業務流程**，因此它會省略大量背景、設定和非核心功能的細節。主要的「差異」在於：

*   **時序圖的抽象層級較高**：它只展示了與「建立任務 -> Agent 執行 -> 交付結果」這一條主線最直接相關的資料庫互動（即更新 `archon_tasks` 表）。
*   **資料庫結構更完整**：它包含了支持所有系統功能所需的全部表格，包括時序圖中未展示的 RAG、系統設定、使用者資料等。
