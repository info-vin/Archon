# Phase 4.6.2 Implementation Plan: Bob's Content Workbench

> **Status**: 已完成 (DONE)
> **Owner**: Bob (Content Lead)
> **Goal**: Deploy the "Content Workbench" — a 3-Agent integrated environment for high-velocity content production.

## 0. Prerequisite Checks & Configuration
- [x] **0.1 Verify Migration 022**: Ensure `migration/022_add_blog_lead_relation.sql` exists and contains RLS policies for `leads` and `visit_logs` (Score >= 80).
- [x] **0.2 Verify Makefile**: Confirm `make db-init` is available.
- [x] **0.3 Configure Settings**:
    - Add `STORY_CANDIDATE_SCORE_THRESHOLD` (Default: 80) to System Settings via `scripts/init_db.py` or Admin UI.
    - Add `NANA_BANANA_MODEL` (Default: `gemini-2.0-flash-exp` or `gemini-2.5-imgen`) to Settings.

## 1. Backend API Implementation (`python/src/server`)

### 1.1 `marketing_api.py` Expansion (The Workbench API)
- [x] **1.1.1 Add `GET /api/marketing/sources`**:
    - **Logic**: Aggregated query.
        - Source A: `leads` where `status='WON'` OR `score >= settings.THRESHOLD`.
        - Source B: `archon_tasks` where `assignee_id = current_user.id` AND `status != 'done'`.
    - **Return**: Unified list `[{id, type, title, score, date, summary}]`.
- [x] **1.1.2 Add `GET /api/marketing/context/{source_id}`**:
    - **Logic**:
        - If Source is `lead`: Fetch `lead_details` + `visit_logs`.
        - If Source is `task`: Fetch `task_details` + `comments`.
        - **Common**: Call `LibrarianService.search(context_text)` for RAG references.
    - **Return**: `ContextPayload` schema.
- [x] **1.1.3 Update `POST /api/marketing/drafts`**:
    - **Param**: Accept `context_source_id` and `context_type`.
    - **Logic**: Inject retrieved context into `MarketBot` prompt.
- [x] **1.1.4 Add `POST /api/marketing/nana-banana`**:
    - **Logic**: Proxy to Google Gemini Vision/Imagen.
    - **Model**: Fetch `NANA_BANANA_MODEL` from settings.

### 1.2 Service Layer Logic
- [x] **1.2.1 Update `LibrarianService`**: Ensure `search` accepts generic text queries (not just `lead_id`).
- [x] **1.2.2 Update `AgentRegistry`**: Register "Nana Banana" tool config (if not present).

## 2. Frontend Implementation (`enduser-ui-fe`)

### 2.1 Layout & Navigation
- [x] **2.1.1 Refactor `BrandPage.tsx`**:
    - Replace Grid with `SplitPaneLayout` (Left: 30%, Right: 70%).
    - **Left**: `<ContentSourceList />`.
    - **Right**: `<WorkbenchContainer />`.

### 2.2 Left Pane: Content Sources
- [x] **2.2.1 Create `<ContentSourceList />`**:
    - Use "Dense List" style (Reference: Admin UI Logs).
    - Display: Icon (Lead/Task), Title, Score Badge, Date.
    - Action: Click to set Active Source.

### 2.3 Right Pane: Workbench Container
- [x] **2.3.1 Create `<WorkbenchTabs />`**:
    - Tabs: `Context` (Read-Only) | `Editor` (Write).
- [x] **2.3.2 Create `<ContextViewer />`**:
    - **Section 1**: Source Data (Visit Log Transcript / Task Desc).
    - **Section 2**: Librarian Suggestions (RAG Cards).
    - **Feature**: Text Highlighting (Select text -> "Add to Prompt").
- [x] **2.3.3 Create `<MagicEditor />`**:
    - Toolbar: `✨ Draft`, `🎨 Image`, `💾 Save`, `🚀 Publish`.
    - State: `draftContent` (Markdown).

### 2.4 Integration
- [x] **2.4.1 Wire `useContentSources` hook**: Fetch from `/api/marketing/sources`.
- [x] **2.4.2 Wire `useContextLoader` hook**: Fetch on source selection.
- [x] **2.4.3 Wire Agent Actions**:
    - `Draft`: POST to `/drafts` with Context.
    - `Image`: POST to `/nana-banana`.

## 3. Database & Security
- [x] **3.1 Verify RLS Policies**:
    - Ensure Bob (Marketing) can read `visit_logs` of High-Score Leads (via 022 migration).
    - Ensure Bob can read his assigned tasks.
- [x] **3.2 Score Config**:
    - Insert default setting into `system_settings` table (if exists) or `credentials`.

## 4. Verification Steps
- [x] **4.1 Test Source Aggregation**:
    - Create a High Score Lead (Alice).
    - Create a Task for Bob (Charlie).
    - Verify both appear in Bob's Left Pane.
- [x] **4.2 Test Context Loading**:
    - Click Lead -> Verify Visit Log Transcript appears.
- [x] **4.3 Test Magic Draft**:
    - Click "Draft" -> Verify content is generated based on Transcript.
- [x] **4.4 Test Nana Banana**:
    - Click "Image" -> Verify image URL returned.
- [x] **4.5 Test RLS**:
    - Try to fetch a Low Score Lead (should fail/empty).

## 5. Artifacts
- **Files to Modify**:
    - `python/src/server/api_routes/marketing_api.py`
    - `enduser-ui-fe/src/pages/BrandPage.tsx`
    - `enduser-ui-fe/src/features/marketing/components/*`
- **Files to Create**:
    - `enduser-ui-fe/src/features/marketing/components/WorkbenchLayout.tsx`
    - `enduser-ui-fe/src/features/marketing/components/ContentSourceList.tsx`
    - `enduser-ui-fe/src/features/marketing/components/MagicEditor.tsx`

---

> **Note**: This plan strictly adheres to the "No new Python files" rule (extending existing APIs) and leverages the 3737 "Dense UI" philosophy.
