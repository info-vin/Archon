# Phase 5.9.4 L2 Architecture Hardening & Job Board Monolith Split

## Context
During `make phase-audit`, a Monolith Check warning was raised for `python/src/server/services/job_board_service.py` exceeding the 400-line strict limit. The file mixed anti-WAF crawling logic using `curl_cffi` and higher-level domain logic (AI inference, DB interaction).

Additionally, a physical scan of the `crawling` subsystem revealed orphan code and misaligned domain boundaries (e.g., Code Extraction logic existing within the Crawling module).

## Objective
1. **Split the Monolith**: Decouple the low-level `curl_cffi` WAF bypassing logic into a dedicated Anti-WAF client layer `crawling/clients/job104_client.py`.
2. **Clean Up Orphan Code**: Eradicate unused `page_storage_operations.py` and `helpers/llms_full_parser.py`.
3. **Domain Re-alignment**: Move `code_extraction_service.py` and its associated `logic/` to an independent `code_extraction` domain, conforming to the Single Responsibility Principle and strict L2 architectural norms.
4. **Eradicate False Tests & Disconnects**: Discover and fix a severe disconnect in `report_enrichment_service.py` regarding the TTS `(success, bytes)` tuple, and eliminate the false tests in `test_report_service.py` that were masking this bug.

## Implementation Steps
1. Create `python/src/server/services/crawling/clients/job104_client.py` and extract `JobData` and sync fetch functions (`search_jobs_sync`, `_fetch_from_104_sync`, etc.).
2. Slim down `JobBoardService` to focus on embedding similarity checks, Gemini LLM `_infer_need`, and Supabase bulk inserts.
3. Establish `python/src/server/services/code_extraction/` and port over the `CodeExtractionService` and `ast_processor.py`.
4. Fix `report_enrichment_service.py` to correctly unpack the TTS tuple and upload generated `wav` bytes to the `archon_documents` bucket.
5. Fix `test_report_service.py` to mock `(bool, bytes)` tuples and correctly patch `get_supabase_client` in `utils` to avoid network dependencies.
6. Run `make lint-be`, `make test-be`, and `make phase-audit` to physically certify all changes.
