# Bolt Performance Guidelines (Consolidated)

## 1. O(1) Map Lookups Over O(N*M) Array Scans in Render Loops
**Learning:** Calling `Array.prototype.find()` or nested `.filter()` inside `.map()` render loops, `useEffect` hooks, or XState context transitions creates hidden $O(N \times M)$ bottlenecks on every render cycle.
**Action:** Pre-calculate a `Map` at the module level (for static configs) or inside `useMemo` (for dynamic collections) to guarantee $O(1)$ lookups during rendering. Avoid `Map` overhead for tiny static arrays (< 5 items).

## 2. Hoist Intl.DateTimeFormat and Regex String Formatting
**Learning:** Instantiating `new Date().toLocaleDateString()`, `.toLocaleTimeString()`, or running chained `.replace(/_/g, " ")` regexes inside `.map()` loops triggers massive garbage collection pressure and repeated regex compilation on every render.
**Action:** Hoist `Intl.DateTimeFormat` instances and static enum/status string lookup dictionaries to the module level, or pre-calculate formatted strings inside `useMemo` when underlying data changes.

## 3. React.memo with Stable Callback and Array Identities
**Learning:** Wrapping list item components (`TeamMemberCard`, `VictoryFeedList`, `IdentityMatrixRow`) in `React.memo()` is completely negated if parent components pass inline arrow functions or fallback array literals (`data?.items || []`).
**Action:** Always pair `React.memo()` (with an explicit `.displayName`) with `useCallback` for handler props and `useMemo` for fallback array dependencies.

## 4. Memoize Expensive Markdown Parsing and Component Maps
**Learning:** Passing inline `components={{ ... }}` object literals to `ReactMarkdown` unmounts and remounts custom subtrees (`MermaidRenderer`, `RAGCitation`) on every render, and inline regex markdown pre-processing blocks UI state updates.
**Action:** Define `ReactMarkdown` component maps statically or wrap them in `useMemo`, and memoize any heavy markdown string transformations.

## 5. Single-Pass Accumulators and Concurrent Async Requests
**Learning:** Chaining `[...arr.map(), ...arr.map()]` for min/max domain calculations (`d3.extent`) causes redundant array allocations, and sequential `await` calls for independent data fetches block rendering.
**Action:** Use a single-pass `for` loop for numeric domain extents and parallelize independent async operations with `Promise.all` (frontend) or `asyncio.gather` (backend).

## 6. Memoize Filtered List Projections in Render Loops
**Learning:** Calling `.filter()` multiple times directly inside JSX render branches (e.g., `users.filter(u => u.role === 'ai_agent')`) causes redundant linear scans and creates throwaway array allocations on every render cycle.
**Action:** Compute filtered sub-collections once using `useMemo` when source collections change, ensuring stable array references for downstream rendering and conditional length checks.
