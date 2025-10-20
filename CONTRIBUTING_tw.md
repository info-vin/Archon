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

### 2.1 本地開發環境啟動 SOP

**目標**: 在本地成功啟動一個完整、可用於端對端手動測試的開發環境。

**核心架構**:
本地開發環境由三個獨立運行的部分組成：
- **核心後端 (Core Backend)**: `archon-server`, `archon-mcp` (Docker, Port `8181`/`8051`)
- **管理後台 (Admin UI)**: `archon-ui-main` (本地 Vite, Port `3737`)
- **使用者介面 (End-User UI)**: `enduser-ui-fe` (本地 Vite, Port `5173`)

**執行步驟**:
1.  **清理環境**: `make stop`
2.  **安裝所有依賴**: `make install && make install-ui`
3.  **啟動核心服務 (終端機 1)**: `make dev`
4.  **啟動使用者介面 (終端機 2)**: `cd enduser-ui-fe && pnpm run dev`

**最終驗證**: 當所有服務都成功啟動後，請在瀏覽器中打開使用者介面 `http://localhost:5173`，並根據 `TODO.md` 的指示，完成一次完整的端對端測試流程。

### 2.2 後端依賴與環境管理

- **`uv.lock` 管理**: `python/uv.lock` **必須**被加入到 `.gitignore`。每位開發者應在本地生成，不應提交共享。
- **依賴組安裝**: `Makefile` 中的 `make test-be` 和 `make lint-be` 會自動使用 `--group` 參數安裝 `test` 和 `dev` 的依賴，無需手動操作。

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
    1.  同步最新程式碼: `git checkout <your-branch> && git pull`
    2.  執行完整測試: `make test`
    3.  執行 Lint 檢查: `make lint-be`

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
