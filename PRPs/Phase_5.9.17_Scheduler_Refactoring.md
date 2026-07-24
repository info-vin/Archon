# Phase 5.9.17: 排程系統重構與動態時區錨點 (Scheduler Refactoring & Dynamic Time Anchor)

## 📌 核心目標 (Core Objectives)
1. **破除單體化危機 (De-Monolithization)**：將 `scheduler_service.py` 透過泛型重構 (DRY)，在不增加檔案數量的情況下，將長度壓縮至 250 行內，避免超過 400 行的系統紅線。
2. **動態時區錨點 (Dynamic Time Anchor)**：消滅所有排程時間的硬編碼。全面讀取 `HF_SLEEP_START` 環境變數（台灣時間 CST），透過時間運算動態決定大型報表任務的觸發時機。
3. **任務分流與相依性控制 (Task Isolation)**：將雙週/每週的大型審計任務精準避開每日早晨 (07:00) 的尖峰時段。

---

## 🛠️ 實作細節 (Implementation Details)

### 1. DRY 泛型重構 (`scheduler_service.py`)
- **問題**：原先存在 `_schedule_stateful_daily`, `weekly`, `monthly`, `biweekly` 四個高度重複的樣板函數，導致代碼臃腫。
- **解法**：統一重構為單一 `_schedule_stateful_job` 泛型方法，將檢查條件 (`check_func`) 與排程觸發器 (`trigger`) 參數化。
- **成效**：成功將檔案總行數從 **~371 行** 縮減至 **232 行**，降幅達 37%。

### 2. 動態時推演算法 (`_parse_dynamic_hf_time`)
- 系統現在會讀取 `os.getenv("HF_SLEEP_START", "20:18")` 並將其解析為時、分。
- 透過動態計算 `offset_hours`，自動扣除時數並處理換日邏輯，確保任務永遠在 Hugging Face 進入休眠前的安全區間執行：
  - **戰情週報 (`weekly_executive_summary`)**：設定為 `HF_SLEEP_START - 3h` (預設 17:18)。
  - **架構健康度 (`architecture_health_audit`)**：設定為 `HF_SLEEP_START - 1h` (預設 19:18)。

### 3. 架構健康度巡檢 (`architecture_patrol.py`)
- 建立了全新的 `architecture_patrol.py` 任務。
- **SSOT 與模組重用**：不再造新輪子，直接透過動態載入 `/scripts/backend_type_health.py` 並呼叫其 Markdown 生成函數，確保與 `make audit-qa` 的標準 100% 物理對齊。
- 巡檢完成後會自動產生工單 (Task)，並指派給 DevBot，讓人類指揮官與 AI 工程師都能無縫審閱。

### 4. 週期任務集中化
所有低相依性的「雙週系統維護任務」皆統一集中於 **週末下午 14:00 (台灣時間)** 執行，完美錯開平日負載：
- `infrastructure_audit`: 週六 14:00 (只寫入日誌，無工單)
- `api_deprecation_scan`: 週六 14:05 (交給 Librarian，產生工單)
- `tech_debt_audit`: 週日 14:00 (條件產生 DevBot 工單)
- `ssot_audit`: 週日 14:05 (條件產生 DevBot 工單)

---

## ✅ 品質公證 (Quality Assurance)
- **Lint 驗證**: `make lint-be` 執行 261 個模組審計，0 錯誤通過 (包含 PEP 8 E701 修正)。
- **單元測試**: `make test-be` 執行 612 項測試全數通過，包含 `test_scheduler_service.py` 核心邏輯。
- **無造新輪子 (No Reinventing)**：取消原本建立 `state_manager.py` 的構想，以 DRY 守則直接在檔案內部完成瘦身。
