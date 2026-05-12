## 2026-05-07 - Add loading spinner to async submit button
**Learning:** Destructive or important actions (like returning content to the author) often lack visual loading states compared to primary "success" actions. Adding a simple spinner and status text (e.g., "RETURNING...") provides immediate feedback and prevents duplicate submissions or confusion during network latency.
**Action:** Always check asynchronous destructive buttons (like Reject, Return, Delete) to ensure they share the same loading state patterns as their primary action counterparts (like Approve, Publish).
## 2024-05-19 - Adding loading state to APPROVE button requires test mock updates
**Learning:** When adding a loading state that introduces a new icon component (like `RefreshCwIcon`) to an existing component (like `EthicsAuditPanel`), the unit tests will fail if that new icon is not also added to the `vi.mock` section of the corresponding `.test.tsx` file.
**Action:** Always check the `.test.tsx` file of the component being modified. If it uses `vi.mock` for its children components or icons, ensure any newly added dependencies in the implementation are mirrored in the mock setup before running tests.
## 2026-05-11 - Add loading state to async configuration save button
**Learning:** System configurations and settings changes (like saving SentinelRadar scoring rules) often lack loading states because they're plain text buttons or text links instead of primary action buttons. Adding visual loading states (e.g., "Saving..." with a spinner) provides necessary feedback and prevents confusion during API delays.
**Action:** Always check text-based actions and configuration save buttons for asynchronous loading states, disabling the element and displaying a spinner while processing.
