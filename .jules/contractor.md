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

## 2025-03-08 - Preserving Original Service Invocation
**Learning:** When retrofitting existing FastAPI routes with Pydantic response models, it is crucial to preserve the exact original data-fetching and tuple-unpacking logic (e.g., `await service.list_items()`). Attempting to "clean up" or modify the internal service call signature in the router to match the new return structure often breaks existing test mocks or causes tuple-unpacking validation failures.
**Action:** When adding Pydantic models to a route, only touch the final return statement. Unpack the original data structure cleanly and pass the values into the `ResponseModel(**data)` constructor, leaving all preceding business logic completely intact.
## 2024-05-24 - Agent HITL API Hardening
**Learning:** The agent HITL endpoints (`get_pending_approvals`, `review_approval`, etc.) previously returned raw dicts. Providing explicit Pydantic response models (`ApprovalRequestResponse`, etc.) required adding explicit `Field` annotations to clearly document the API response in OpenAPI schema. This was done without changing any of the handler's internal data passing logic (still pulling properties as dictionary items when returning) ensuring backwards compatibility.
**Action:** Always maintain the underlying handler dictionary extraction logic while wrapping the route definition itself with explicit `response_model` arguments to allow FastAPI to do the validation and documentation overhead gracefully.
