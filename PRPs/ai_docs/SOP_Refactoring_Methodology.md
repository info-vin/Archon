# SOP：代碼重構與邏輯剝離方法論 (Code Refactoring Methodology)

> **制定者**: DevBot (經由實戰重構 stats_api.py 總結)
> **目的**: 指導 DevBot 如何系統性地將「肥控制器」轉換為「瘦控制器 + 強服務層」。

## 1. 識別階段 (Identification)
*   **觸發條件**: 任何超過 **300 行** 的 API 路由文件 (`_api.py`)。
*   **拆分對象**:
    *   直接調用 `supabase.table()...execute()` 的代碼區塊。
    *   包含 `datetime`, `timedelta` 運算的聚合邏輯。
    *   包含複雜 `math` 或數據分數計算的函式。

## 2. 剝離步驟 (Extraction Workflow)
1.  **建立 Service**: 在 `src/server/services/` 建立對應的 `_service.py` 檔案。
2.  **方法遷移**:
    *   將計算型函式（如 `calculate_ai_score`）改為 `static method` 或 Service 方法。
    *   將數據庫聚合改為 Service 實例方法，並透過 `self.supabase` 進行操作。
3.  **依賴注入**: 在 API 文件中實例化 Service (`stats_service = StatsService()`)。
4.  **接口簡化**: 將 API 端點簡化為單行 Service 調用。

## 3. 品質與 Token 核算 (Quality & Accounting)
*   **Token 紀錄**: 每個遷移到 Service 的 AI 相關方法，必須確保包含 `TokenUsageService.log_usage` 的非同步調用。
*   **異常處理**: Service 層拋出明確的商業異常，API 層負責捕捉並轉換為 `HTTPException`。

## 4. 驗證序列 (Verification Sequence)
DevBot 必須理解：**「綠色的 Backend 測試不代表全系統安全」**。重構後必須完成以下「物理核對」：

### 【全量品質檢查清單】
1.  **靜態掃描**: `make lint` (必須包含 FE/BE 雙端)。
2.  **前端單元測試**: `cd enduser-ui-fe && pnpm run test:unit` (確保行銷/統計展示無誤)。
3.  **後端回歸測試**: `make test-be` (確保邏輯 1:1 遷移)。
4.  **管理端聯動測試**: `cd archon-ui-main && pnpm test` (確保 Agent 調度前端穩定)。

## 5. 修復級別與晉升條件 (Refactoring Levels & Promotion Policy)

為了防止「過度自信」造成的破壞，所有 Agent（DevBot, MarketBot, Librarian）均須遵守 Poisson 分佈晉升模型：

| 級別 | 類別 | 範圍 | 晉升要求 (累積成功次數) |
| :--- | :--- | :--- | :--- |
| **L1** | **微手術** | Lint 錯誤、單行修復。 | **起點 (> 300 次)** |
| **L2** | **小重構** | 300 行以下函式修正。 | **L1 達標 + 120 次 (420)** |
| **L3** | **邏輯剝離** | SQL 搬移至 Service。 | **L2 達標 + 80 次 (500)** |
| **L4** | **接口調整** | 修改 API 參數或結構。 | **L3 達標 + 50 次 (550)** |
| **L5** | **依賴解耦** | 修復循環引用與依賴。 | **L4 達標 + 30 次 (580)** |
| **L6** | **服務演進** | 跨模組數據流變更。 | **L5 達標 + 20 次 (600)** |
| **L7** | **核心變革** | Base 基座或安全原則。 | **David Howard 手動授權** |

> **注意**: 任何一次「修復後導致 Regression」的紀錄，將會扣除該級別 10 次成功積分。

## 6. 實戰案例：Stats API (2026-02-16)
*   **成果**: `stats_api.py` 從 832 行減少至 150 行。
*   **優勢**: 邏輯集中在 `stats_service.py`，大幅提升了數據分數計算的可測試性。
