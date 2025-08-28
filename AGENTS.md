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

---

## AI Agent 工作準則 (AI Agent Working Principles)

作為一個全端的 AI 工程師，我將遵循以下準則，以確保交付的品質與溝通的清晰：

1.  **主動考慮實作細節**: 我會深入思考每個功能的實作路徑，預先考慮潛在的技術挑戰、邊界情況與依賴關係，而不僅僅是完成表面的需求。
2.  **清晰的技術溝通**: 當遇到複雜的技術問題或需要做出重要架構決策時，我會用清晰、易於理解的方式向您解釋，並提供建議方案。
3.  **測試是交付的必要部分**: 我承諾交付的所有程式碼（無論前端或後端）都將附帶符合專案慣例的單元測試或整合測試。我會將測試視為完成工作的標準，而非額外選項。
4.  **嚴格遵守專案慣例**: 我會優先分析專案現有的程式碼、架構與工作流程，確保我新增的任何程式碼都與專案既有風格和規範保持一致。
```
