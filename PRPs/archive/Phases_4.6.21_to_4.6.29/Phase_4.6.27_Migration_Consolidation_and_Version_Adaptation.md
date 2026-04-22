# Phase 4.6.27: 資料庫語意化整併與版本自適應 (Migration Consolidation)

## 1. 核心目標
將碎片化的資料庫遷移檔案 (20+) 熔煉為 5 個具備語意化結構的終極檔案，並修復 `init_db.py` 的版本硬編碼問題，達成「版本自適應」物理落地。

## 2. 物理熔煉清單 (Target: migration/0.2.2/)

### 🏗️ 01_foundation.sql
- 整合 `RESET_DB`, `core_auth`, `task_priority` ENUM, `archon_migrations` 表。
- **物理目標**：建立所有系統運行的物理基石。

### 💼 02_business_schema.sql
- 整合 CRM、專案、任務、RAG 頁面元數據、以及 5 種維度的 Embedding 實體欄位。
- **物理目標**：消除所有 `ALTER TABLE` 補丁，直接定義最終態 Schema。

### 🛡️ 03_logic_security.sql
- 整合所有 SQL Functions (混合搜尋、維度偵測) 與 RLS 安全政策。
- **物理目標**：集中管理資料庫大腦與防火牆。

### ⚙️ 04_seed_config.sql
- 整合 Agent 配置、RAG 預設值與營運配置。
- **物理目標**：確保系統啟動時具備正確的營運基因。

### 🧪 05_seed_mock.sql
- 整合所有 Mock Leads, Tasks, Blog posts。
- **物理目標**：提供具備完整外鍵關聯的測試環境。

## 3. 代碼硬化目標
- [x] **init_db.py 升級**：移除硬編碼的 `0.2.1`，實作「自動偵測最新版本目錄」邏輯。 (Done)
- [x] **版本連動更新**：更新 `archon-ui-main/.env` 為 `0.2.2`。 (Done)
- [x] **SOP 對齊**：更新 `CONTRIBUTING_tw.md` 中的手動初始化路徑。 (Done)

## 4. 物理驗證協議
1. [x] **編譯驗證**：`make dev-docker` 確保重建無誤。 (Done)
2. [x] **初始化驗證**：執行 `make db-init ARGS="--clean"`。 (Verified in Log)
3. [x] **物理對帳**：確認 0.2.2 總行數為 4000 行，且物理排除 1536 欄位以與目前的 Gemini (768) 模型對齊。 (Done)
