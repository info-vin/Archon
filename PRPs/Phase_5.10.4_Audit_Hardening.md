# Phase 5.10.4: Audit Hardening & Eradicating False Validation

## 🎯 目標 (Objective)
徹底根除系統中存在的「虛假驗證與開發 (False Validation)」問題。過去的自動化驗證腳本 (如 `init_db.py`, `verify_system.py`) 存在過多的退路 (Fallback) 與硬編碼，導致即使目錄配置錯誤或缺少實體檔案，驗證腳本仍會退回舊版給出虛假的「綠燈」。本階段旨在實作真正的快速崩潰 (Fail-Fast) 機制，確保測試與物理現實 100% 同步。

## 🛠️ 已完成的物理變更 (Completed Physical Changes)

### 1. 拔除 Fallback，導入動態解析與 Fail-Fast (`scripts/init_db.py`)
- **問題**：`get_latest_migration_version` 若找不到數字開頭的版號目錄，會靜默退回 `"0.2.3"`。
- **變更**：刪除 fallback，改為 `raise FileNotFoundError`。若目錄錯誤，強制崩潰 (Fail-Fast)。

### 2. 消除硬編碼路徑，強制動態同步 (`scripts/archive/verify_system.py`)
- **問題**：`verify_system.py` 寫死了 `WORKSPACE_DIR / "migration" / "0.2.3"`。
- **變更**：改為動態調用 `init_db.py` 的邏輯 (`get_latest_migration_version`)，確保影子資料庫與真實資料庫共用 SSOT。

### 3. 環境隔離與污染防禦 (Environment Isolation)
- **變更**：在 `init_db.py` 加入了生產環境防禦斷言。若 `SUPABASE_URL` 為生產環境 (`supabase.co`) 且未設定 `FORCE_PROD_INIT`，則 `sys.exit(1)` 強制中斷，避免測試污染正式資料庫。

### 4. 強化 CI 退出碼阻斷機制 (Exit Codes)
- **變更**：修正了 `Makefile` 內 `persona-audit` 呼叫的路徑錯誤 (指向了不存在的 `scripts/persona_smoke_test.py`，現已修復為 `scripts/archive/persona_smoke_test.py`)。確保 `make audit-qa` 能在 Docker 內部正確執行全角色巡檢。

## 🧪 物理公證結果 (Physical Audit Results)
- `make lint`: 100% 通過。
- `make test-be`: 641 項單元測試全數通過，無靜默失敗。
- `make audit-qa`:
  - 影子資料庫遷移腳本 (01 至 07) 100% 執行成功，無順序衝突。
  - Persona Audit 成功驗證 4 位人類與 5 位 AI 的 API 權限 (200 OK)。
  - LLM Content Judge 語義斷言成功。
  - DNS Leak Probe 無內部網域外流。

## 💡 廚師日誌 (Chef's Notes)
**絕對禁止虛假開發**：未來任何新增的自動化驗證腳本，皆**嚴禁**使用 `try...except` 將錯誤靜默吞噬。所有的驗證都必須是 Fail-Fast，寧可讓 CI 崩潰，也不允許在錯誤的基礎上繼續疊加開發。這是邁向自動化營運 (Auto-Ops) 的核心底線。
