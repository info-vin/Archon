# Phase 5.1.17: Code Governance Refactoring

此計畫旨在優化專案中目前超過 400 行的兩個核心代碼檔案，分別在前端與後端進行模組化拆分，以維護程式碼的長期健康度與可讀性。

## 使用者審查要求

> [!NOTE]
> 本次重構皆為 **非破壞性重構**。後端重構不改動任何資料庫欄位或外部 API 合約，僅在 Service 層級進行類別/模組拆解；前端重構僅進行 React 元件層級的抽離，不影響任何現有版面與 CSS Tron 霓虹樣式。

## 待討論問題

* **無**：目前拆分邊界非常清晰。後端由 `SchedulerService` 繼續負責排程觸發，而將報告生成移至新服務；前端將內部 `SidebarProjectCard` 移入 `features/projects/components` 目錄中，均符合既有架構設計。

---

## 預期異動內容

### 前端重構 (Admin UI - `enduser-ui-fe`)

#### [NEW] [SidebarProjectCard.tsx](file:///Users/vincenta/GoogleKwok022/Archon/enduser-ui-fe/src/features/projects/components/SidebarProjectCard.tsx)
* 將原 `ProjectsView.tsx` 底部的 `SidebarProjectCard` 元件（約 73 行）完整移入此新檔案。
* 包含相關的 `Pin`、`ListTodo`、`Activity`、`CheckCircle2` 圖標及型別宣告與 `StatPill` 子元件的使用。

#### [MODIFY] [ProjectsView.tsx](file:///Users/vincenta/GoogleKwok022/Archon/enduser-ui-fe/src/features/projects/views/ProjectsView.tsx)
* 移除檔案底部的 `SidebarProjectCard` 元件實作。
* 引入新建立的 `SidebarProjectCard` 元件。
* 檔案行數預計從 **438 行** 降至 **約 365 行**。

---

### 後端重構 (Python Backend - `python`)

#### [NEW] [report_service.py](file:///Users/vincenta/GoogleKwok022/Archon/python/src/server/services/report_service.py)
* 新增報告服務類別 `ReportService`。
* 將以下函式從 `business.py` 中移入：
  * `gather_report_context(days: int) -> str` (數據收集邏輯)
  * `run_daily_executive_summary() -> None` (星環群聊任務發送)
  * `run_weekly_executive_summary() -> None` (Map-Reduce 任務執行)
  * `run_monthly_executive_summary() -> None` (Map-Reduce 任務執行)
* 提供單例模式執行實例 `report_service`。

#### [MODIFY] [business.py](file:///Users/vincenta/GoogleKwok022/Archon/python/src/server/services/scheduler/jobs/business.py)
* 移除上述 4 個函式的具體實作。
* 引入 `report_service`。
* 對應的 `run_daily_executive_summary` 等排程函數直接代理（Delegate）調用 `report_service`：
  ```python
  async def run_daily_executive_summary():
      from src.server.services.report_service import report_service
      await report_service.generate_daily_executive_summary()
  ```
* 檔案行數預計從 **615 行** 降至 **約 330 行**。

---

## 驗證計畫

### 自動化測試
* 執行 `make lint` 確保前端與後端靜態類型與風格完全合規（沒有 TS/Mypy/Ruff 錯誤）。
* 執行 `make test-be-fast` 確保後端重構沒有破壞 any 單元測試。

### 手動驗證
* 執行 `make twin-scout` 驗收數位雙生，確認 Alice、Bob、Charlie 角色及前端專案列表的渲染與狀態依然 100% 物理對齊。
