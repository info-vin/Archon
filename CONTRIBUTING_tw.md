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

...

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