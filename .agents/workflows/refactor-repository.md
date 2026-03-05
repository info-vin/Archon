---
description: How to automate the BaseRepository refactoring for a given Python backend service
---

# 🚀 Automated Workflow: Refactor BaseRepository
This workflow uses an AST-based script to accurately replace the repetitive `try...except` Supabase logic inside a given backend service with the streamlined `self.execute_query()` closure from `BaseRepository`.

## Step 1: Execute AST Automation Script
First, we will run the `refactor_service.py` script against the target service file. This script will find all `try...except` block instances that call `self.supabase_client` and rewrite them to use `BaseRepository._query` closures. 
```bash
python scripts/refactor_service.py <path_to_service_file>
```

## Step 2: Agent Quality Review
The automated script handles the bulk of the refactoring, but variable names or specific error messages might need light touch-ups.
Use `git diff` to review the changes.
```bash
git diff <path_to_service_file>
```
If the AST script missed a custom error handling scenario, use your agent tools to safely adjust the code. Ensure the class inherits from `BaseRepository` instead of instantiating the raw Supabase client if not already done.

## Step 3: Validation and Typing 
Run the backend tests and type-checks for the refactored code. The change MUST pass all tests.
```bash
// turbo-all
make type-check
make test-be
```

## Step 4: Add and Commit
If the tests pass successfully, the refactoring for this service is complete.
```bash
git add <path_to_service_file>
git commit -m "refactor(backend): use BaseRepository for <service_name>"
```

## Target Services Checklist (20 Files)
These are the exact 20 files that currently use the `try...except` and `self.supabase_client` boilerplate and should be passed through this workflow.

### Core
- [ ] `python/src/server/services/settings_service.py`
- [ ] `python/src/server/services/health_service.py`
- [ ] `python/src/server/services/log_service.py`
- [ ] `python/src/server/services/source_management_service.py`

### Projects & Documents
- [ ] `python/src/server/services/projects/document_service.py`
- [ ] `python/src/server/services/projects/project_creation_service.py`
- [ ] `python/src/server/services/projects/project_service.py`
- [x] `python/src/server/services/projects/task_service.py` (Pilot completed)
- [ ] `python/src/server/services/projects/versioning_service.py`
- [ ] `python/src/server/services/projects/source_linking_service.py`

### Storage & Search
- [ ] `python/src/server/services/storage/storage_services.py`
- [ ] `python/src/server/services/storage/base_storage_service.py`
- [ ] `python/src/server/services/search/agentic_rag_strategy.py`
- [ ] `python/src/server/services/search/base_search_strategy.py`
- [ ] `python/src/server/services/search/rag_service.py`
- [ ] `python/src/server/services/search/hybrid_search_strategy.py`

### Crawling
- [ ] `python/src/server/services/crawling/document_storage_operations.py`
- [ ] `python/src/server/services/crawling/code_extraction_service.py`
- [ ] `python/src/server/services/crawling/page_storage_operations.py`
- [ ] `python/src/server/services/crawling/crawling_service.py`

### Other
- [x] `python/src/server/services/profile_service.py` (Completed)
