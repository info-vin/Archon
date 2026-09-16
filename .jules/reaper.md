## 2025-05-24 - [工具誤判與核心元件]
**學習心得：** ts-prune 會將 `index.ts` 中的匯出標示為未使用（如果沒有其他模組透過 index 引用），但該元件實際上可能在同一目錄下被其他檔案直接匯入並使用（例如 `KnowledgeInspector.tsx` 直接匯入同目錄的 `ContentViewer` 並作為核心 UI 渲染）。
**行動：** 在移除被靜態工具標示為未使用的匯出時，必須優先確認是否有直接檔案層級的引用。若無法確定是否為展示或核心元件，應遵循「寧可留著，也不要誤刪 (When in doubt, leave it out)」原則。

## 2025-05-24 - [ts-prune 誤判與集中匯出模式]
**學習心得：**
1. 靜態分析工具 (如 ts-prune) 常會誤報。例如標記 UI components 或 context providers (如 AuthProvider) 為未使用，但這些通常在根目錄或版面配置檔 (如 MainLayout.tsx) 被使用，只是工具可能未正確解析。
2. 許多檔案透過 `index.ts` 匯出 (re-export)，必須追蹤匯出檔案是否被引用。例如 `workbench/index.ts` 匯出了所有 workbench 元件，而 `ContentWorkbench.tsx` 引用了這些匯出；`services/api/index.ts` 也是類似情況，因此不能輕易刪除。
**行動：**
在判定殭屍代碼前，一定要用 `grep -rn '目標名稱' src/` 搜尋所有可能被使用的地方。如果看到 components 被引用，或者 context 被使用，就不要刪除。寧可留著，也不要誤刪。

## 2025-05-24 - [Python 參數 unused 問題與 FastAPI query/dependency]
**學習心得：** 在使用 vulture 等工具時，FastAPI 的路徑操作函式中定義的 Query 或 Dependency 參數，即使在函數主體內沒有直接被當作變數使用，它們也提供了 API 文件的 Schema 以及 request 驗證機制。這些不能被直接移除，否則會破壞 API 介面。同時，對於繼承或實現某個介面的方法中，為了維持簽章一致性而未被使用的參數，這類情況也屬於誤報。
**行動：** 對於 API endpoints（有 FastAPI 裝飾器的函式）以及為了介面一致性保留的參數，如果被標記為 unused，應該將參數名稱加上前綴 `_`，並在需要時使用 `alias` 來維持外部接口，例如：`_include_capabilities: bool = Query(..., alias="include_capabilities")`。這能消除 vulture 警告，同時不改變 API 的實際輸入輸出定義，亦不違反寧可留著不要誤刪的原則。
