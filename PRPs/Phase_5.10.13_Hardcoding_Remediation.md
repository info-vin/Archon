# [Phase 5.10.13] 系統去硬編碼 (Hardcoding Remediation) 與稽核網硬化計畫

這份計畫基於最新的 Git Log 開發紀錄 (`85384a70`, `f12aa5f2`, `0079d099`) 與實體代碼分析而生成，並嚴格遵循團隊的架構鐵律。

## 🔍 問題根源分析 (Root Cause Analysis: 為何 phase-audit 會漏抓？)
經過嚴格的實體對帳，我們發現 `make phase-audit` 存在以下死角：

1. **前端漏掃與 Port 鐵律忽略**：
   - 根據【絕對鐵律】，`enduser-ui-fe` (Port 5173) 是 Admin UI，而 `archon-ui-main` (Port 3737) 是 Enduser UI。然而 `scripts/phase_audit.py` 內的 `ssot_hardcoding_audit` 的 `target_dirs` 完全沒有包含這兩個前端目錄，導致 `ManageMemberModal.tsx` 等檔案內的 `ROLE_DISPLAY_NAMES` 硬編碼未被發現。
2. **正則表示式破綻 (Regex Flaws)**：
   - `url_pattern` 僅攔截 `http://` 與 `https://`，所以 `system_api.py` 的 Socket IP (`8.8.8.8`) 被漏掃。
   - `set_literal_pattern` (字串陣列偵測) 不包含斜線 `/` 與句點 `.`，因此 `seeding_service.py` 內的 `POSSIBLE_DIRS` 完美躲過。
   - 針對「整數魔法數字」(`latency_ms: 150`, `retry_count < 3`) 完全沒有稽核規則涵蓋。

## ⚠️ 關於 Alice Johnson 判斷式的勘誤 (Git Log 對帳)
- **修正**：在先前的分析中，我誤判了 `TeamMemberCard.tsx` 內 `member.name === 'Alice Johnson'` 是錯誤的硬編碼。
- **證據**：經過比對 Git Log (Commit `0079d09969`)，該行程式碼附有註解 `/* Inject SOP Viewer specifically for Alice's workflow context */`，且在 Phase 5.3 的規劃中，Alice Johnson 被指定負責 Phase 4.2 業務功能測試，因此這個 SOP 按鈕是專為她的 Workflow Context 刻意注入的。**這並非 Bug，而是符合設計意圖的實作，因此本次修復將不會更動該邏輯。**

---

## 🛠️ Proposed Changes (修復計畫)

### 1. 前端架構重構 (Frontend DRY, 針對 enduser-ui-fe 5173)
將角色名稱的格式化抽離為全域共享，解決 `ManageMemberModal.tsx` 與 `TeamMemberCard.tsx` 重複定義的問題。
*注意：此重構僅限於 Admin UI (`enduser-ui-fe`，Port 5173)，與 Enduser UI (`archon-ui-main`，Port 3737) 無關，避免改 A 壞 B。*

#### [MODIFY] `enduser-ui-fe/src/types/index.ts`
- **新增**：將 `ROLE_DISPLAY_NAMES` 字典宣告並匯出，集中所有角色名稱的對應關係。

#### [MODIFY] `enduser-ui-fe/src/features/team/components/ManageMemberModal.tsx` 及 `TeamMemberCard.tsx`
- **刪除**：原先宣告在檔案頂端的 `ROLE_DISPLAY_NAMES` 字典。
- **引入**：改從 `@/types` 引入 `ROLE_DISPLAY_NAMES`。

### 2. 後端去硬編碼 (Backend Decoupling) 與 測試連動 (Test Synchronization)

#### [MODIFY] `python/src/server/api_routes/system_api.py`
- 將 Socket 網路連線偵測的 `8.8.8.8` 抽離，改由環境變數讀取。
- 移除 `TARGET_MODELS` 與 `latency_ms: 150` 的硬編碼，改為從資料庫或 SSOT 模組動態獲取。
- **[NEW] 測試連動**：重新建立 `python/tests/api_routes/test_system_api.py` (注意：為了遵循新的測試目錄結構，我們將其建立在 `python/tests/api_routes/`，而不是舊的 `python/tests/server/api_routes/`)，並使用 `unittest.mock` 攔截網路請求，確保測試覆蓋新的 Fallback 邏輯。

#### [MODIFY] `python/src/server/services/system/seeding_service.py`
- 將 `.md` 與 `.txt` 以及 `knowledge_type="technical"` 抽離為常數。
- **測試連動**：建立或更新 `python/tests/services/system/test_seeding_service.py`，補上對這些常數的 Mock 驗證。

#### [MODIFY] `python/src/server/services/system/worker_service.py`
- 將重試次數 `3`、`tier="lite"` 以及建構子的 `poll_interval_seconds` 抽離至設定檔 (SettingsService)。
- **測試連動**：更新 `python/tests/services/system/test_worker_service.py`，確保 `global_throttler.wait_for_capacity` 的呼叫會使用從 Mock Settings 動態取得的 Tier 進行斷言 (Assert)。

### 3. 自動化稽核防禦網硬化 (Phase Audit Hardening)

#### [MODIFY] `scripts/phase_audit.py`
- **擴展目標目錄**：將 Admin UI (`enduser-ui-fe/src`) 與 Enduser UI (`archon-ui-main/src`) 加入 `ssot_hardcoding_audit` 的掃描範圍。
- **補強 Regex**：更新 `set_literal_pattern` 支援路徑字元，並加入 IP 正則表達式 (`\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}`)，徹底消除掃描死角。

---

## ✅ Verification Plan
1. **靜態分析**：執行硬化後的 `make phase-audit`，確保它能成功抓出我們預期的違規，然後在去硬編碼後能全數亮綠燈。
2. **測試公證 (安全執行)**：
   - 後端：執行 `make test-be`，確保後端 API 測試通過。
   - 前端：**【嚴禁使用 `make test-fe` 以免清空資料庫】**，將改為進入特定目錄執行安全的單元測試指令（例如 `cd enduser-ui-fe && npm run test`），以確保前端的改動不會破壞渲染。
