---
description: How to automate the BaseRepository refactoring for a given Python backend service
---

# 🚀 Automated Workflow: Refactor BaseRepository
This workflow uses an AST-based script or a manual surgical approach to replace repetitive `try...except` Supabase logic with the streamlined `self.execute_query()` closure from `BaseRepository`.

## Step 1: Execute AST Automation Script (Preferred)
Run the `refactor_service.py` script against the target service file.
```bash
uv run python scripts/refactor_service.py <path_to_service_file>
```

## Step 1.1: Fallback - Surgical Manual Refactoring
If Step 1 fails due to environment issues (e.g., Python < 3.9), follow this **Physical Alignment Pattern**:

1. **Inheritance**: 
   ```python
   from ..base_repository import BaseRepository
   class YourService(BaseRepository):
   ```
2. **Initialization**:
   ```python
   def __init__(self, supabase_client=None):
       super().__init__(supabase_client)
       # Use self.supabase for dependent services
       self.other_service = OtherService(self.supabase)
   ```
3. **Closure Conversion**:
   Replace:
   ```python
   try:
       response = self.supabase_client.table("xxx").select("*").execute()
       return True, response.data
   except Exception as e:
       return False, {"error": str(e)}
   ```
   With:
   ```python
   query = self.supabase.table("xxx").select("*")
   return self.execute_query(query)
   ```

## Step 2: Agent Quality Review
Ensure variable names match and redundant `logger.error` within service methods are removed (since `BaseRepository` handles it).

## Step 3: Validation and Typing 
Run the backend tests and type-checks.
```bash
make type-check
make test-be
```

## Step 4: Add and Commit
```bash
git add <path_to_service_file>
git commit -m "refactor(backend): use BaseRepository for <service_name>"
```

## Target Services Checklist (20 Files)
### Core (Verified Inheritance)
- [x] `python/src/server/services/settings_service.py`
- [x] `python/src/server/services/health_service.py`
- [x] `python/src/server/services/log_service.py`
- [x] `python/src/server/services/source_management_service.py`
- [x] `python/src/server/services/profile_service.py`

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
- [x] `python/src/server/services/crawling/document_storage_operations.py`
- [x] `python/src/server/services/crawling/code_extraction_service.py`
- [x] `python/src/server/services/crawling/page_storage_operations.py`
- [x] `python/src/server/services/crawling/crawling_service.py`
