## 2026-05-07 - Add loading spinner to async submit button
**Learning:** Destructive or important actions (like returning content to the author) often lack visual loading states compared to primary "success" actions. Adding a simple spinner and status text (e.g., "RETURNING...") provides immediate feedback and prevents duplicate submissions or confusion during network latency.
**Action:** Always check asynchronous destructive buttons (like Reject, Return, Delete) to ensure they share the same loading state patterns as their primary action counterparts (like Approve, Publish).
