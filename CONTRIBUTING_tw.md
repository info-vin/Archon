## 開發流程與標準 (原 AGENTS.md 內容)

## Dev environment tips
- Use `pnpm dlx turbo run where <project_name>` to jump to a package instead of scanning with `ls`.
- Run `pnpm install --filter <project_name>` to add the package to your workspace so Vite, ESLint, and TypeScript can see it.
- Use `pnpm create vite@latest <project_name> -- --template react-ts` to spin up a new React + Vite package with TypeScript checks ready.
- Check the name field inside each package's package.json to confirm the right name—skip the top-level one.

## Testing instructions
- Find the CI plan in the .github/workflows folder.
- Run `pnpm turbo run test --filter <project_name>` to run every check defined for that package.
- From the package root you can just call `pnpm test`. The commit should pass all tests before you merge.
- To focus on one step, add the Vitest pattern:
  ```bash
  pnpm vitest run -t "<test name>"
  ```
- Fix any test or type errors until the whole suite is green.
- After moving files or changing imports, run `pnpm lint --filter <project_name>` to be sure ESLint and TypeScript rules still pass.
- Add or update tests for the code you change, even if nobody asked.

## PR instructions
- Title format: [<project_name>] <Title>
- Always run `pnpm lint` and `pnpm test` before committing.

## 開發環境小撇步
- 使用 `pnpm dlx turbo run where <project_name>` 來跳轉到特定套件，而不是用 `ls` 慢慢找。
- 運行 `pnpm install --filter <project_name>` 來安裝套件，這樣 Vite、ESLint 和 TypeScript 才能正確識別它。
- 使用 `pnpm create vite@latest <project_name> -- --template react-ts` 快速建立一個新的 React + Vite + TypeScript 專案。
- 檢查每個套件 `package.json` 裡的 name 欄位來確認正確名稱，忽略最上層的那個。

### **跨平台指令注意事項 (Cross-platform Command Notes)**

- **問題**: 在 Windows 環境下，使用 `rm` 指令會失敗。
- **解法**: 在 Windows 環境下，請使用 `del` 指令來刪除檔案。在撰寫跨平台的指令時，需要特別注意不同作業系統的指令差異。

### 後端依賴與環境管理 (Backend Dependency & Environment)

為了確保後端開發環境在不同平台（macOS, Windows, Linux）之間的一致性與穩定性，我們總結了以下最佳實踐：

1.  **鎖定檔案的管理 (`uv.lock`)**
    *   **問題**: `python/uv.lock` 檔案會因為作業系統或 Python 版本的不同，而產生不相容的內容。例如，`torch` 套件在不同平台上有不同的編譯版本，強制提交 lock 檔案會導致其他開發者無法成功安裝依賴。
    *   **結論**: `python/uv.lock` **必須**被加入到專案根目錄的 `.gitignore` 檔案中。每位開發者都應該在自己的環境中生成一份本地的 lock 檔案，而不是共用同一份。

2.  **安裝特定任務的依賴**
    *   **問題**: 執行 `make test-be` 或 `make lint-be` 時，可能會出現 `ModuleNotFoundError` (例如 `pytest-mock` 找不到) 或其他依賴問題。
    *   **原因**: 這是因為 `pyproject.toml` 將 `test` 和 `dev` 的依賴分組管理，預設的 `uv sync` 不會安裝它們。
    *   **解法**: `Makefile` 中的指令已經更新，會自動處理這個問題。當您執行 `make test-be` 時，它會先執行 `uv sync --extra test` 來安裝測試所需的額外套件。同理，`make lint-be` 也會安裝 `dev` 依賴。

3.  **Makefile 的跨平台相容性**
    *   **問題**: `Makefile` 中的某些語法（例如註解或複雜的條件判斷）在 Windows 的 `make` 環境中可能會解析失敗。
    *   **結論**: 專案中的 `Makefile` 已經過簡化，移除了可能導致問題的複雜語法，以確保核心指令（如 `make test-be`, `make test-fe-project`）在主流作業系統上都能正常運作。

## 測試指南
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

### **重要架構變更**

> **【注意】健康檢查邏輯已統一 (2025-09-08)**
> 
> 為移除重複程式碼，原有的 `/api/projects/health` 端點已被**移除**。
> 
> 現在，所有服務的健康狀態（包含資料庫連線、資料表是否存在等）都已統一由 `HealthService` 管理，並只透過根路徑的 `/health` 端點對外提供。未來若有其他分支或新功能需要進行健康檢查，請務必遵循此一新架構。

### 前端測試實踐與常見問題 (Frontend Testing Practices & FAQ)

在本次開發週期中，我們總結了以下前端測試的最佳實踐與常見問題的解決方案：

1.  **如何執行特定子專案的測試？**
    *   **問題**: 專案根目錄的 `make test-fe` 指令只會測試 `archon-ui-main`。
    *   **解法**: 必須先進入目標專案的目錄，再執行測試指令。例如，要測試 `enduser-ui-fe`，正確的指令是：
        ```bash
        cd enduser-ui-fe && npm test
        ```

2.  **如何透過 `make` 指令加速測試？**
    *   **問題**: `make test-fe` 會執行所有前端測試，速度較慢。
    *   **解法**: 我們在 `Makefile` 中新增了兩個指令，讓您可以更精準地執行測試：
        *   **方法2：測試特定子專案**
            ```bash
            # 語法：make test-fe-project project=<project_name>
            make test-fe-project project=enduser-ui-fe
            ```
            這個指令只會執行 `enduser-ui-fe` 目錄下的所有測試。

        *   **方法3：測試特定單一檔案**
            ```bash
            # 語法：make test-fe-single project=<project_name> test=<test_name>
            make test-fe-single project=enduser-ui-fe test="TaskModal"
            ```
            這個指令只會執行 `enduser-ui-fe` 中，名稱包含 "TaskModal" 的測試，速度最快。

3.  **`Failed to resolve import` 錯誤**
    *   **問題**: 執行測試時，出現無法解析 `import` 的錯誤，例如 `@testing-library/user-event`。
    *   **解法**: 這代表該專案的 `package.json` 中缺少了必要的開發依賴 (`devDependencies`)。需在該專案目錄下使用 `npm install --save-dev <package-name>` 來安裝缺少的套件。

4.  **測試中找不到「純圖示按鈕」**
    *   **問題**: 使用 `screen.getByRole('button', { name: /.../i })` 無法找到一個只有圖示（例如 "X"）的按鈕。
    *   **解法**: 為了無障礙性 (a11y) 和測試的穩定性，純圖示按鈕應加上 `aria-label` 屬性，為按鈕提供一個文字描述。例如：
        ```html
        <button aria-label="Close">
          <XIcon />
        </button>
        ```

5.  **表單必填欄位的驗證測試**
    *   **問題**: 當 `input` 有 `required` 屬性時，在測試中 `userEvent.click(submitButton)` 可能不會觸發 `submit` 事件，導致無法測試元件內部的錯誤處理邏輯（例如 `alert`）。
    *   **解法**: 為了繞過瀏覽器的預設驗證行為，專門測試元件的內部邏輯，可以使用 `fireEvent.submit(submitButton)` 來直接觸發 `submit` 事件。

6.  **如何為沒有測試的元件建立 API Mock 與測試？**
    *   **情境**: 當需要為一個呼叫 API 的元件（例如 `DashboardPage.tsx`）補上測試，但卻找不到任何既有的測試檔案或 API 模擬 (`mock`) 設定時。
    *   **偵錯流程**: ...
    *   **解決方案 (建立測試環境)**: ...

7.  **Vitest 的 `vi.mock` 變數提升問題**
    *   **問題**: 測試出現 `ReferenceError: Cannot access '...' before initialization`。
    *   **原因**: `vi.mock` 會被 Vitest 自動提升到檔案的最頂部執行。如果在 `vi.mock` 的工廠函式中，使用了在檔案頂層才被宣告的變數，就會因為變數尚未初始化而產生此錯誤。
    *   **解法**: 將所有 `vi.mock` 需要用到的變數（例如 `mockTasks`, `mockUsers`），都直接定義在 `vi.mock` 的工廠函式**內部**，而不是在檔案的頂層。

8.  **測試因「元件未匯出」而失敗**
    *   **問題**: 測試出現 `Error: Element type is invalid: expected a string ... but got: undefined`。
    *   **原因**: 這通常發生在 `render` 一個元件時，該元件內部 import 了另一個子元件，但該子元件卻沒有被正確地從來源檔案（例如 `Icons.tsx`）中 `export` 出來。
    *   **解法**: 仔細檢查錯誤訊息中提到的元件（例如 `ListView`），找出它 import 了哪些子元件（例如 `PaperclipIcon`），然後去對應的檔案（`Icons.tsx`）確認該子元件是否已 `export`。

### 後端 API 測試：模擬資料庫 (Backend API Testing: Mocking the Database)

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

**關鍵點**:
- 在「Arrange」階段，透過設定 `mock_supabase_client` 的 `return_value`，您可以精準地控制資料庫層的行為，模擬成功、失敗、回傳空值等多種情境。
- 所有測試都應遵循 Arrange-Act-Assert (3A) 模式，以保持清晰和可讀性。

### 測試非同步方法 (Testing Asynchronous Methods)

...

### 測試目錄中的 `__init__.py` 檔案

...

### 避免框架特定依賴 (Avoiding Framework-Specific Dependencies)

...

## PR 提交規範
- 標題格式：[<project_name>] <標題>
- 提交前務必運行 `pnpm lint` 和 `pnpm test`。

### **Commit 訊息的特殊字元問題 (Special Characters in Commit Messages)**

...

---

### **標準提交與推送工作流程 (Commit & Push Workflow)**

...

---

## 常見環境問題與解法 (FAQ)

...

### 檔案修改與復原的最佳實踐 (Best Practices for File Modification & Recovery)

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

---

## 部署策略與分支管理 (Deployment Strategy & Branch Management)

為了避免因流程不清導致的部署失敗，並確保每次上線的程式碼都穩定可靠，所有團隊成員應遵循以下策略。

### 1. 部署環境 (Deployment Environment)
- **平台**: 本專案所有服務，包括後端 (FastAPI) 與前端 (React)，均統一使用 **Render** 進行部署。
- **目標**: 任何關於 Vercel, Supabase Functions 或其他平台的部署假設都是**不正確的**。所有與部署相關的修改（如 Dockerfile, 啟動指令）都應以 Render 環境為唯一目標。

### 2. 分支策略 (Branching Strategy)
- **`main` 分支**: 是唯一代表**穩定、可部署**程式碼的分支。
- **`feature` 分支**: 所有新功能開發、錯誤修復或重構，都必須在**獨立的 `feature/...` 分支**上進行。
- **合併流程**: 功能開發完成後，應發起 Pull Request (PR) 合併至 `main` 分支。PR 必須經過至少一位團隊成員審查，並確保所有自動化檢查 (CI) 都已通過。

### 3. 部署標準作業流程 (SOP) - 修訂版 v1.1

此流程的最終目標，是成功部署一個穩定的版本到 Render，包含所有已完成的核心功能。

#### **階段一：部署前本地檢查 (Pre-Deployment Checks)**

在推送任何程式碼到 Render 之前，必須在本地嚴格執行以下檢查清單，確保程式碼的穩定性。

1.  **同步最新程式碼**:
    ```bash
    # 根據你的目標分支，例如 main 或 spike/...
    git checkout <your-target-branch>
    git pull origin <your-target-branch>
    ```
2.  **執行完整測試 (關鍵步驟)**: 這是為了避免「測試又錯一堆」的狀況。此指令會涵蓋前後端的所有測試。
    ```bash
    make test
    ```
3.  **執行 Lint 檢查**:
    ```bash
    make lint-be
    ```
    只有當以上所有指令都成功通過後，才能進入下一階段。

#### **階段二：資料庫遷移 (Database Migration) - 關鍵手動步驟**

**這是最容易出錯的步驟！** 根據 `deployment_verification_log.txt` 的經驗，應用程式會因為資料庫結構未更新而無法啟動。

1.  **登入 Supabase 儀表板**。
2.  **進入 SQL Editor**。
3.  **比對並依序執行** `migration/` 目錄中，尚未在 Supabase 中執行過的遷移腳本。請仔細確認執行順序。

#### **階段三：Render 服務設定 (Infrastructure Setup)**

此階段在 Render 上設定三個獨立的服務。這些設定通常只需要在專案初次設定時執行。

1.  **部署後端 (`archon-server`)**:
    *   **類型**: `Web Service`
    *   **設定**: 完全依照本文件「Render 部署除錯實戰指南」章節中的後端設定（Root Directory: `python` 等）。

2.  **部署管理後台 (`archon-ui-main`)**:
    *   **類型**: `Static Site`
    *   **Root Directory**: `archon-ui-main`
    *   **Build Command**: `npm install && npm run build`
    *   **Publish Directory**: `archon-ui-main/dist`
    *   **環境變數**: 新增 `VITE_API_URL`，其值為後端服務的公開網址。

3.  **部署使用者介面 (`enduser-ui-fe`)**:
    *   **類型**: `Static Site`
    *   **Root Directory**: `enduser-ui-fe`
    *   **Build Command**: `npm install && npm run build`
    *   **Publish Directory**: `enduser-ui-fe/dist`
    *   **環境變數**: 新增 `VITE_API_URL`，其值為後端服務的公開網址。

#### **階段四：執行部署 (Deployment Execution)**
- 當 `main` 或目標分支準備就緒後，使用以下指令觸發 Render 部署：
  ```bash
  # 假設你的 Render remote 叫做 render
  git push render <your-target-branch>:main
  ```

#### **階段五：部署後驗證 (Post-Deployment Verification)**

1.  **監控日誌**: 分別檢查三個服務在 Render 上的部署日誌，確認建置 (build) 和服務啟動 (live) 過程沒有任何錯誤訊息。
2.  **健康檢查**: 存取後端服務的 `/health` 端點，確認回傳 `{"status":"ok"}` 或 `{"status":"healthy"}`。
3.  **功能驗證 (Smoke Test)**:
    *   打開 `enduser-ui-fe` 的公開網址，嘗試登入並查看任務列表。
    *   打開 `archon-ui-main` 的公開網址，確認管理儀表板能正常載入。

### 4. Render 部署除錯實戰指南 (Render Deployment Debugging Guide)

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