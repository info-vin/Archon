## 2026-08-13 - FastAPI type hinting vs dictionary return values
**Learning:** When a FastAPI route is typed with a Pydantic model (e.g., `-> LeadActionResponse`), returning a raw dictionary (e.g., `return res`) works at runtime because FastAPI dynamically coerces it via `response_model`, but standard Python static type checkers will flag this as a type violation.
**Action:** Always instantiate the Pydantic model explicitly in the `return` statement (e.g., `return LeadActionResponse(...)`) to satisfy both FastAPI's validation and static type checkers.
## 2025-05-24 - TypedDict vs Dict Typing in FastAPI
**Learning:** When a service returns `list[dict[str, Any]]` or `dict[str, Any]`, FastAPI's `response_model` handles the serialization correctly but Python type checkers (like MyPy/Ruff) will complain about return type mismatches.
**Action:** Use `typing.cast` (e.g. `cast(list[CrawlerTargetResponse], res)`) to satisfy the type checker when returning service data to a route handler typed with a specific Pydantic model.
