# Phase 4.11 Technical Debt Paydown - The Type Safety Purge

> **Status**: IN PROGRESS
> **Goal**: Systematically eliminate high-risk MyPy type errors in the backend codebase to prevent runtime crashes (500 Errors).

## 📊 Backend Type Error Analysis (Top 10 Offenders)

| Rank | File Path | Initial Errors | Resolved | Status | Action Item |
| :--- | :--- | :---: | :---: | :--- | :--- |
| **1** | `src/server/api_routes/settings_api.py` | 36 | **36** | 🟢 **Clean** | Fixed `logfire` usage & `None` checks. |
| **2** | `src/server/api_routes/projects_api.py` | 38 | 0 | 🔴 Pending | Fix dict key access & return types. |
| **3** | `src/server/services/source_management_service.py` | 31 | 0 | 🔴 Pending | Fix implicit Optional & returns. |
| **4** | `src/server/api_routes/marketing_api.py` | 27 | 0 | 🔴 Pending | Fix logging attribute errors. |
| **5** | `src/server/services/projects/task_service.py` | 23 | 0 | 🔴 Pending | Fix implicit Optional. |
| **6** | `src/server/services/crawling/code_extraction_service.py` | 23 | 0 | 🔴 Pending | Fix complex regex types. |
| **7** | `src/agents/document_agent.py` | 18 | 0 | 🔴 Pending | Fix list methods & optional. |
| **8** | `src/server/services/storage/code_storage_service.py` | 17 | 0 | 🔴 Pending | Fix file ops types. |
| **9** | `src/server/api_routes/ollama_api.py` | 17 | 0 | 🔴 Pending | Fix operator mismatches. |
| **10** | `src/agents/base_agent.py` | 15 | 0 | 🔴 Pending | Fix base class generics. |

### Other Critical Fixes (High Impact)
| File | Resolved | Impact |
| :--- | :---: | :--- |
| `src/server/utils/semantic_version.py` | **16** | Prevented version comparison crashes. |
| `src/mcp_server/models.py` | **10** | Fixed Pydantic model instantiation. |
| `src/server/services/credential_service.py` | **32** | Hardened API key retrieval logic. |
| `src/server/services/llm_provider_service.py` | **25** | Stabilized LLM client creation. |

## Strategy
1.  **Level 1 (Core Infrastructure)**: `settings_api`, `credential_service` - **COMPLETED**
2.  **Level 2 (Business Logic)**: `projects_api`, `marketing_api` - **NEXT**
3.  **Level 3 (Agents & Tools)**: `document_agent`, `code_storage_service` - **PENDING**

## Verification
Run `make lint-be` to check progress.
Current total errors: **~501** (Down from initial estimate >600)
