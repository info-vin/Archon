# 專案食譜 (Project Cookbook)

> 歡迎來到 Archon 廚房！本食譜記載了我們團隊合作的最佳實踐與標準作業流程。
>
> **與 `GEMINI.md` (廚師日誌) 的關係:**
> 本食譜中的許多原則，都附有「👨‍🍳 **主廚筆記**」連結。當您想了解某個流程或原則背後的詳細研發故事時，可以點擊該連結，跳轉至 `GEMINI.md` 中對應的真實案例，以獲得最完整的上下文。

---

## 第一章：核心心法 (Core Mindset)

這是在專案開發過程中，透過不斷試錯總結出的寶貴經驗。請在開始任何任務前，先閱讀並理解這些原則。

### 1.1 警惕「副本任務」陷阱
- **情境**: 在分析出一個問題後，容易為了解決這個問題而開啟一個新的、孤立的調查或研究任務。
- **心法**: **分析是為了解決「主線任務」，而不是為了開啟「副本任務」**。在得到分析結果後，應回頭思考如何將此結果應用於完成最初的、最大的目標，而不是陷入無止盡的調查循環。

### 1.2 驗證而非假設
- **原則**: 不要「幻想」一個可運行的環境或一個完美的程式碼狀態。永遠要透過指令或工具進行驗證。
- **案例 A：關於 `cherry-pick` 和 UI**：程式碼移植成功（`git cherry-pick`）不代表視覺整合成功。對於 UI 變更，在所有測試的最後，必須進行「眼見為實」的視覺化驗收，不能僅信賴自動化測試，因為樣式和佈局問題是自動化測試的盲區。
- **案例 B：關於端對端測試**：在制定端對端測試計畫前，必須先驗證所有前置條件都已滿足。應主動查閱專案文件（如 `GEMINI.md`）中已記錄的風險（例如，資料庫遷移衝突），並優先解決這些「阻塞性問題」，而不是規劃一個無法執行的「幻想計畫」。
- **案例 C：關於建置腳本**：當 `make test-be` 失敗且 `Makefile` 中的指令 (`uv sync --extra`) 與 `pyproject.toml` 的結構 (`[dependency-groups]`) 產生矛盾時，不能輕率地認定 `Makefile` 就是錯的。必須使用 `git log -p -- Makefile` 來追溯該指令的引入歷史，理解其作者的意圖。在本次除錯中，正是 `git log` 揭示了專案曾刻意選擇 `[dependency-groups]`，從而確認了 `--group` 才是正確的參數，指明了唯一的、正確的修復方向。

*👨‍🍳 **主廚筆記**: 這個案例的完整偵錯過程，展示了追溯 `git log` 的重要性。詳見 [我的工作日誌 (2025-09-22)](GEMINI.md#本次會話總結與學習教訓-2025-09-22)，了解我們是如何在 `Makefile` 和 `pyproject.toml` 的矛盾中找到真相的。*

### 1.3 精準修改，避免副作用
- **原則**: 修復 Bug 或修改程式碼時，應採取最小、最精準的修改。
- **心法**: 在使用 `replace` 等工具時，務必提供足夠的上下文，確保只修改到目標程式碼。這能有效避免「改 A 壞 B」的副作用，是建立穩定性的基礎。

### 1.4 徹底理解工具，避免「自動修復」陷阱
- **情境**: 在修復 `projects_api.py` 的技術債後，執行 `make lint-be` 驗證，卻導致大量不相關的檔案被自動修改，汙染了工作區。
- **教訓**: **永遠不要假設一個指令的行為**。`make lint-be` 看似是單純的檢查工具，但透過閱讀 `Makefile` 才發現其包含了 `--fix` 參數，會自動修改檔案。這種帶有副作用的指令是極其危險的。
- **最佳實踐**: 在處理有潛在副作用的工具時，必須遵循「**先分析 -> 原子化寫入 -> 再驗證**」的安全工作流程：
    1.  **分析 (Analyze)**: 使用該工具的「唯讀模式」（如 `ruff check` 而非 `ruff check --fix`）來**完整地**收集所有需要修改的點。
    2.  **原子化寫入 (Atomic Write)**: 在本地將所有必要的修改（功能程式碼 + 所有 Lint 修復）一次性準備好，然後使用單一的 `write_file` 指令完整覆寫檔案。
    3.  **驗證 (Verify)**: 此時，再執行原來的指令（如 `make lint-be`）。因為檔案已經是乾淨的，帶有副作用的 `--fix` 旗標將無事可做，該指令從而變成一個純粹的、安全的**驗證步驟**。

*👨‍🍳 **主廚筆記**: 這條原則來自一次慘痛的教訓。詳見 [我的工作日誌 (2025-09-23)](GEMINI.md#本次會話總結與學習教訓-2025-09-23)，了解 `make lint-be` 的 `--fix` 副作用是如何導致信任危機，並最終催生出這套安全工作流程的。*

### 1.5 撰寫冪等的資料庫腳本 (Writing Idempotent Database Scripts)
- **情境**: 執行資料庫遷移腳本（如 `000_unified_schema.sql`）時，因 `policy ... already exists` 等錯誤而中斷。
- **心法**: 資料庫遷移腳本應始終具備「冪等性 (Idempotency)」，確保其可以安全地重複執行而不會中途失敗。這犧牲了微不足道的效能，換來了設定過程的穩定性與可靠性。
- **最佳實踐**: 對於不支援 `CREATE ... IF NOT EXISTS` 的資料庫物件（如 `POLICY`, `FUNCTION`, `TRIGGER`），在 `CREATE` 語句之前，必須先使用 `DROP ... IF EXISTS` 語句進行清理。
- **範例**:
    ```sql
    -- 不穩健的寫法 (Brittle way)
    CREATE POLICY "MyPolicy" ON my_table;

    -- 穩健的、冪等的寫法 (Robust, Idempotent way)
    DROP POLICY IF EXISTS "MyPolicy" ON my_table;
    CREATE POLICY "MyPolicy" ON my_table;
    ```

*👨‍🍳 **主廚筆記**: 這個原則是在本地環境啟動過程中，反覆遭遇資料庫錯誤後總結出來的。詳見 [我的工作日誌 (2025-09-21)](GEMINI.md#本次會話總結與學習教訓-2025-09-21)，查看關於 `000_unified_schema.sql` 冪等性修復的討論。*

### 1.6 以 `Makefile` 作為指令的單一事實來源 (Makefile as Single Source of Truth)
- **情境**: 專案中的 `README.md` 或其他貢獻指南，記載了與 `Makefile` 中不一致的、或已經過時的指令，導致開發者遵循文件操作時發生錯誤。
- **心法**: **可執行的腳本 (`Makefile`) 是指令的最終真理**。文件應當是腳本的「說明」，而不是一個獨立的、可能過時的副本。
- **最佳實踐**: 當新增或修改一個開發流程時，應優先更新 `Makefile`。然後，在撰寫 `.md` 文件時，應**引用** `make <command>`，而不是直接複製貼上底層的 shell 指令。這確保了當 `Makefile` 更新時，文件中的指令引用永遠不會過時。

*👨‍🍳 **主廚筆記**: 這個共識是在多次因文件與 `Makefile` 不一致而導致啟動失敗後確立的。詳見 [我的工作日誌 (2025-09-19)](GEMINI.md#本次會話總結與學習教訓-2025-09-19)，了解我們是如何統一指令，並確立 `Makefile` 核心地位的。*

### 1.7 檔案修改與復原的最佳實踐 (Best Practices for File Modification & Recovery)
為了確保程式碼修改的穩定性與可追蹤性，並避免在開發過程中產生難以修復的錯誤，請遵循以下最佳實踐：

1.  **優先使用 `write_file` 進行完整覆寫**
    *   **情境**: 當需要對一個檔案進行多行、或結構性的修改時。
    *   **風險操作 (應避免)**: 應避免對複雜的程式碼塊，連續執行多次、零碎的 `replace` 操作。這種方法容易因為字串匹配不精確、或遺漏修改點，而導致檔案損毀或語法錯誤。
    *   **最佳實踐**: 在動手修改前，先在心中或草稿中構思好完整的最終檔案內容。然後，**使用 `write_file` 工具，將正確的完整內容一次性地覆寫目標檔案**。這能確保檔案的最終狀態是 100% 正確的。
    *   **實戰案例 (2025-09-08)**: 在開發「任務附件顯示」功能時，多次嘗試使用 `replace` 修改 `DashboardPage.tsx` 失敗，因為檔案內容在讀取和寫入之間存在微小差異。最終改用 `read_file` 獲取最新內容，然後使用 `write_file` 一次性覆寫，成功解決了問題。

2.  **使用 `git checkout` 作為首選復原手段**
    *   **情境**: 當執行檔案修改操作（無論是 `replace` 或 `write_file`）後，執行測試 (`make test-be`/`make test-fe-project`) 失敗，且錯誤訊息指向檔案語法或結構問題時。
    *   **風險操作 (應避免)**: 不要在一個可能已損壞的檔案基礎上，繼續嘗試用 `replace` 進行「修補」。這往往會讓問題變得更複雜。
    *   **最佳實踐**: **立即使用 `git checkout -- <file_path>` 指令**，將出問題的檔案還原到上次提交時的乾淨狀態。然後，回到第一步，重新分析問題並使用 `write_file` 進行一次性修改。這能確保您永遠在一個已知的、正確的基礎上進行工作。

*👨‍🍳 **主廚筆記**: 這個原則是在多次嘗試修補檔案不成，最終導致需要手動恢復時得到的教訓。詳見 [我的工作日誌 (2025-09-23)](GEMINI.md#本次會話總結與學習教訓-2025-09-23)，其中記錄了放棄修補、直接使用 `git checkout` 恢復穩定狀態的決策過程。*

---

## 第二章：環境設定 (Environment Setup)

### 2.1 本地開發環境啟動與驗證 SOP (v1.0 - 2025-09-19)
本文件是經歷了數次失敗與偵錯後，總結出的最終、最可靠的本地開發環境啟動流程。

#### 2.1.1 目標 (Objective)
在本地成功啟動一個完整、可用於端對端手動測試的開發環境。

#### 2.1.2 核心架構 (Core Architecture)
本地開發環境由三個獨立運行的部分組成，必須對它們有清晰的認識：
- **核心後端 (Core Backend)**:
  - **服務**: `archon-server`, `archon-mcp`
  - **運行方式**: 在 Docker 容器中運行。
  - **監控埠號**: `8181` (API), `8051` (MCP)
- **管理後台 (Admin UI)**:
  - **服務**: `archon-ui-main`
  - **運行方式**: 在本地終端機中運行 (Vite Dev Server)。
  - **監控埠號**: `3737`
- **使用者介面 (End-User UI)**:
  - **服務**: `enduser-ui-fe`
  - **運行方式**: 在本地終端機中運行 (Vite Dev Server)。
  - **監控埠號**: `5173`

#### 2.1.3 執行步驟 (Execution Steps)
**第一步：清理環境 (Clean Environment)**
確保沒有任何殘留的 Docker 容器在運行，避免連接埠衝突。
```bash
make stop
# 預期結果：看到 "Services stopped"，且 `docker ps -a` 應為空。
```

**第二步：安裝所有依賴 (Install All Dependencies)**
此步驟會安裝專案所需的所有後端和前端依賴。
```bash
make install
make install-ui
# 預期結果：兩個指令都成功執行，沒有錯誤訊息。
```

**第三步：啟動核心服務 (Start Core Services)**
在**第一個終端機分頁**中，啟動後端服務和管理後台 UI。
```bash
make dev
# 預期結果：指令會持續運行，並在日誌最後顯示 Vite 伺服器已在 http://localhost:3737 上準備就緒。
```

**第四步：啟動使用者介面 (Start End-User UI)**
**打開一個新的終端機分頁**，進入 `enduser-ui-fe` 目錄並啟動其開發伺服器。
```bash
cd enduser-ui-fe && npm run dev
# 預期結果：指令會持續運行，並顯示 Vite 伺服器已在 http://localhost:5173 上準備就緒。
```

#### 2.1.4 排錯計畫 v2 (已加入「改A壞B」風險評估)

##### **第一階段：資料庫準備**
**目標**: 在 Supabase SQL Editor 中，成功手動依序執行 `000_unified_schema.sql` 和 `seed_mock_data.sql`。

| **潛在錯誤** | **解決方案** | **「改A壞B」風險與緩解策略** |
| :--- | :--- | :--- |
| 1. SQL 語法錯誤 (Syntax Error) | 我讀取 SQL 檔案，分析後提出 `replace` 或 `write_file` 修正。 | **風險**: **高**。直接修改共享的 SQL 腳本，可能會破壞所有人的開發環境。<br>**緩解策略**: 我**不會**直接修改原檔案。我會將修正後的 SQL 內容輸出到一個**臨時檔案** (如 `temp_fix.sql`) 中，在您確認邏輯無誤後，我才會提議覆寫原始檔案，並再次提醒這是一個會被 `git` 追蹤的永久性修改。 |
| 2. 物件已存在 (Object already exists) | **(內容已根據 `GEMINI.md` 修正)** `seed_mock_data.sql` 對部分資料表**不是**冪等的，重複執行會因違反 `UNIQUE` 約束而失敗。若發生此錯誤，建議在開發環境中執行 `migration/RESET_DB.sql` 來清空資料庫後重試。 | **風險**: **極高**。`RESET_DB.sql` 是破壞性操作，會清空資料庫，可能導致您手動添加的、未記錄的測試資料遺失。<br>**緩解策略**: 我**必須**用加粗和警告的語氣，再三向您確認您理解其後果，並主動詢問：「**資料庫中是否有任何需要保留的資料？**」。我只會將其作為最後手段。 |

##### **第二階段：應用程式啟動**
**目標**: 成功啟動所有服務，並能在瀏覽器中存取 `http://localhost:3737` (管理後台) 和 `http://localhost:5173` (使用者介面)。

| **潛在錯誤** | **解決方案** | **「改A壞B」風險與緩解策略** |
| :--- | :--- | :--- |
| 1. `make dev` 埠號衝突 (Port in use) | 執行 `make stop` 清理環境。 | **風險**: **低**。`make stop` 是 SOP 的一部分，設計上只會停止 `docker-compose.yml` 中定義的服務，是安全的清理操作。 |
| 2. `enduser-ui-fe` 依賴找不到 | **(內容已根據 `GEMINI.md` 修正)** 重新執行 `make install-ui`。若問題持續，可嘗試進入 `enduser-ui-fe` 目錄下執行 `pnpm install`。 | **風險**: **中等**。如果 `package.json` 使用了浮動版本號 (如 `^1.2.3`)，`pnpm install` 可能會引入有破壞性變更的新版套件。<br>**緩解策略**: 在建議安裝前，我會先檢查 `enduser-ui-fe/` 目錄下是否存在 `pnpm-lock.yaml` 檔案。<br>  - **如果存在**，我會建議執行 `pnpm install --frozen-lockfile`，它會嚴格按照 lock 檔案安裝，**完全避免**此風險。<br>  - **如果不存在**，我會指出 `pnpm install` 的風險，並建議在安裝後立即執行 `make test-fe-project project=enduser-ui-fe` 來驗證變更。 |
| 3. `enduser-ui-fe` 啟動時無聲掛起 | 檢查根目錄 `.env` 檔案中的 `GEMINI_API_KEY`。 | **風險**: **極低**。此為唯讀檢查操作，僅要求使用者確認，不涉及任何修改。 |

#### 2.1.5 最終驗證 (Final Verification)
當所有服務都成功啟動後，請在瀏覽器中打開**使用者介面**: `http://localhost:5173`，並根據 `TODO.md` 的指示，完成一次「建立任務 -> 指派給 Agent -> 驗證產出的附件」的完整端對端測試流程。

### 2.2 後端依賴與環境管理 (Backend Dependency & Environment)
為了確保後端開發環境在不同平台（macOS, Windows, Linux）之間的一致性與穩定性，我們總結了以下最佳實踐：

1.  **鎖定檔案的管理 (`uv.lock`)**
    *   **問題**: `python/uv.lock` 檔案會因為作業系統或 Python 版本的不同，而產生不相容的內容。例如，`torch` 套件在不同平台上有不同的編譯版本，強制提交 lock 檔案會導致其他開發者無法成功安裝依賴。
    *   **結論**: `python/uv.lock` **必須**被加入到專案根目錄的 `.gitignore` 檔案中。每位開發者都應該在自己的環境中生成一份本地的 lock 檔案，而不是共用同一份。

2.  **安裝特定任務的依賴**
    *   **問題**: 執行 `make test-be` 或 `make lint-be` 時，可能會出現 `ModuleNotFoundError` (例如 `pytest-mock` 找不到) 或其他依賴問題。
    *   **原因**: 這是因為 `pyproject.toml` 將 `test` 和 `dev` 的依賴分組管理，預設的 `uv sync` 不會安裝它們。
    *   **解法**: `Makefile` 中的指令已經更新，會自動處理這個問題。當您執行 `make test-be` 時，它會先執行 `uv sync --group dev --group mcp --group agents` 來安裝測試所需的額外套件。同理，`make lint-be` 也會安裝 `dev` 依賴。

3.  **Makefile 的跨平台相容性**
    *   **問題**: `Makefile` 中的某些語法（例如註解或複雜的條件判斷）在 Windows 的 `make` 環境中可能會解析失敗。
    *   **結論**: 專案中的 `Makefile` 已經過簡化，移除了可能導致問題的複雜語法，以確保核心指令（如 `make test-be`, `make test-fe-project`）在主流作業系統上都能正常運作。

### 2.3 跨平台指令注意事項 (Cross-platform Command Notes)
- **問題**: 在 Windows 環境下，使用 `rm` 指令會失敗。
- **解法**: 在 Windows 環境下，請使用 `del` 指令來刪除檔案。在撰寫跨平台的指令時，需要特別注意不同作業系統的指令差異。

### 2.4 開發環境小撇步
- 使用 `pnpm dlx turbo run where <project_name>` 來跳轉到特定套件，而不是用 `ls` 慢慢找。
- 運行 `pnpm install --filter <project_name>` 來安裝套件，這樣 Vite、ESLint 和 TypeScript 才能正確識別它。
- 使用 `pnpm create vite@latest <project_name> -- --template react-ts` 快速建立一個新的 React + Vite + TypeScript 專案。
- 檢查每個套件 `package.json` 裡的 name 欄位來確認正確名稱，忽略最上層的那個。

---

## 第三章：測試指南 (Testing Guide)

### 3.1 通用測試指令
- CI 計畫設定在 `.github/workflows` 資料夾裡。
- 運行 `pnpm turbo run test --filter <project_name>` 來執行該套件的所有檢查。
- 在套件的根目錄下，你也可以直接用 `pnpm test`。合併前請確保所有測試都通過。
- 如果只想跑單一測試，可以加上 Vitest 的 pattern：
  ```bash
  pnpm vitest run -t "<test name>"
  ```
- 修復所有測試或型別錯誤，直到整個測試套件都亮綠燈。
- 移動檔案或更改 imports 後，記得跑 `pnpm lint --filter <project_name>` 確保 ESLint 和 TypeScript 規則仍然通過。
- 即使沒人要求，也請為你修改的程式碼增加或更新測試。

### 3.2 後端 API 測試：模擬資料庫 (Backend API Testing: Mocking the Database)
所有後端 API 測試都**嚴格禁止**連線到真實的資料庫。為了達成此目標，我們採用了基於 `pytest` 的 `fixture` 和 `unittest.mock` 的模擬機制。

**核心原理**:
1.  **自動注入的模擬器**: 在 `python/tests/conftest.py` 中，我們定義了一個名為 `mock_supabase_client` 的 `fixture`。這個 `fixture` 會建立一個 `MagicMock` 物件，用來模擬真實的 `SupabaseClient`。
2.  **全域攔截**: 同樣在 `conftest.py` 中，我們使用 `@pytest.fixture(autouse=True)` 和 `patch` 來自動攔截所有測試中對 `supabase.create_client` 或 `get_supabase_client` 的呼叫，並將它們替換為 `mock_supabase_client` 的實例。
3.  **無需手動傳遞**: 因為使用了 `autouse=True` 的 `fixture`，開發者在撰寫新的 API 測試時，**無需**手動處理模擬的設定。`pytest` 會自動將 `client` (FastAPI 測試客戶端) 和 `mock_supabase_client` (模擬資料庫客戶端) 這兩個 `fixture` 注入到您的測試函式中。

**如何在測試中使用**:
您只需要將 `client` 和 `mock_supabase_client` 作為參數加入到您的測試函式簽名中，就可以開始使用它們。

**程式碼範例**:
以下是一個簡化的測試範例，展示如何設定模擬的回傳值，並驗證 API 的行為。
```python
# 檔案: python/tests/server/api_routes/test_your_api.py

# 1. 將 fixture 加入函式簽名
def test_your_api_endpoint(client, mock_supabase_client):
    # 2. Arrange (安排): 設定模擬資料庫的行為
    # 模擬一個成功的資料庫插入操作
    mock_response = MagicMock()
    mock_response.data = [{'id': 'new_record_id', 'name': 'test_name'}]
    
    # 設定當 .insert(...).execute() 被呼叫時，要回傳的假資料
    mock_supabase_client.table.return_value.insert.return_value.execute.return_value = mock_response

    # 3. Act (執行): 透過測試 client 呼叫您的 API
    api_response = client.post("/api/your-endpoint", json={"name": "test_name"})

    # 4. Assert (斷言): 驗證 API 的回傳結果是否符合預期
    assert api_response.status_code == 201
    assert api_response.json()["message"] == "Record created successfully"
    assert api_response.json()["record_id"] == "new_record_id"

    # (可選) 驗證 insert 方法是否被正確呼叫
    mock_supabase_client.table.return_value.insert.assert_called_once_with({"name": "test_name"})
```

### 3.2.1 如何測試啟動背景任務的 API 端點

**情境**: 當一個 API 端點的主要職責是接收請求，然後使用 `asyncio.create_task` 啟動一個長時間運行的背景任務來處理時，我們不應該在 API 的單元測試中等待整個背景任務完成。

**最佳實踐**: **測試端點的「職責」，而非「實作細節」**。此類端點的職責是「正確地啟動任務」。因此，我們應該模擬 (Mock) `asyncio.create_task` 本身，並驗證它是否被以正確的參數呼叫。

**程式碼範例**:
```python
# 檔案: python/tests/server/api_routes/test_knowledge_api.py

# 1. 在測試函式上使用 @patch 來模擬 `create_task`
@patch('src.server.api_routes.knowledge_api.asyncio.create_task')
def test_upload_document_endpoint_success(mock_create_task, client: TestClient):
    """
    驗證 /documents/upload 端點能成功接收檔案，
    並正確啟動一個背景任務。
    """
    # 2. Arrange (安排): 準備測試資料
    file_name = "test_document.txt"
    file_content = b"This is a test file."

    # 3. Act (執行): 呼叫 API 端點
    response = client.post(
        "/api/documents/upload",
        files={"file": (file_name, file_content, "text/plain")},
        data={"tags": '["test"]', "knowledge_type": "docs"},
    )

    # 4. Assert (斷言):
    # 斷言 API 立即回傳了成功的回應
    assert response.status_code == 200
    assert response.json()["success"] is True
    assert "progressId" in response.json()

    # 斷言背景任務有被啟動
    mock_create_task.assert_called_once()
```

**關於 `RuntimeWarning`**:
採用此策略時，`pytest` 可能會顯示 `RuntimeWarning: coroutine ... was never awaited` 的警告。這是一個**預期中且無害的**副作用，因為被傳遞給模擬 `create_task` 的協程確實從未被執行。這恰好證明了我們的測試成功地將 API 端點的職責與背景任務的實作細節隔離開來。

*👨‍🍳 **主廚筆記**: 這個測試策略是在為檔案上傳功能編寫測試時確立的。詳見 [我的工作日誌 (2025-09-27)](GEMINI.md#本次會話總結與學習教訓-2025-09-27)，了解其背後的完整偵錯與決策過程。*

### 3.3 前端測試實踐與常見問題 (Frontend Testing Practices & FAQ)
在本次開發週期中，我們總結了以下前端測試的最佳實踐與常見問題的解決方案：

1.  **如何執行特定子專案的測試？**
    *   **問題**: 專案根目錄的 `make test-fe` 指令只會測試 `archon-ui-main`。
    *   **解法 (已根據 `Makefile` 修正)**: 使用 `Makefile` 中提供的標準指令，可以更精準地執行測試：
        *   **方法1：測試特定子專案**
            ```bash
            # 語法：make test-fe-project project=<project_name>
            make test-fe-project project=enduser-ui-fe
            ```
            這個指令只會執行 `enduser-ui-fe` 目錄下的所有測試。

        *   **方法2：測試特定單一檔案**
            ```bash
            # 語法：make test-fe-single project=<project_name> test=<test_name>
            make test-fe-single project=enduser-ui-fe test="TaskModal"
            ```
            這個指令只會執行 `enduser-ui-fe` 中，名稱包含 "TaskModal" 的測試，速度最快。

2.  **`Failed to resolve import` 錯誤**
    *   **問題**: 執行測試時，出現無法解析 `import` 的錯誤，例如 `@testing-library/user-event`。
    *   **解法**: 這代表該專案的 `package.json` 中缺少了必要的開發依賴 (`devDependencies`)。需在該專案目錄下使用 `pnpm install --save-dev <package-name>` 來安裝缺少的套件。

3.  **測試中找不到「純圖示按鈕」**
    *   **問題**: 使用 `screen.getByRole('button', { name: /.../i })` 無法找到一個只有圖示（例如 "X"）的按鈕。
    *   **解法**: 為了無障礙性 (a11y) 和測試的穩定性，純圖示按鈕應加上 `aria-label` 屬性，為按鈕提供一個文字描述。例如：
        ```html
        <button aria-label="Close">
          <XIcon />
        </button>
        ```

4.  **表單必填欄位的驗證測試**
    *   **問題**: 當 `input` 有 `required` 屬性時，在測試中 `userEvent.click(submitButton)` 可能不會觸發 `submit` 事件，導致無法測試元件內部的錯誤處理邏輯（例如 `alert`）。
    *   **解法**: 為了繞過瀏覽器的預設驗證行為，專門測試元件的內部邏輯，可以使用 `fireEvent.submit(submitButton)` 來直接觸發 `submit` 事件。

5.  **Vitest 的 `vi.mock` 變數提升問題**
    *   **問題**: 測試出現 `ReferenceError: Cannot access '...' before initialization`。
    *   **原因**: `vi.mock` 會被 Vitest 自動提升到檔案的最頂部執行。如果在 `vi.mock` 的工廠函式中，使用了在檔案頂層才被宣告的變數，就會因為變數尚未初始化而產生此錯誤。
    *   **解法**: 將所有 `vi.mock` 需要用到的變數（例如 `mockTasks`, `mockUsers`），都直接定義在 `vi.mock` 的工廠函式**內部**，而不是在檔案的頂層。

6.  **測試因「元件未匯出」而失敗**
    *   **問題**: 測試出現 `Error: Element type is invalid: expected a string ... but got: undefined`。
    *   **原因**: 這通常發生在 `render` 一個元件時，該元件內部 import 了另一個子元件，但該子元件卻沒有被正確地從來源檔案（例如 `Icons.tsx`）中 `export` 出來。
    *   **解法**: 仔細檢查錯誤訊息中提到的元件（例如 `ListView`），找出它 import 了哪些子元件（例如 `PaperclipIcon`），然後去對應的檔案（`Icons.tsx`）確認該子元件是否已 `export`。

---

## 第四章：貢獻流程 (Contribution Workflow)

### 4.1 Git 工作流程常見問題 (Git Workflow FAQ)
1.  **`git cherry-pick --continue` 卡住**
    *   **問題**: 在解決衝突並 `git add` 檔案後，執行 `git cherry-pick --continue` 指令卡住，沒有任何反應。
    *   **原因**: 這通常發生在非互動式的指令環境中。`cherry-pick` 預設會嘗試打開文字編輯器來讓您確認 commit message，或觸發 GPG 簽章的密碼輸入提示，這些都會導致流程卡住。
    *   **解法**: 使用 `--no-edit` 和 `--no-gpg-sign` 兩個參數，可以繞過所有互動環節。
        ```bash
        # 解決衝突並 add 檔案後，執行此指令
        git cherry-pick --continue --no-edit --no-gpg-sign
        ```

### 4.2 PR 提交規範
- **標題格式**：`[<project_name>] <標題>`
- **提交前檢查**: 務必運行 `pnpm lint` 和 `pnpm test`。

---

## 第五章：部署 (Deployment)

### 5.1 部署策略與分支管理 (Deployment Strategy & Branch Management)
為了避免因流程不清導致的部署失敗，並確保每次上線的程式碼都穩定可靠，所有團隊成員應遵循以下策略。

#### 5.1.1 部署環境 (Deployment Environment)
- **平台**: 本專案所有服務，包括後端 (FastAPI) 與前端 (React)，均統一使用 **Render** 進行部署。
- **目標**: 任何關於 Vercel, Supabase Functions 或其他平台的部署假設都是**不正確的**。所有與部署相關的修改（如 Dockerfile, 啟動指令）都應以 Render 環境為唯一目標。

#### 5.1.2 分支策略 (Branching Strategy) - **專案特定**
**【警告】本專案有特定的分支策略，與標準 GitFlow 不同。**

- **`main` 分支**: **請勿使用。** `git log` 顯示 `main` 分支與本專案工作無關，其程式碼版本不相容。
- **`feature/...` 分支**: 所有開發、修復、重構都**必須**在獨立的 `feature/...` 分支上進行。這些分支是本專案的實際工作線。
- **部署**: 部署**必須**從 `feature/...` 分支進行。在部署前，應確保該 `feature` 分支是完整且穩定的。**嚴禁**將 `feature` 分支合併到 `main`，也**嚴禁**從 `main` 部署。

### 5.2 部署標準作業流程 (SOP) - 修訂版 v1.2 (教學模式)
此流程將一步步指導您如何將一個穩定的 `feature` 分支，完整地部署到 Render 平台。

#### **階段一：本地最終檢查 (Final Pre-flight Check)**
*   **目的**: 確保您本地的程式碼是最新且無誤的。
*   **動作**:
    1.  在您的終端機中，執行 `git pull`，確保您擁有所有最新的變更。
    2.  接著執行 `make test`，確認所有測試均成功通過。

#### **階段二：資料庫遷移 (Manual Database Migration)**
*   **目的**: 確保線上的資料庫結構與程式碼版本同步。這是最關鍵的手動步驟。
*   **動作**:
    1.  請您登入 **Supabase 儀表板** 並進入 **SQL Editor**。
    2.  **清空資料庫 (如果需要)**: 如果您的目標資料庫不是全新的，為了避免後續錯誤，請先執行 `migration/RESET_DB.sql` 的內容。**警告：此操作會刪除所有資料。**
    3.  **執行核心腳本**: 依序複製並執行以下兩個腳本的內容：
        *   `migration/000_unified_schema.sql`
        *   `migration/seed_mock_data.sql`

#### **階段三：Render 服務設定與部署 (Render Setup & Deployment)**
*   **目的**: 在 Render 上正確設定三個服務（1個後端，2個前端），並觸發部署。
*   **動作 (後端 `archon-server`)**:
    1.  在 Render 點擊 "New" -> "**Web Service**"，並連接您的 GitHub 倉庫。
    2.  **Name**: `archon-server` (或您自訂的名稱)
    3.  **Root Directory**: `python`
    4.  **Dockerfile Path**: `python/Dockerfile.server`
    5.  **Start Command**: (保持空白)
    6.  **環境變數**: 根據您的 `.env` 檔案，將 `SUPABASE_URL`, `SUPABASE_SERVICE_KEY` 等變數加入。
    7.  點擊 "Create Web Service" 並等待其首次部署完成。完成後，複製其公開網址 (例如 `https://your-archon-server.onrender.com`)。

*   **動作 (前端 1 - `archon-ui-main`)**:
    1.  在 Render 點擊 "New" -> "**Static Site**"。
    2.  **Name**: `archon-ui-main` (或自訂)
    3.  **Root Directory**: `archon-ui-main`
    4.  **Build Command**: `pnpm install --frozen-lockfile && pnpm run build`
    5.  **Publish Directory**: `archon-ui-main/dist`
    6.  **環境變數**: 新增一個名為 `VITE_API_URL` 的變數，其值貼上您剛剛複製的後端服務網址。
    7.  點擊 "Create Static Site"。

*   **動作 (前端 2 - `enduser-ui-fe`)**:
    1.  再次點擊 "New" -> "**Static Site**"。
    2.  **Name**: `enduser-ui-fe` (或自訂)
    3.  **Root Directory**: `enduser-ui-fe`
    4.  **Build Command**: `pnpm install --frozen-lockfile && pnpm run build`
    5.  **Publish Directory**: `enduser-ui-fe/dist`
    6.  **環境變數**: 同樣新增 `VITE_API_URL` 變數，其值也是您的後端服務網址。
    7.  點擊 "Create Static Site"。

*   **動作 (觸發部署)**:
    *   在您的本地終端機中，執行以下指令來推送您的程式碼，這將觸發 Render 上所有服務的自動建置與部署。
        ```bash
        git push render feature/e2e-file-upload:main
        ```

#### **階段四：部署後驗證 (Post-Deployment Verification)**
*   **目的**: 確認所有服務都已成功上線並正常運作。
*   **動作**:
    1.  **監控日誌**: 在 Render 儀表板上，檢查三個服務的部署日誌，確保沒有錯誤。
    2.  **健康檢查**: 存取後端服務的 `/health` 端點，確認看到成功的回應。
    3.  **手動煙霧測試**: 分別打開 `archon-ui-main` 和 `enduser-ui-fe` 的公開網址，實際操作核心功能，確認一切符合預期。

### 5.3 Render 部署除錯實戰指南 (Render Deployment Debugging Guide)
根據 `spike/verify-deployment-pipeline` 的部署驗證任務，我們總結了首次在 Render 上部署後端服務時，最關鍵的五個設定。如果遇到部署失敗，請優先檢查這些項目：
1.  **Dockerfile Path**:
    *   **問題**: Render 在根目錄找不到 `Dockerfile`。
    *   **解法**: 在 Render 設定中，將此路徑指定為 `python/Dockerfile.server`。
2.  **Root Directory**:
    *   **問題**: Docker 建置時，找不到 `src`, `tests` 等資料夾 (`"/tests": not found`)。
    *   **解法**: 在 Render 設定中，將此路徑指定為 `python`，告訴 Render 從 `python` 目錄開始建置。
3.  **Docker Command** (或 Start Command):
    *   **問題**: 服務啟動時發生 `could not find ... /python/python` 錯誤。
    *   **解法**: 在 Render 設定中，將此欄位**保持空白**。這會強制 Render 使用我們在 `Dockerfile.server` 中定義好的 `CMD` 指令，而不是用一個不正確的指令覆蓋它。
4.  **環境變數 `ARCHON_SERVER_PORT`**:
    *   **問題**: 部署成功，但日誌顯示 `No open ports detected`。
    *   **解法**: 在 Render 的環境變數設定中，將 `ARCHON_SERVER_PORT` 的值設定為 `8181`。Render 的系統會自動偵測到這個 Port 並完成網路設定，即使它與預設的 `10000` 不同。
5.  **Health Check Grace Period**:
    *   **問題**: 應用程式日誌有正常輸出，但 Render 仍然顯示 `No open ports detected`。
    *   **解法**: 這是因為我們的應用程式啟動較慢。在 Render 的健康檢查設定中，將 `Health Check Grace Period` 的值拉長，建議設定為 `120` 秒，給予服務足夠的啟動時間。

---

## 附錄 A：重要架構決策

### A.1 健康檢查邏輯已統一 (2025-09-08)
為移除重複程式碼，原有的 `/api/projects/health` 端點已被**移除**。

現在，所有服務的健康狀態（包含資料庫連線、資料表是否存在等）都已統一由 `HealthService` 管理，並只透過根路徑的 `/health` 端點對外提供。未來若有其他分支或新功能需要進行健康檢查，請務必遵循此一新架構。
