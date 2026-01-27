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

1.  **Config**: Edit `python/pytest.ini` to add `external: marks tests relying on 3rd party APIs`.
2.  **Relocate**: Move logic from `python/test_crawler.py`.
3.  **Pytest-ify**:
    *   Convert `CrawlerTestRunner` class to `test_104_crawler_reliability()`.
    *   Use `@pytest.mark.external`.
    *   Assertion: Check `jobs` list is not empty and contains valid fields.

### Step 2: The Service Migration (Backend)
*Target: `python/src/server/services/health_service.py`, `api_routes/system_api.py`*

1.  **Refactor**: Create `check_rag_integrity()` in `HealthService`.
    *   Logic clone from `probe_librarian.py`.
    *   Return type: `HealthCheckResult` (status: "ok"|"degraded", details: dict).
2.  **Endpoint**: Add `GET /api/system/health/rag`.
    *   **Decorator**: `@check_role(EmployeeRole.SYSTEM_ADMIN)` (or equivalent dependency).
3.  **Cleanup**: Delete `scripts/probe_librarian.py`.

### Step 3: The UI Normalization (Frontend)
*Target: `enduser-ui-fe/src/pages/TeamManagementPage.tsx`*

1.  **Remove**: Delete the `bg-indigo-900` "AI Fleet" section.
2.  **Unify**: Add Agents to the main `team` list (mocked or fetched).
    *   If fetched from API, ensure `role: 'ai_agent'` is handled.
3.  **Component**: Update `MemberCard` (or equivalent render logic):
    *   **Avatar**: If role is `ai_agent`, show specific Icon (🛠️/📈).
    *   **Stats**: If role is `ai_agent`, display "Shared Budget: {total_used}/{total}" (derived from `aiUsage` state).
    *   **Actions**: Disable "Manage Role" for Agents.

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
