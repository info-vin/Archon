# Phase 5.9.38: Report Enhancements & SSOT Data Alignment

## 執行摘要 (Executive Summary)
針對「星環群聊週報/月報」的通知機制、資料結構（表格與定義）以及 Token 拆分的物理對齊，進行架構上的優化。完全遵循 SSOT 與 DRY 原則，不引入臃腫依賴。

---

## 1. Telegram 與 PDF 通知機制 (Notification Architecture)

> [!WARNING]
> **架構與依賴風險評估**：
> 1. **PDF 格式**：Python 原生不支援 Markdown 轉 PDF。若要實作，需引入 `WeasyPrint` 或 `pdfkit`，這會強制在 Docker 容器內安裝巨大的底層依賴（如 `cairo`, `pango`, `wkhtmltopdf`），極大程度破壞當前的輕量化微服務架構。
> 2. **Telegram 限制**：Telegram 單則訊息有 4096 字元的限制，直接塞入完整的星環群聊報告極易引發 HTTP 400 截斷錯誤。

### 實作設計 (Proposed Design)
*   **拒絕 PDF 依賴**：保持雲端原生的純淨度，不引入 PDF 渲染引擎。
*   **精簡導流通知 (Lightweight Routing)**：在 `report_service.py` 成功建立週報/月報 `archon_tasks` 任務後，呼叫現有的 `telegram_service.send_message` 發送「精簡卡片通知」。
*   **通知內容格式**：
    ```markdown
    🚨 **[Archon 系統通知] 星環週報已產出**
    * 日期區間: 2026-07-20 ~ 2026-07-27
    * 總花費成本: $0.0079 USD
    * 狀態: 已指派給 Charlie
    👉 請登入 Admin UI 查看詳細數據與表格：[Task UUID 連結]
    ```

---

## 2. 優化 `report_service.py` 中的 Prompt

> [!IMPORTANT]
> **SSOT 提示詞工程優化**：為了解決報告中「缺乏數據表格」與「缺乏名詞定義」的問題，需修改預設的系統 Prompt，強制 LLM (Charlie & Bob) 的輸出格式。

### 實作設計 (Proposed Design)
修改 `report_service.py` 中 `generate_weekly_executive_summary`、`generate_monthly_executive_summary` 與每日摘要的 `default_prompt`。

**新增強制約束條款 (Constraints)**：
1. **表格化強制 (Table Enforcement)**：`「所有的商業行銷數據、Token成本花費、系統警示數量，皆必須使用 Markdown 表格進行結構化對照，禁止純文字描述。」`
2. **物理定義強制 (Definition Enforcement)**：`「凡在報告中提出任何比率、轉換率或百分比數據，必須在該數據後方使用括號清楚標示『(分子/分母)』的計算來源與名詞定義，確保數據無歧義。」`

---

## 3. Input / Output Token 分拆 (Token Split SSOT)

> [!TIP]
> **物理現實查核**：經檢視 `report_service.py` 的 `_get_token_context`，底層實際上**已經分拆了 Input 與 Output Tokens** 餵給群聊。報告沒有印出來，純粹是因為舊 Prompt 將其過度濃縮。

### 實作設計 (Proposed Design)
為了貫徹 SSOT，確保資料庫、日誌與報告三向連動的絕對對齊，採取「全域統一分拆」策略：

1. **報告層 (Report Level) - 統一分拆**：
   不需修改底層邏輯。依賴第 2 點的 Prompt 優化生效後，日報、週報、月報將會「統一」以表格印出完整的 Input/Output/Total 拆分視圖。
2. **巡邏日誌層 (Sentinel Level) - 補齊 SSOT**：
   修改 `python/src/server/services/scheduler/jobs/sentinel_patrol.py` 中的 `analyze_token_usage()`。
   *   **目前缺失**：寫入 `archon_logs` 供查閱的 `details` JSON 中，只有加總的 `total_tokens`。
   *   **修改內容**：將 `details` 擴充，把 `input_tokens` 與 `output_tokens` 獨立存入 JSON 結構中，徹底拔除日誌層的數據模糊地帶。

---

## 用戶審查與下一步 (Next Steps)
請長官審閱上述計畫：
1. **捨棄 PDF，改採 Telegram 導流短通知**的輕量化做法是否同意？
2. 若無異議，我將開始執行上述三點修改，並為您重新跑一次週報測試！

## 4. 進度更新 (Progress Update: 2026-08-01)
> [!NOTE]
> 根據使用者的嚴格 Code Review 與指導，我們發現了 `report_service.py` 存在深層的 DRY 違規，以及 `telegram_service.py` 的 SSOT 斷層。今日已完成以下徹底的重構與修復：

1. **SSOT URL 物理對齊**: 
   - 移除 `patrol_infra.py` 與 `report_service.py` 中硬編碼的 Vercel 網址，統一收斂至 `settings.py` 的 `NetworkConfig().frontend_url` (`https://archon-enduser.vercel.app`)。
2. **修復 Telegram 設定斷層**:
   - `telegram_service.py` 不再直接呼叫 `os.getenv`，而是透過 `SettingsService` 動態讀取資料庫中的 `NotificationConfig`，確保 Admin UI 的修改能即時生效。
3. **Deep DRY 實踐**:
   - 將 `report_service.py` 內部超過 40 行的重複派發、日期計算、ID 查詢與日誌紀錄邏輯，徹底抽取為共用方法 `_create_summary_task_and_log`。
   - 所有硬編碼的繁體中文 Prompt (包含 `REPORT_CONTEXT_DEFAULT` 與各類摘要預設文本) 皆已 100% 移至 `pm_prompts.py` 集中管理。
4. **公證與驗證**:
   - `mypy` 靜態型別檢查 0 錯誤。
   - 修正相關的 Pytest 測試斷言後，620 項後端測試全數綠燈通過。
