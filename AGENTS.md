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
- 如果只想跑單一測試，可以加上 Vitest 的 pattern：`pnpm vitest run -t "<test name>"`。
- 修復所有測試或型別錯誤，直到整個測試套件都亮綠燈。
- 移動檔案或更改 imports 後，記得跑 `pnpm lint --filter <project_name>` 確保 ESLint 和 TypeScript 規則仍然通過。
- 即使沒人要求，也請為你修改的程式碼增加或更新測試。

## PR 提交規範
- 標題格式：[<project_name>] <標題>
- 提交前務必運行 `pnpm lint` 和 `pnpm test`。```
