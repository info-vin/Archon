---
name: "PRP 5.1: Admin Capability & Identity Synchronization Fixes (管理員權限與身份同步修復計畫)"
description: "解決管理員 (Admin) 權限不全、無法變更使用者角色、以及將假資料身份 (如 Alice) 實體化為真實帳號的修復任務。"
---

## 原始故事 (Original Story)

**賦予管理員真權力 (Empowering the Admin):**
在 Phase 5 的架構遷移中，我們發現管理員雖然能進入管理面板，但卻面臨「看得到動不了」的窘境。具體表現為：無法變更使用者角色 (API 500)、無法編輯非本人撰寫的部落格。同時，為了讓系統能進行真實測試，我們需要一個標準流程將 `alice@archon.com` 等假資料身份轉化為可登入的真實帳號。

## 故事元資料 (Story Metadata)

**故事類型 (Story Type)**: Fix & Alignment (修復與對齊)
**預估複雜度 (Estimated Complexity)**: Small (低)
**主要受影響系統 (Primary Systems Affected)**: `archon-server` (settings_api, blog_api), `enduser-ui-fe` (Blog permissions)

---

## 實作任務 (IMPLEMENTATION TASKS)

### Phase 1: 管理員權限補強 (Admin Capability Reinforcement)

#### 1.1 修復 Admin 變更角色權限 (Fix Admin Role Update):
- **問題**: 呼叫 `PUT /api/users/{id}` 時，因為 Pydantic 模型缺少 `role` 欄位導致失敗。
- **行動**:
    - 在 `python/src/server/api_routes/settings_api.py` 中，建立 `AdminUserProfileUpdate` 模型並加入 `role` 欄位。
    - 更新 `update_user_profile_admin` 端點以接受此新模型。
- **驗證**: Admin 帳號修改其他使用者的 Role 為 "manager" 後，資料庫顯示變更。

#### 1.2 管理員全域編輯 Blog 權限 (Admin Blog Override):
- **問題**: 部落格 API 或 UI 限制了只有作者本人才能編輯/刪除文章。
- **行動**:
    - **後端**: 檢查 `blog_api.py`，確保 `system_admin` 角色在執行 PUT/DELETE 時可跳過擁有者檢查 (Ownership Check)。
    - **前端**: 檢查 `BlogDetailPage.tsx` 或編輯按鈕渲染邏輯，若當前使用者是 Admin，應顯示「編輯」按鈕。
- **驗證**: Admin 登入後，可以編輯作者為 "Bob" 的文章。

### Phase 2: 身份實體化 (Identity Migration)

#### 2.1 Alice 帳號實體化 SOP (Alice Implementation):
- **目標**: 將 `alice@archon.com` 從 SQL Seed 產生的虛擬 Profile 轉為真實可登入帳號。
- **步驟**:
    1.  Admin 登入系統 (5173)。
    2.  進入 **Admin Panel** > **Create User**。
    3.  輸入 Email: `alice@archon.com` 與密碼。
    4.  系統將呼叫後端 `adminCreateUser` API，在 Supabase Auth 建立帳號並與現有 Profile 連結。
- **驗證**: 登出 Admin 後，使用 `alice@archon.com` 成功登入 Dashboard。

---

## COMPLETION CHECKLIST (完成檢查清單)

- [x] **Role Update**: `settings_api.py` 支援 `role` 欄位更新。
- [x] **Blog Admin Access**: 管理員可編輯/刪除任何人的文章 (透過修復 `rbac_service.py`)。
- [x] **Alice Migration**: `alice@archon.com` 已透過 Admin Panel 成功創建，並驗證可登入與編輯個人檔案。 (流程：Admin 先新增帳號 -> Alice 登入 -> 變更資料)

---

## ✅ 驗收標準 (Acceptance Criteria)

1.  **管理功能完整性**: 管理員在 UI 上的權限變更操作不再觸發 500 錯誤。
2.  **安全性**: `role` 欄位的變更僅限於帶有 `system_admin` 或 `admin` 標頭的請求。
3.  **無感遷移**: 實體化 Alice 帳號時，其原有的 Profile 資料 (如頭像、姓名) 應被保留。
