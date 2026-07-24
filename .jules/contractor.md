
## 2026-07-23 - Hardened log_api /record-gemini-log
**Learning:** Returning dictionaries with potential error keys in FastAPI endpoints that signify successful completion (status 201) can cause schema mismatches if the Pydantic schema strictly expects nested data (like `{"log": {}}`). Handled by ensuring `log` and `error` keys are typed as Optional, allowing both successful dicts and error dicts to pass serialization without triggering an Internal Server Error.
**Action:** Always carefully trace the raw return dict of the underlying service (e.g. `log_service.create_log_entry`) to include all possible dynamic fields (like failure structures) in the Pydantic ResponseModel when adding strict types.
