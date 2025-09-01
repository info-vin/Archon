---
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
- To focus on one step, add the Vitest pattern: `pnpm vitest run -t "<test name>"`.
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

## 測試指南
- CI 計畫設定在 `.github/workflows` 資料夾裡。
- 運行 `pnpm turbo run test --filter <project_name>` 來執行該套件的所有檢查。
- 在套件的根目錄下，你也可以直接用 `pnpm test`。合併前請確保所有測試都通過。
- 如果只想跑單一測試，可以加上 Vitest 的 pattern：`pnpm vitest run -t "<test name>"`.
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

2.  **`Failed to resolve import` 錯誤**
    *   **問題**: 執行測試時，出現無法解析 `import` 的錯誤，例如 `@testing-library/user-event`。
    *   **解法**: 這代表該專案的 `package.json` 中缺少了必要的開發依賴 (`devDependencies`)。需在該專案目錄下使用 `npm install --save-dev <package-name>` 來安裝缺少的套件。

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

### 後端 API 測試：模擬資料庫 (Backend API Testing: Mocking the Database)

為了確保後端測試的穩定與獨立性，所有測試**嚴禁**連線至真實資料庫。我們透過模擬 (Mocking) 來達成此目的。

- **測試指令**: 永遠使用 `make test-be` 來執行後端測試。此指令已在 `Makefile` 中定義，能確保在正確的虛擬環境中執行。

- **常見錯誤**: 如果測試出現 `supabase._sync.client.SupabaseException: Invalid API key` 錯誤，這代表你的測試案例意外地觸發了真實的資料庫連線。

- **解決方案**: 我們必須攔截 (patch) 任何嘗試建立真實資料庫客戶端的行為，並將其替換為測試環境提供的 `mock_supabase_client`。這需要使用 `pytest-mock` 套件提供的 `mocker` 功能。

**範例：**

假設一個 API 端點會呼叫 `LogService`，而 `LogService` 在初始化時會呼叫 `get_supabase_client()`。

**錯誤的測試寫法（會觸發真實連線）:**
```python
# 這會失敗！
def test_some_api_call_failure(client, mock_supabase_client):
    # ... 即使這裡有 mock_supabase_client，
    # LogService 內部呼叫的 get_supabase_client() 仍然是真實的。
    response = client.post("/api/some_endpoint", json={...})
    assert response.status_code == 200
```

**正確的測試寫法（使用 mocker.patch）:**
```python
# 正確！
def test_some_api_call_success(client, mock_supabase_client, mocker):
    # 使用 mocker.patch 攔截在 service 層的 get_supabase_client 呼叫
    # 並讓它回傳我們測試專用的 mock_supabase_client
    mocker.patch(
        'src.server.services.log_service.get_supabase_client',
        return_value=mock_supabase_client
    )

    # 接下來的測試邏輯...
    # ...設定 mock_supabase_client 的預期回傳值...
    mock_supabase_client.table.return_value.insert.return_value.execute.return_value = ...

    # ...觸發 API ...
    response = client.post("/api/record-gemini-log", json={...})

    # ...驗證結果...
    assert response.status_code == 201
```

## PR 提交規範
- 標題格式：[<project_name>] <標題>
- 提交前務必運行 `pnpm lint` 和 `pnpm test`。

---

### **標準提交與推送工作流程 (Commit & Push Workflow)**

為了確保每一次的程式碼提交都清晰、正確且完整，請遵循以下標準步驟：

1.  **檢查狀態 (`git status`)**
    *   在做任何操作前，先用此指令確認目前工作區的檔案狀態，了解哪些檔案被修改過。

2.  **檢視變更 (`git diff HEAD`)**
    *   在提交前，務必檢視所有變更的內容，確保沒有包含預期之外的修改。

3.  **加入暫存區 (`git add ...`)**
    *   使用 `git add <file1> <file2> ...` 將確認無誤的檔案加入暫存區。
    *   **注意**: 這是 `commit` 前的必要步驟，確保只有您想提交的變變更被包含進去。

4.  **提交變更 (`git commit -m "..."`)**
    *   執行提交，並撰寫清晰、有意義的提交訊息，說明這次變更的目的。

5.  **推送至遠端 (`git push`)**
    *   將本地的提交推送到遠端分支，與團隊成員同步進度。
    *   **注意**: 第一次推送新的分支時，需使用 `git push --set-upstream origin <branch-name>` 來建立本地與遠端分支的追蹤關係。
