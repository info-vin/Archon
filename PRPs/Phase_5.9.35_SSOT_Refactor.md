# Phase 5.9.35: SSOT 重構與全域常數收攏計畫 (SSOT Refactor & Constants Hub)

## 目標 (Goal)
針對 `make phase-audit` 所揭露的大量 SSOT 違規（主要為 RBAC 角色與狀態字串的陣列硬編碼），我們將把四散各處的魔法字串 (Magic Strings) 統一收攏至 `shared_constants.py`，並透過重構 `auth/dependencies.py` 與各 API 路由，消除維護死角，最後透過 `# 合法` 註解處理稽核工具的假警報。

## 需要使用者的審查 (User Review Required)
> [!IMPORTANT]
> **數據分析報告：關於改動廣度與依賴注入的風險**
> 
> 根據全域掃描 `grep -rE "if .*role.* in \[" python/src/server/api_routes/`，我們在 API 路由中找到了 **8 處** 角色硬編碼。
> 經過深入比對原始碼，我發現這 8 處**並非單純的端點進入許可證**，而是與複雜的業務邏輯深度綁定。例如在 `projects/ops.py` 中：
> 1. `if u_role in ["system_admin", "admin", "manager"]:`：這決定了使用者只能看到自己負責的任務，還是能看到全公司任務，並非阻擋存取。
> 2. `if u_role not in ["system_admin", "admin"] and p.get("department") != u_dept:`：這牽涉到跨部門派發任務的業務規則。
>
> **結論**：如果我們強行採用「選項 B」(將權限驗證移到 API 宣告 `Depends(verify_roles(...))`)，將會發生大規模的業務邏輯損壞 (Regression)，因為普通員工會直接被 HTTP 403 阻擋在門外，導致無法取得他們自己的任務！
>
> 因此，我們將**果斷放棄選項 B，全數採用「選項 A」**：保持現有業務邏輯判斷，僅將字串陣列替換為 `[RoleEnum.ADMIN, RoleEnum.SYSTEM_ADMIN]`。這樣既能解決 SSOT 違規，又能 100% 保障業務邏輯的穩定性。

## 預期修改內容 (Proposed Changes)

---
### 1. 建立全域常數中心 (Constants Hub)
我們將使用既有的 `shared_constants.py` 作為核心，不再新增檔案。

#### [MODIFY] [shared_constants.py](file:///Users/vincenta/GoogleKwok022/Archon/python/src/server/services/shared_constants.py)
- 新增 `RoleEnum (StrEnum)`：收錄 `admin`, `system_admin`, `manager`, `marketing`, `sales`, `employee`, `member` 等。
- 新增 `StatusEnum (StrEnum)`：收錄 `draft`, `changes_requested`, `published`, `starting`, `running`, `crawling`, `completed` 等。

---
### 2. 重構 RBAC 依賴與 API (Middleware & Routes)
根除陣列字串，改用 `RoleEnum`。因為稽核腳本的正規表達式只捕捉「字串陣列 (`["admin"]`)」，改用 Enum 陣列 (`[RoleEnum.ADMIN]`) 即可自然通過稽核並達到強型別安全。

#### [MODIFY] [auth/dependencies.py](file:///Users/vincenta/GoogleKwok022/Archon/python/src/server/auth/dependencies.py)
- 將 `get_current_admin`, `verify_admin_role`, `verify_manager_role` 中的 `["admin", "system_admin"]` 替換為 `[RoleEnum.ADMIN, RoleEnum.SYSTEM_ADMIN]`。

#### [MODIFY] 各大 API 路由模組
替換所有 `if role not in ["..."]` 為 Enum。影響檔案包含：
- `api_routes/admin_api.py`
- `api_routes/marketing_api.py`
- `api_routes/progress_api.py` (替換 StatusEnum)
- `api_routes/projects/ops.py`
- `api_routes/projects/versioning.py`

---
### 3. 處理稽核工具的假警報 (False Positives Handling)
針對使用者指示：「合法就註解 "合法"」。

#### [MODIFY] [phase_audit.py](file:///Users/vincenta/GoogleKwok022/Archon/scripts/phase_audit.py)
- 在檔案讀取迴圈中加入：`if "# 合法" in line: continue`。只要該行帶有 `# 合法` 的註解，稽核工具就會直接忽略跳過。

#### [MODIFY] 合法硬編碼檔案
在以下檔案中合法使用的網址或字串陣列旁加上 `# 合法`，使其免除 SSOT 警告：
- `crawling/clients/job104_client.py` (104 網址)
- `api_routes/settings_api.py` (`target_keys = ["GOOGLE_API_KEY"...]`)
- `extraction_api.py` (註解中的網址範例)
- `ollama/discovery/...` (HuggingFace/Ollama 能力標籤)

## 驗證計畫 (Verification Plan)

### 自動化測試與品質門禁 (QA Gates)
- **`make lint-be` 及 `mypy`**：確保 Enum 的引用完全符合型別安全。
- **`make test-be`**：執行測試套件，確保 RBAC 替換為 Enum 後，API 的權限阻斷 (403 Forbidden) 行為沒有被破壞。
- **`make phase-audit`**：執行稽核，預期將看到「Hardcoded String Set Literal (SSOT Violation)」與「Hardcoded HTTP URL/Port」的違規數量**歸零**。

### 手動驗證
- 檢查 Terminal 輸出，確認 `# 合法` 註解確實能成功屏蔽特定的警報。
