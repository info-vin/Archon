1. **Optimize `validTasks` in `enduser-ui-fe/src/features/dashboard/components/GanttView.tsx`**
   - The D3 rendering logic creates `new Date()` instances multiple times for the same data inside the render loop (`useEffect`), particularly in calculating domains and drawing bars (`x(new Date(d.created_at!))`).
   - Also, `validTasks` only filters out undefined dates but doesn't map them.
   - We will update `validTasks` memoization to pre-parse the `Date` objects and store them alongside the task data. This prevents expensive date string parsing on every render and loop iteration. The prompt memory notes: "When optimizing performance by hoisting expensive operations (like datetime parsing) out of loops, verify that the operation wasn't originally guarded by conditions that restrict its execution to only relevant items. Unconditionally hoisting guarded operations can degrade performance by computing values for all items unnecessarily." In this case, `validTasks` already filters out tasks without `due_date` and `created_at`, so we are only parsing dates for valid tasks.

2. **Verify changes to `GanttView.tsx`**
   - Use `run_in_bash_session` to check the diff.

3. **Run tests**
   - Run tests to ensure no regressions are introduced.

4. **Complete pre-commit steps**
   - Follow instructions to verify.

5. **Submit PR**
   - Create PR with the Bolt template.
