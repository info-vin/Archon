# Phase 5.10.5: Zombie Task Recovery & DLQ

## Objective
Implement a robust Janitor/Reaper pattern in the `WorkerService` to automatically recover tasks that are stuck in `doing` or `processing` states due to unexpected process termination (Zombie tasks). Introduce a Dead Letter Queue (DLQ) mechanism with a `retry_count` limit to prevent infinite crash loops.

## Requirements
1. **Schema Update**: Add `retry_count` (integer, default 0) to `archon_tasks`.
2. **WorkerService Healing**: On `start()`, `worker_service.py` must scan for `doing` and `processing` tasks.
3. **Retry Logic**: If `retry_count < 3`, increment it, append error context to logs/description, and reset status to `dispatched`.
4. **DLQ Logic**: If `retry_count >= 3`, mark task as `failed` to prevent infinite loops.
5. **Testing**: Comprehensive `pytest` coverage for the new self-healing logic in `test_worker_service.py`.

## Compliance
- **No False Development**: Must physically verify DB schema and behavior.
- **SSOT**: Use `task_service` for all database interactions.
- **DRY**: Reuse existing query logic where possible.
