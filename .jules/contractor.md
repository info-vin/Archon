## 2026-08-13 - FastAPI type hinting vs dictionary return values
**Learning:** When a FastAPI route is typed with a Pydantic model (e.g., `-> LeadActionResponse`), returning a raw dictionary (e.g., `return res`) works at runtime because FastAPI dynamically coerces it via `response_model`, but standard Python static type checkers will flag this as a type violation.
**Action:** Always instantiate the Pydantic model explicitly in the `return` statement (e.g., `return LeadActionResponse(...)`) to satisfy both FastAPI's validation and static type checkers.
