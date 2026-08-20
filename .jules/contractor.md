## 2026-08-13 - FastAPI type hinting vs dictionary return values
**Learning:** When a FastAPI route is typed with a Pydantic model (e.g., `-> LeadActionResponse`), returning a raw dictionary (e.g., `return res`) works at runtime because FastAPI dynamically coerces it via `response_model`, but standard Python static type checkers will flag this as a type violation.
**Action:** Always instantiate the Pydantic model explicitly in the `return` statement (e.g., `return LeadActionResponse(...)`) to satisfy both FastAPI's validation and static type checkers.
## 2025-05-24 - TypedDict vs Dict Typing in FastAPI
**Learning:** When a service returns `list[dict[str, Any]]` or `dict[str, Any]`, FastAPI's `response_model` handles the serialization correctly but Python type checkers (like MyPy/Ruff) will complain about return type mismatches.
**Action:** Use `typing.cast` (e.g. `cast(list[CrawlerTargetResponse], res)`) to satisfy the type checker when returning service data to a route handler typed with a specific Pydantic model.

## 2024-08-15 - Hardening get_ai_model_health
**Learning:** When hardening endpoints that return lists of objects inside a top-level wrapper object (like `{ "status": ..., "models": [...] }`), it's crucial to define both the wrapper response model (`AIModelHealthResponseDTO`) and the item detail model (`AIModelHealthDetailDTO`) to preserve the exact JSON structure. Also, `from_attributes=True` wasn't needed here because we are explicitly mapping to the Pydantic models from dictionaries during instantiation.
**Action:** Always create a hierarchy of DTOs matching the exact nested structure of the legacy dict return type before migrating the return statements to instantiate the Pydantic classes.
## 2026-08-16 - Handling Pydantic Fallbacks for Service Exceptions
**Learning:** When unpacking dictionary responses from service layers into Pydantic response models, wrap the primary logic in a `try` block (`return Model(**(await service()))`) and catch exceptions to return a `Model` instance initialized with generic default fields that fulfill the strict structural contract. This prevents `ValidationError` 500s when downstream data fails and preserves client type compatibility.
**Action:** Always provide structurally complete fallback instantiation in except blocks when typing endpoint routes with explicit response models.
## 2025-05-15 - Pydantic Instantiation from Services
**Learning:** When using a dictionary return from a service in FastAPI, it is safer to return `Model.model_validate(data)` rather than `Model(**data)` since it provides better compatibility with Pydantic V2 and ensures correct parsing logic.
**Action:** Always prefer `Model.model_validate()` when returning the data directly.
