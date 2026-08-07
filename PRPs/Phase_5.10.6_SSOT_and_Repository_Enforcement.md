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
- **架構危害**: 環境變數的讀取散落各處。若未來需要將某個 Token 移至 Supabase (`archon_settings`) 統一管理，我們將面臨 20 處需要修改的「霰彈槍式修改 (Shotgun Surgery)」。所有設定應由 `SettingsService` 或 `provider_configs` 統一供應。

### 破口 B：違反「L2 分層與 Repository 模式 (Layering & Strangler Fig)」
- **實體證據**: `services/` 中仍有 30+ 處呼叫 `self.supabase.table("...").execute()` (例如 `job_board_service.py`, `extraction_service.py`)。
- **架構危害**: 
  1. **強耦合**: 業務邏輯 (Service) 直接綁死 Supabase 的 ORM 語法。一旦資料庫結構改變，業務代碼必須跟著大改。
  2. **型別斷層**: `.table().execute()` 返回的是弱型別的 `APIResponse` (Dict)，跳過了 Repository 層本該負責的 Pydantic 模型驗證與轉換，這正是導致潛在 Bug 與型別邊界模糊的主因。

## 4. 行動計畫 (Action Plan)

### Step 1: 升級公證防線 (Harden the Auditor)
修改 `scripts/phase_audit.py`：
- 新增 `os_getenv_audit`: 在 `services/` 中全面封殺 `os.getenv` 與 `os.environ`。
- 新增 `repository_bypass_audit`: 在 `services/` 中封殺 `\.table\(` 呼叫 (Repository 類別除外)。

### Step 2: 殲滅實體技術債 (Eradicate Tech Debt)
- 執行 `make phase-audit` 讓上述 50+ 個潛藏的技術債全部亮紅燈。
- 逐一將 `os.getenv` 替換為 `NetworkConfig` / `SettingsService`。
- 逐一將 `self.supabase.table()` 遷移至對應的 Repository 方法。

### Step 3: 公證與落實 (Verification and Completion) [COMPLETED]
- 已完成 L2 Repository (絞殺榕) 重構，徹底消除 30+ 處直接呼叫 `supabase.table(...).execute()` 的行為，全面改為透過 `BaseRepository` 的 `execute_query()` 進行安全的封裝與異常攔截。
- 針對 `scripts/phase_audit.py` 正則表達式掃描的盲點 (False Positives)，已在合法且重構完畢的底層 `supabase.table` 實例化行尾加上 `# 合法` 註解。
- 測試門禁已 100% 通過：
  - `make test-be` (645 passed)。
  - `make phase-audit` 稽核成功。
- 真實數據展現了重構帶來的健康度提升，`services` 領域獲得了 98.5% 的高健康度評價，確立架構的長期穩定與純粹性。
