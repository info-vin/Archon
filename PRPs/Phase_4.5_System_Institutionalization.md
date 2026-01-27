---
name: "Phase 4.5: System Institutionalization (系統制度化)"
description: |
  A strict refactoring phase to pay off the "Speed Debt" incurred during Phase 4.4.
  Focuses on normalizing UIs, converting scripts into proper APIs, and standardizing test suites.
  (這是一個嚴格的重構階段，旨在償還 Phase 4.4 為了追求速度所欠下的「技術債」。專注於 UI 正規化、將腳本轉化為正式 API，以及測試套件的標準化。)

---

## Goal (目標)

**Core Objective (核心目標)**: To move from "it works via script" to "it works via system architecture". (從「透過腳本運作」轉變為「透過系統架構運作」。)

**Deliverables (交付成果)**:
1.  **Unified Team UI (統一團隊介面)**: Replace the high-contrast "Dark Mode" Agent panel with standard "White Cards" that match human employees.
    *   *Correction*: Display "Team Budget" (Shared) for Agents instead of fake individual quotas until individual tracking is implemented.
2.  **System Health API (系統健康 API)**: Migrate `scripts/probe_librarian.py` into `HealthService`.
    *   *Security*: Endpoint `GET /api/system/health/rag` must be strictly protected by `system_admin` role.
3.  **Standardized Test Suite (標準化測試)**: Relocate `python/test_crawler.py` to `python/tests/external/`.
    *   *Config*: Register `external` marker in `pytest.ini`.

**Success Definition (成功定義)**:
- **Visual**: The Team Management page looks consistent. Accessing `/team` as non-manager redirects or shows specific view.
- **Automation**: `curl` to health endpoint returns valid JSON with `integrity_status`. 
- **QA**: `pytest -m external` runs successfully. `pytest` (default) skips it or runs it without warning.

---

## All Needed Context (所有需要的上下文)

### Documentation & References (文件與參考資料)

```yaml
- file: enduser-ui-fe/src/pages/TeamManagementPage.tsx
  why: Current UI implementation containing the "Indigo Panel" to be removed.
- file: scripts/probe_librarian.py
  why: Source logic for the RAG probe, to be ported to backend Service.
- file: python/src/server/services/health_service.py
  why: Destination service for the probe logic.
- file: python/test_crawler.py
  why: The orphan script to be adopted into the pytest family.
- file: python/pytest.ini
  why: Needs 'external' marker registration.
```

### Risk Analysis (風險分析 - "Don't Break B")

| Change | Potential Risk (潛在風險) | Mitigation Strategy (緩解策略) |
| :--- | :--- | :--- |
| **UI Refactor** | Removing the panel might hide "AI Quota" info. | **Decision**: Move "Quota" to the header or keep it on Agent Cards but explicitly label it "Shared Team Budget" to avoid misleading users. |
| **Probe Migration**| The script does actual DB writes (Seeding). | Backend implementation must use `dry_run` logic or distinct test entities. **Strictly enforce `system_admin` access** to prevent DOS via probe. |
| **Test Move** | `pytest` markers missing. | Update `pytest.ini` first. Ensure `httpx` is installed in test env. |

---

## Implementation Blueprint (實作藍圖)

### Step 1: The Test Standardization (QA First)
*Target: `python/pytest.ini`, `python/tests/external/test_104_reliability.py`*

- [x] **Config**: Edit `python/pytest.ini` to add `external: marks tests relying on 3rd party APIs`.
- [x] **Relocate**: Move logic from `python/test_crawler.py`.
- [x] **Pytest-ify**:
    *   Convert `CrawlerTestRunner` class to `test_104_crawler_reliability()`.
    *   Use `@pytest.mark.external`.
    *   Assertion: Check `jobs` list is not empty and contains valid fields.

### Step 2: The Service Migration (Backend)
*Target: `python/src/server/services/health_service.py`, `api_routes/system_api.py`*

- [x] **Refactor**: Create `check_rag_integrity()` in `HealthService`.
    *   Logic clone from `probe_librarian.py`.
    *   Return type: `HealthCheckResult` (status: "ok"|"degraded", details: dict).
- [x] **Endpoint**: Add `GET /api/system/health/rag`.
    *   **Decorator**: `@check_role(EmployeeRole.SYSTEM_ADMIN)` (or equivalent dependency).
- [x] **Cleanup**: Delete `scripts/probe_librarian.py`.

### Step 3: The UI Normalization (Frontend)
*Target: `enduser-ui-fe/src/pages/TeamManagementPage.tsx`*

- [x] **Remove**: Delete the `bg-indigo-900` "AI Fleet" section.
- [x] **Unify**: Add Agents to the main `team` list (mocked or fetched).
    *   If fetched from API, ensure `role: 'ai_agent'` is handled.
- [x] **Component**: Update `MemberCard` (or equivalent render logic):
    *   **Avatar**: If role is `ai_agent`, show specific Icon (🛠️/📈).
    *   **Stats**: If role is `ai_agent`, display "Shared Budget: {total_used}/{total}" (derived from `aiUsage` state).
    *   **Actions**: Disable "Manage Role" for Agents.

---

## Phase 4.5.1: Workflow Validation & Readiness (工作流驗證與就緒評估)

> 基於 Phase 4.5 完成後的系統現狀分析，針對企業工作流腳本、角色就緒度與人機協作落地的評估。

### Q1: 企業工作流程腳本 (Enterprise Execution Script) 正確嗎？
**評估結果**: **大部分正確，細節已就緒。**
*   **環境重置 (Step 0)**: `make db-init` 與 `dev-token` 機制運作正常，開發者登入體驗流暢。
*   **業務情蒐 (Step 1)**: MarketBot 爬蟲與 Pitch 生成功能已通過 E2E 測試驗證，Librarian 自動歸檔機制正常。
*   **行銷內容 (Step 2)**: Blog 生成已整合 RAG，且 `Brand Hub` UI 已實作完畢。
*   **管理決策 (Step 3)**: `TeamManagementPage` 重構完成 (Phase 4.5)，正確顯示待審核項目與 AI Agent 狀態。
*   **限制**: Step 5 (Final Deployment) 的 Logo 動態替換目前依賴手動設定或 Admin UI 操作，End-User UI 的即時反映需視快取狀況而定。

### Q2: Alice 與其他人的工作可以開始進行了嗎？
**評估結果**: **可以 (Ready to Start)。**
*   **帳號**: `mock_data` 已預建 Alice, Bob, Charlie 帳號。
*   **權限**: RBAC 修復完成，各角色介面隔離正確 (Sales Nexus vs Team Management)。
*   **工具**: Alice 有 Search Nexus，Bob 有 Brand Hub，Charlie 有 Team War Room。

### Q3: 5173 與 3737 的人機協作可以落地了？
**評估結果**: **是的 (Ready for Landing)。**
*   **5173 (End-User UI)**: 協作核心。DevBot 與 MarketBot 已作為「虛擬員工」整合進任務指派與團隊列表，視覺風格統一。
*   **3737 (Admin UI)**: 運維核心。負責系統監控、Prompt 管理與全域設定。
*   **狀態**: 在功能驗證環境 (Staging) 已完全可行，生產環境需注意 Secret 配置。

---

## Phase 4.5.2: Prompt as Data Migration (提示詞資料化遷移)

> **Goal**: To fully transition from Git-based to Data-based prompt management, resolving the discrepancy between documentation and implementation.

**Implementation Plan (執行計畫)**:
1.  **Backend Refactoring (Completed)**:
    *   Modified `PromptService` to handle empty database states gracefully (clearing memory cache).
    *   Added `test_prompts_loading.py` to verify DB loading logic.
    *   Status: ✅ Code & Test Ready.
2.  **Data Migration (Pending)**:
    *   Created `migration/013_seed_system_prompts.sql` containing "Golden Prompts" (POBot, DevBot, MarketBot).
    *   Action: Execute `make db-init` to populate `archon_prompts` table.
3.  **Frontend Implementation (Planned)**:
    *   **Location**: `enduser-ui-fe` (5173).
    *   **Strategy**: Extend `AdminPage.tsx` with a "Prompt Engineering" Tab.
    *   **Rationale**: Consolidates Admin tasks in one UI for dev convenience ("Probe" approach).

**Validation Steps (驗收標準)**:
*   [ ] **DB Verification**: `make db-init` runs without error; `archon_prompts` has 4 records.
*   [ ] **Service Verification**: Backend logs `Loaded 4 prompts` on startup.
*   [ ] **UI Verification (Future)**: Admin can view/edit prompts in 5173 Admin Page.

---

## Q&A (針對您的疑慮)

### Q1: Why was the Agent panel dark?
**Correction**: It violates the "Unified Workforce" philosophy. We will fix this by using consistent card designs.

### Q2: Is `make probe` a script?
**Correction**: Moving to `HealthService` allows `Clockwork` and external monitors to call it via API. `make probe` will become a wrapper for `curl`.

---

## Validation Steps (驗收步驟)

1.  **Test Config**:
    *   Run `cd python && pytest --markers` -> Confirm `external` is listed.
    *   Run `make test-external` -> Confirm 104 crawler runs.

2.  **API Security**:
    *   Run `curl ... /health/rag` as **Marketing User** -> Expect `403 Forbidden`.
    *   Run `curl ... /health/rag` as **System Admin** -> Expect `200 OK` with JSON `{ "dimension_check": "pass", ... }`.

3.  **UI Consistency**:
    *   Visit `/team`. Confirm "DevBot" appears as a White Card alongside human members.
    *   Confirm DevBot's stats show "Shared Budget" (e.g. 128/200).