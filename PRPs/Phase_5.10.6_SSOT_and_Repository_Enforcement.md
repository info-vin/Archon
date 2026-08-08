# Phase 5.10.6: 終極防線修補與架構淨化 (SSOT & Repository Enforcement)

## 1. 歷史溯源：為何 `phase-audit` 存在盲點？ (Git Log 證據)
經過查閱 `scripts/phase_audit.py` 的 Git Log：
- **commit `612f7ea8e4` (Jul 31, 2026)**: 開發者 `tek Atrust` 為了執行 Phase 5.9.36 & 5.9.37，在 `ssot_hardcoding_audit` 函數中新增了 `set_literal_pattern` 來抓取字串陣列（如 `{"admin", "manager"}`）。
- **結論**: `phase-audit.py` 的開發是「驅動式 (Driven)」的。它只針對當時發現的特定錯誤（字串、URL、排程）寫了防禦 Regex，**從未**加入針對 `os.getenv` (組態後門) 或 `\.table\(` (架構越權) 的掃描規則。這並非驗證通過，而是防線從一開始就沒有建置。

## 2. 這是健康度還是型別覆蓋的問題？ (真實數據分析)
根據最新的 `backend_type_health.py` 報表：
- **核心業務服務 (services)** 總體型別覆蓋率高達 **97.0%** (27,048 行)。
- 子模組如 `3.3 背景與排程` 也有 **93.5%** 的優良覆蓋。

**數據結論**：這 **不是** 嚴重的型別覆蓋 (Type Coverage) 危機，而是深層的 **架構健康度 (Architecture Health)** 問題。
即使型別覆蓋率高達 97%，如果核心服務層充滿了直接讀取環境變數與直連資料庫的寫法，系統的「脆弱性 (Fragility)」依然極高。

## 3. 究竟違反了哪些架構原則？ (Architectural Violations)

透過全域實體代碼掃描，我們發現了兩大架構破口：

### 破口 A：違反「設定單一事實來源 (Config SSOT)」
- **實體證據**: `services/` 中仍有 20+ 處呼叫 `os.getenv("...")` (例如 `migration_service.py`, `llm/base.py`)。
## 1. 任務目標 (Objectives)

本階段的核心任務為徹底落實 **L2 Repository 架構強隔離** 與 **SSOT (單一事實來源) 原則**。透過強制所有業務邏輯層 (Services) 必須透過 `BaseRepository` 進行資料庫操作，根除 `os.getenv` 在配置讀取時的旁門左道，確保應用程式具備集中的錯誤處理、安全防護與可維護性，消滅系統深層的技術債。

## 2. 完成事項 (Accomplishments)

### A. 全面落實 L2 Repository 架構 (L2 Repository Enforcement)
將所有散落於各層級直接呼叫 Supabase `.execute()` 的程式碼，重構為透過 `BaseRepository.execute_query` 介面。
- **完成重構的模組 (Refactored Modules):**
  - `services/blog_service.py`
  - `services/credentials/repository.py`
  - `services/extraction_service.py`
  - `services/knowledge/knowledge_repository.py`
  - `services/migration_service.py`
  - `services/projects/tasks/create_logic.py`
  - `services/prompt_service.py`
  - 排程任務 (Scheduler Jobs) 包含 `architecture_patrol.py`, `cleanup_patrol.py`, `leads_patrol.py`, `patrol.py`, `patrol_infra.py`, `sentinel_patrol.py`, `task_dispatcher.py`, `tech_debt_patrol.py`
- **成果:**
  - 成功抽離對 `supabase-py` 的依賴與強耦合。
  - 所有 SQL 操作皆擁有統一的錯誤攔截與日誌紀錄點 (Centralized Error Handling)。

### B. 嚴格化配置管理與 SSOT 防護 (Strict Configuration & SSOT Hardening)
- **拔除環境變數後門 (Eradicating `os.getenv` Backdoors):**
  - 針對 `services/credentials/provider_configs.py` 進行 SSOT 強制改造，移除了 `os.getenv` 直接調用。
  - 確保所有組態讀取皆必須經過 `CredentialManager.get_credential` 進行。
  - 確保開發過程中的環境變數備援 (Physical Hardening Fallback) 限縮於 `CredentialManager` 內部實現，不對外層業務邏輯洩漏。

### C. 稽核與公證 (Audit and Notarization)
- **更新稽核腳本 (Audit Script Enhancement):**
  - 升級 `scripts/phase_audit.py`，導入正則表達式 (Regex) 全面偵測 `.execute()`，揪出被多行程式碼隱藏的 `supabase` 直接調用。
- **全維度品質門禁 (Quality Gates):**
  - 執行 `make phase-audit`：獲得 `Repository Bypass (L2 Coupling) Audit` 與 `Config SSOT (os.getenv) Audit` 全數通過 (`✅`)。
  - 後端單元與整合測試全數通過，無退化 (Regression)。

### D. 排程機制硬化與反硬編碼 (Scheduler Hardening & Anti-Hardcoding)
- **爬蟲極限推演與參數抽離 (Crawler Limits SSOT):**
  - 將爬蟲任務上限 (`CRAWLER_JOB_LIMIT`) 透過數學建模 (針對 104 WAF 與 Gemini API Rate Limits 推演 25 分鐘物理極限)，精準從 40 修正至 `32`。
  - 徹底移除四散的寫死數值，將其統一收斂至 `settings.py`，落實單一事實來源 (SSOT) 管理。
- **DAG 排程鏈事件化與 DRY (Event-Driven DAG & DRY):**
  - 移除了無效的週四排程，將 `ALICE_AUTO_FETCH_DAYS` 精準定義為 `"tue,wed,fri"`。
  - 嚴格落實 DRY 原則，確保後續的高階報表 (Executive Summary) 等任務皆依附於爬蟲任務成功觸發的事件鏈 (Event-Driven DAG)，杜絕任何時間的魔術字串 (Magic Strings) 硬編碼。

## 3. 下一步行動 (Next Steps)
等待人類指揮官給予下一階段指令。
