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

### 後端 API 測試：模擬資料庫 (Backend API Testing: Mocking the Database)

為了確保後端測試的穩定與獨立性，所有測試**嚴禁**連線至真實資料庫。我們透過模擬 (Mocking) 來達成此目的。

- **測試指令**: 永遠使用 `make test-be` 來執行後端測試。此指令已在 `Makefile` 中定義，能確保在正確的虛擬環境中執行，並安裝所有必要的依賴（包括 `dev`, `mcp`, `agents` 等 extras）。

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

### 測試非同步方法 (Testing Asynchronous Methods)

當測試非同步方法時，特別是當這些方法回傳多個值（例如 `(success, result)` 元組）時，需要正確地模擬它們的行為。

- **問題**: 直接將元組賦值給 `AsyncMock().return_value` 可能會導致 `TypeError: object tuple can't be used in 'await' expression`，因為 `AsyncMock` 預期回傳的是一個可等待的物件，而不是直接的結果。

- **解決方案**: 使用 `pytest` 的 `monkeypatch` fixture 來直接替換類別上的非同步方法。這樣可以確保在測試執行時，呼叫到的是我們模擬的非同步函式，而不是真實的實作。

**範例：**

假設 `TaskService` 有一個非同步方法 `get_task`，它回傳 `(bool, dict)`。

**錯誤的模擬寫法（會導致 TypeError）:**
```python
mock_task_service = AsyncMock(spec=TaskService)
mock_task_service.get_task.return_value = (True, {"task": {"id": "test"}})
# 當執行 await mock_task_service.get_task() 時，會嘗試 await 一個元組，導致錯誤。
```

**正確的模擬寫法（使用 monkeypatch）:**
```python
import pytest
from unittest.mock import AsyncMock
from src.server.services.projects.task_service import TaskService

@pytest.mark.asyncio
async def test_example_async_method_mocking(monkeypatch):
    mock_get_task = AsyncMock(return_value=(True, {"task": {"id": "test-task"}}))
    monkeypatch.setattr(TaskService, "get_task", mock_get_task)

    # 現在，當你實例化 TaskService 並呼叫 get_task 時，會呼叫到 mock_get_task
    task_service_instance = TaskService()
    success, result = await task_service_instance.get_task("some-id")

    assert success is True
    assert result["task"]["id"] == "test-task"
    mock_get_task.assert_called_once_with("some-id")
```

### 測試目錄中的 `__init__.py` 檔案

- **問題**: 在某些環境或 `pytest` 版本中，如果測試檔案位於沒有 `__init__.py` 檔案的子目錄中，`pytest` 可能無法正確發現或匯入這些測試。

- **解決方案**: 為了確保測試的穩定發現和可移植性，建議在所有包含測試檔案的子目錄中，都放置一個空的 `__init__.py` 檔案。例如，如果 `tests/agents/` 包含測試檔案，則應確保 `tests/agents/__init__.py` 存在。

### 避免框架特定依賴 (Avoiding Framework-Specific Dependencies)

- **問題**: 在核心業務邏輯或通用輔助函式中直接引入特定框架（如 FastAPI）的物件或類型，會導致程式碼與框架緊密耦合，降低可測試性和可重用性。

- **解決方案**: 盡量保持核心邏輯的框架無關性。如果需要與框架特定物件互動，應將其限制在框架層（如 API 端點）或透過抽象介面、簡單資料結構來傳遞必要資訊。例如，如果一個服務需要處理上傳的檔案，可以讓它接受檔案內容的位元組流 (`bytes`) 和檔名 (`str`)，而不是直接要求 `fastapi.UploadFile` 物件。在測試中，可以建立符合這些簡單介面的模擬物件。

## PR 提交規範
- 標題格式：[<project_name>] <標題>
- 提交前務必運行 `pnpm lint` 和 `pnpm test`。

### **Commit 訊息的特殊字元問題 (Special Characters in Commit Messages)**

- **問題**: 當使用 `git commit -m "..."` 並且訊息內容包含特殊字元（例如 `$` 或 `` ` ``）時，指令可能會因為安全限制而失敗。
- **解法**: 為了避免這個問題，建議將複雜或包含特殊字元的 commit 訊息儲存到一個暫存檔案（例如 `commit_message.txt`），然後使用 `git commit -F commit_message.txt` 來執行提交。

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