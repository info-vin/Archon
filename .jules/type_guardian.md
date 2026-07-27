## 2025-01-20 - Adding typed dicts for dynamic API responses in Settings Service
**Learning:** When incrementally adding static type safety to services that return complex, dynamic dictionary data structures (like database statistics) consumed directly by downstream JSON responses, using `TypedDict` is safer than `BaseModel` or `dataclass` as it avoids unexpected runtime serialization or `TypeError` breaking changes.
**Action:** Apply `TypedDict` for raw dictionary responses first before migrating completely to class-based models if downstream systems are tightly coupled to dict syntax.
