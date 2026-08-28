## 2024-05-18 - String split vs find for extracting occurrences
**Learning:** Using `string.find("```", pos)` inside a while loop to extract all occurrences in a large text is significantly slower (~30-50% slower) than simply using `string.split("```")` and calculating the positions, or using `re.finditer`.
**Action:** When extracting all positions of a substring in a large document, prefer `re.finditer` or string splitting with length accumulation instead of sequential `.find()` calls in a while loop.

## 2024-05-18 - Pre-compiled arrays vs inline arrays in loops
**Learning:** Defining constant arrays (like lists of stop words or syntax indicators) inside a function that runs in a tight loop is surprisingly costly due to repeated object creation and allocation overhead in Python. Pulling them out into module-level constants speeds up execution.
**Action:** Always extract constant reference lists and tuples to module-level variables (e.g. `_DOC_INDICATORS`) when used inside loops, especially in text processing functions like `extract_code_blocks`.

## 2026-03-09 - Avoid sum(1 for ...) generator expressions in hot paths
**Learning:** Using `sum(1 for x in y if condition)` generator expressions inside frequently executed paths or nested loops incurs a performance penalty due to generator object creation overhead in Python. Standard `for` loops with a counter variable or even `len([x for x in y if condition])` (list comprehensions) are faster.
**Action:** Replace `sum(1 for ...)` with standard `for` loops and counters (or list comprehensions if appropriate) when optimizing Python code that runs in tight loops.

## 2024-05-18 - Repeated string conversions in generator expressions
**Learning:** Using a generator expression like `sum(1 for x in y if x in text.lower())` re-evaluates `text.lower()` on every iteration if it's placed in the loop condition, leading to O(N*M) string allocations instead of O(N) when iterating over strings. The creation of generator expressions also has some overhead compared to standard for loops.
**Action:** When extracting data or checking multiple items against a string, always cache the string conversions (like `.lower()`) outside of loops, and consider standard for loops instead of generators on hot paths for better performance.

## 2024-05-18 - Nested generator expressions vs explicit loops
**Learning:** Using nested generator expressions like `sum(1 for ... if any(...))` causes significant overhead in Python due to creating multiple generator objects per outer loop iteration. Replacing these nested generators with standard `for` loops, caching type conversions (like `str()`), and using early `break` statements can be ~4x faster on hot paths.
**Action:** When filtering or counting based on compound conditions involving sub-lists or strings, unroll nested generators (`any()`, `all()`, or inner comprehensions) into standard `for` loops to avoid allocation overhead and enable true short-circuiting.
## 2025-05-18 - Pre-calculate feature strings before O(N^2) comparison loops
**Learning:** In `extract_code_blocks_logic`, calling `_normalize_code_for_comparison` inside the O(N^2) nested deduplication loop caused massive performance degradation because expensive regex substitutions were run redundantly.
**Action:** Always pre-calculate normalized codes or feature vectors into an O(N) list comprehension BEFORE executing an O(N^2) similarity or comparison loop.

## 2024-05-18 - Fast upper-bound ratio checks for SequenceMatcher
**Learning:** In Python, calling `difflib.SequenceMatcher.ratio()` inside O(N^2) loops (like deduplicating code blocks) is a severe performance bottleneck because `.ratio()` calculates the actual longest common subsequence in O(L_a * L_b) time.
**Action:** Always optimize `SequenceMatcher` inside loops by pre-calculating sequence lengths to allow a fast O(1) upper-bound check (`2.0 * min(l1, l2) / (l1 + l2) < threshold`), and always call the heuristic guards `.real_quick_ratio()` and `.quick_ratio()` before committing to `.ratio()`.

## 2025-05-18 - Tracking O(N) generator expressions in Python queues for rate limiters
**Learning:** In highly concurrent paths like `RateLimiter`, using an O(N) generator expression (e.g., `sum(tokens for _, tokens in deque)`) to calculate current token usage causes a significant performance bottleneck because it repeatedly loops over potentially thousands of items.
**Action:** Replace `sum(...)` generator expressions over queues with an O(1) caching counter (e.g., `self.current_tokens`) that is incremented when adding items and decremented when removing items.

## 2025-05-18 - Batch database fetches for related entities using .in_()
**Learning:** Using O(N) individual database queries through loop mechanisms like `asyncio.gather(*[format_with_sources(p) for p in projects])` produces an N+1 query bottleneck when looking up relationships, such as linked sources for project IDs.
**Action:** Always batch these database lookups into a single O(1) `.in_("id", id_list)` database query, and map the bulk response data back to the entity list in memory in order to speed up the loop processing execution path.
## 2024-05-18 - Replacing multiple list comprehensions with single iteration over lists
**Learning:** Traversing the exact same list twice using list comprehensions like `[s["source_id"] for s in sources if ...]` adds unnecessary O(N) overhead compared to a single pass accumulation.
**Action:** When extracting grouped items from a list, use a single for-loop with O(1) appends to respective lists to prevent redundant iteration loops over large datasets.

## 2024-05-18 - Single pass accumulation over multiple generators
**Learning:** In Python, calculating multiple aggregates (like sums) from the exact same list using multiple generator expressions (e.g., `sum(r['a'] for r in data)` and `sum(r['b'] for r in data)`) adds unnecessary O(N) iteration overhead and generator allocations.
**Action:** Use a single pass `for` loop to accumulate multiple values simultaneously to save CPU time and memory spikes.

## 2024-05-18 - Beware Supabase 1000-row limit for aggregate counts
**Learning:** Using an O(1) `.in_("id", ids)` fetch to retrieve ALL rows into memory in Python to emulate a `GROUP BY COUNT` is functionally dangerous because Supabase/PostgREST enforces a strict 1000-row limit by default. If the total relations exceed this, the query silently truncates, resulting in wildly inaccurate counts.
**Action:** Do NOT use `.in_()` to pull raw rows to emulate aggregate database counts. Use `count="exact", head=True` inside individual `.eq()` lookups if an RPC is not available, as it delegates the true count to the database engine and respects pagination limits.

## 2025-05-18 - Batching database inserts for chunked content
**Learning:** When splitting large text files into chunks for database storage, inserting each chunk in a loop (`.insert().execute()`) creates an N+1 query bottleneck. The database insertion overhead can dominate the function's execution time for large files.
**Action:** Batch multiple Supabase row insertions by accumulating data into a list and calling a single `.insert([...]).execute()`. Add a fallback to individual insertions in case of batch failure to preserve data and detailed logging.

## 2024-05-18 - Avoid text.split() for fast word counting
**Learning:** Using `len(text.split())` to estimate token or word counts is extremely inefficient because it allocates a new list and string objects for every word. When inside a generator expression like `sum(len(t.split()) for t in batch)`, it can be ~10x slower than alternative approaches.
**Action:** When you only need to estimate word counts (like for rate limit calculations), use `text.count(' ') + 1` inside a standard for-loop. This executes in optimized C code, bypassing massive string and list allocations.
## 2025-05-18 - Pre-parsing dates before nested time window loops
**Learning:** In `get_knowledge_roi` and `get_sla_reliability`, calling `datetime.fromisoformat()` repeatedly inside a 14-day rolling window loop causes an O(N*M) performance bottleneck, as the same date strings are parsed over and over.
**Action:** Extract the date string parsing out of the nested loops. Pre-parse all dates into an in-memory list (e.g., `[(item, parsed_date)]`) before executing the time window loop to ensure O(N) date conversions and fast O(1) datetime comparisons.
## 2025-05-18 - Avoid repeated string conversions in dictionaries
**Learning:** In Python, applying string transformations (e.g., `.upper()`) to static dictionary values inside a nested loop causes redundant memory allocation and performance penalties.
**Action:** Extract and precalculate these values (e.g., `categories_upper = {k: [w.upper() for w in v] for k, v in categories.items()}`) outside the loop.
## 2024-04-29 - Python Performance: Redundant String Allocations in Nested Loops
**Learning:** In Python, applying string transformations (e.g., `k.upper()`) to static dictionary values inside a nested loop causes redundant memory allocations and significant CPU overhead during every iteration.
**Action:** Extract and precalculate the transformed values into a new dictionary (e.g., `categories_upper = {k: [w.upper() for w in v] for k, v in categories.items()}`) outside the loop.
## 2025-05-18 - Replacing len(text.split()) with text.count(' ') is functionally incorrect
**Learning:** In Python, replacing `len(text.split())` with `text.count(' ') + 1` for word counting or token estimations is functionally incorrect because `split()` handles all whitespace characters (tabs, newlines, multiple spaces) and groups them, whereas `count(' ')` introduces logical bugs by ignoring other whitespaces and miscounting consecutive spaces.
**Action:** Do not use `text.count(' ') + 1` to replace `len(text.split())`. If performance is a critical issue without allocations, use regex iterators like `sum(1 for _ in re.finditer(r'\S+', text))` or stick to the highly optimized CPython `split()` for general cases.
## 2024-05-18 - Nested list comprehensions vs explicit loops for counting
**Learning:** Using `len([1 for x in y for z in x if condition])` causes unnecessary list allocation and generator overhead in Python, slowing down execution.
**Action:** Replace `len([1 for ...])` with standard `for` loops and a counter variable to prevent allocation overhead.
## 2024-05-18 - String conversions inside array iterators
**Learning:** In React/JavaScript frontend applications, calling string transformations like `.toLowerCase()` inside iterative array methods (e.g., `.filter()`, `.some()`) causes O(N) redundant string allocations.
**Action:** Precalculate these values outside the loop to improve rendering performance and memory efficiency.
## 2026-05-06 - Separating pre-calculation from active filtering in React
**Learning:** When optimizing React frontend search filters to avoid redundant string allocations (e.g., `.toLowerCase()`), separating the pre-calculation and filtering logic into two distinct `useMemo` hooks is crucial. Combining them executes the allocations on every keystroke, resulting in a de-optimization. The first `useMemo` must cache the pre-calculated search strings (dependent on the source data), and the second `useMemo` should handle the active filtering (dependent on the cached strings and search query).
**Action:** Always verify the dependency arrays of `useMemo` hooks when pre-calculating string values to ensure they do not re-run on frequent user inputs like search queries.

## 2024-05-18 - Avoid object cloning inside memoized filters
**Learning:** When optimizing React frontend search filters to avoid redundant string allocations, hoisting operations like `searchQuery.toLowerCase()` outside the `.filter()` loop into a `useMemo` hook is good, but mapping or cloning the original data array (e.g., `data.map(item => ({...item, searchStr}))`) just to cache search strings breaks object reference equality and causes unnecessary memory allocations that often outweigh the CPU savings.
**Action:** Filter the original array directly without cloning objects.

## 2024-05-18 - Avoid meaningless micro-optimizations
**Learning:** Extracting string operations (e.g., `.toLowerCase()`) from small, fixed-size array iterations (e.g., mapping over a 4-item status list) saves no measurable time and violates the rule against meaningless micro-optimizations.
**Action:** Only optimize string transformations or allocations when they occur inside O(N) loops operating on potentially large datasets or frequent user input events.

## 2026-05-18 - Pre-calculating strings using parallel arrays
**Learning:** When optimizing React search filters, using  to create objects containing the original item and the search string (e.g. ) causes unnecessary memory allocations and breaks object reference equality.
**Action:** Use parallel arrays for searchable strings (e.g. ) and filter the original array using the index: .

## 2026-05-18 - Pre-calculating strings using parallel arrays
**Learning:** When optimizing React search filters, using map() to create objects containing the original item and the search string (e.g. { doc, searchStr }) causes unnecessary memory allocations and breaks object reference equality.
**Action:** Use parallel arrays for searchable strings (e.g. const searchStrings = data.map(d => d.text.toLowerCase())) and filter the original array using the index: data.filter((_, i) => searchStrings[i].includes(query)).
## 2024-05-15 - React Component Primitive Array Filtering
**Learning:** Inside core React primitives like a Combobox that get reused frequently, string operations like `.toLowerCase()` inside iterative filtering cause redundant O(N) string allocations on every keystroke. Using `.map(item => ({...item, searchStr}))` is dangerous as it breaks object reference equality and memoization.
**Action:** Precalculate parallel arrays (e.g., `searchableLabels = options.map(opt => opt.label.toLowerCase())`) in a separate `useMemo` and use the index `(_, i)` to filter the original array, preserving references while eliminating per-keystroke allocations.
## 2024-05-18 - Pre-calculating combined search strings in parallel arrays
**Learning:** When optimizing React search filters to prevent redundant `.toLowerCase()` string allocations, if the search requires matching across multiple object fields (e.g. `item.title` and `item.source_id`), creating a single pre-calculated parallel array of combined strings (e.g. `` `${item.title} ${item.source_id}`.toLowerCase() ``) provides O(1) active search speed without breaking object reference equality.
**Action:** Use `useMemo` to pre-calculate combined string fields into a parallel array when multiple fields must be searchable, and use the array index `(_, index)` to filter the original array during active searches.
## 2024-10-24 - React Component Static Weights Dictionary Allocation
**Learning:** Defining static objects like lookup dictionaries (`STATUS_WEIGHTS`, `PRIORITY_WEIGHTS`) inside a React component or hook function causes them to be recreated on every single render cycle, wasting memory and CPU.
**Action:** Move static objects or constant lookup dictionaries outside the component or hook definition to prevent them from being reallocated on every render. Additionally, when using these dictionaries inside array sort comparators, retain `.toLowerCase()` for true case-insensitivity rather than expanding the dictionary with specific casing variations, as the latter is a flawed micro-optimization.
## 2024-05-24 - Expensive Hook Invocations
**Learning:** Found a severe anti-pattern where a hook returned a function (`hasPermission`) that executed O(N) array transformations, string allocations, and Set creations *on every invocation* during render, rather than pre-calculating the state based on dependencies.
**Action:** Always memoize derived state (like Set creation from arrays) outside of returned callback functions within hooks, ensuring expensive operations only run when underlying dependencies change.
## 2026-06-08 - Parallelizing sequential API requests in React hooks
**Learning:** Sequential network requests in React hooks (e.g., awaiting a blog post, then awaiting its context) create unnecessary network waterfalls that increase loading times for users, especially if the secondary request's inputs don't depend on the first request's output.
**Action:** Use Promise.all() (or parallel promise initialization) to run independent API calls concurrently. When doing so without Promise.all, initiate the promises early and await them independently within their existing try/catch blocks to prevent single failures from breaking the entire feature.

## 2024-06-09 - D3 Render Loop Allocation Churn
**Learning:** In React components that wrap D3 renderings (like `GanttView.tsx`), using inline object instantiations like `new Date(d.created_at)` inside `.map()` and `.attr()` callbacks during the D3 render phase causes massive redundant allocations on every React re-render. Since `d3.extent` and multiple `.attr` loops iterate over the data repeatedly, the same date strings are parsed multiple times per render.
**Action:** Pre-parse strings into native `Date` objects during the `useMemo` data-filtering stage. Map them onto the data objects once (e.g., `parsedCreatedAt`, `parsedDueDate`), and reference those pre-computed values directly in the D3 loop to prevent N*M allocations during render cycles.
## 2026-06-10 - Memoizing task grouping and sorting in BoardView
**Learning:** Using dynamic filtering functions like `tasks.filter(t => t.status === status).sort(...)` inside the render function of complex list views (like a Kanban board) causes O(N log N) work per column on every render. This becomes a severe bottleneck when the parent component tracks frequent state changes like `hoveredTaskId` during mouse movement.
**Action:** Replace dynamic per-column filtering with a single `useMemo` hook that groups and sorts all tasks into a dictionary object (`groupedTasks`) in a single pass. This reduces the time complexity from O(C * N log N) to O(1) during hover state updates, while safely updating only when the `tasks` dependency changes.
## 2024-05-24 - Inline Regex vs O(N) Map Allocation
**Learning:** In React components rendering lists (`KanbanView`, `ListView`), using a `useMemo` block to iterate over the entire array to create a dictionary of `.toLowerCase()` strings just for simple text matching (`includes('bot')`) is significantly slower than using an inline case-insensitive regular expression (`/bot/i.test()`). The map approach forces O(N) memory allocation and string mutations upfront on every state change.
**Action:** When performing simple text matching (like checking roles or names) inside a `.map()` render loop, prefer inline `/pattern/i.test()` over building intermediate lowercased lookup maps.
## 2025-05-18 - Replacing .toLowerCase().includes() with inline regex in list rendering loops
**Learning:** Using `string.toLowerCase().includes()` inside render functions that are executed many times per render cycle (like list items in a Kanban or Table view) causes a new lowercased string to be allocated in memory on every invocation. This leads to high Garbage Collection (GC) overhead and performance degradation during rapid state updates like mouse hovering.
**Action:** Replace `string.toLowerCase().includes(pattern)` with an inline case-insensitive regex test like `/pattern/i.test(string)` inside high-frequency render loops to prevent redundant string memory allocations.
## 2026-06-19 - Promise.all Optimization for RAG Settings
**Learning:** In frontend configuration services, sequentially fetching independent data endpoints (like different credential categories) creates unnecessary waterfall delays. Decoupling them with `Promise.all` is a highly effective, safe optimization that reduces the total execution time to the duration of the longest request, significantly improving UI responsiveness when loading configuration pages.
**Action:** When auditing data fetching functions, specifically look for sequential `await` calls that do not depend on each other's results, and refactor them into a single `Promise.all` block.
## 2026-06-20 - Expensive Intl.DateTimeFormat Instantiations
**Learning:** The `Intl.DateTimeFormat` constructor is a known slow operation in JavaScript. Instantiating it repeatedly inside render loops, like in `VictoryFeedList`'s map or `LiveClock`'s 1-second interval, causes massive CPU overhead and memory churn.
**Action:** Always hoist `Intl.DateTimeFormat` (and similarly expensive constructors like `Intl.NumberFormat` or `RegExp`) outside of React components and loop iterations to instantiate them exactly once upon module load.
## 2026-07-06 - Intl.DateTimeFormat RangeError Handling
**Learning:** `Intl.DateTimeFormat.prototype.format()` throws a `RangeError` when passed an invalid date (evaluating to NaN), unlike `Date.prototype.toLocaleDateString()` which safely returns "Invalid Date". When optimizing render loops by hoisting `Intl.DateTimeFormat`, failing to handle invalid dates will cause unhandled exceptions that crash the entire React component tree.
**Action:** Always wrap the hoisted `.format()` call in a helper function that explicitly checks for invalid dates (e.g., `isNaN(date.getTime())`) before formatting, preserving the safe fallback behavior of `toLocaleDateString()`.

## 2026-07-11 - Inline Regex Micro-Optimizations
**Learning:** Replacing string operations like `.toLowerCase().includes()` with inline case-insensitive regex (e.g., `/pattern/i.test()`) in standard UI render paths (e.g., small components or state machine transitions) is a rejected micro-optimization. It yields no measurable performance impact and carries a high risk of introducing TypeScript type coercion errors (e.g., `str && /pattern/.test(str)` evaluating to an empty string instead of a boolean when `str` is empty).
**Action:** Never propose inline regex as a replacement for simple string matching in cold paths. Focus on systemic memory allocations, like avoiding unhandled `Intl.DateTimeFormat` crashes or hoisting expensive loop allocations.

## 2024-05-24 - Intl.DateTimeFormat configuration for toLocaleString replacement
**Learning:** When optimizing render loops by hoisting `Intl.DateTimeFormat` to replace `Date.prototype.toLocaleString()`, the default `new Intl.DateTimeFormat(undefined)` only outputs the date (e.g., "10/24/2023"). This causes a functional regression for components that rely on exact timestamps (e.g., Audit Logs, System Health logs).
**Action:** Always pass explicit options (e.g., `{ year: 'numeric', month: 'numeric', day: 'numeric', hour: 'numeric', minute: 'numeric', second: 'numeric' }`) when replacing `.toLocaleString()` to preserve the time component, and abstract this into a reusable helper function.


## 2026-07-20 - Refactoring sequential async AI inference to concurrent asyncio.gather
**Learning:** When performing independent async AI inferences (like `_infer_need`) inside a loop over a list of items (e.g., job leads), using a sequential `for` loop with `await` creates a massive network waterfall bottleneck. This scales the execution time as O(N) instead of O(1) concurrent waiting time, severely slowing down processes like daily background data fetching.
**Action:** Specifically look for `for` loops containing independent `await` calls, especially those hitting external network APIs, and refactor them to execute concurrently using `asyncio.gather` to eliminate the waterfall delay.

## 2024-05-18 - Avoid redundant string allocations in Array.prototype.sort() comparators
**Learning:** Calling string methods like `.toLowerCase()` inside an `Array.prototype.sort()` comparator causes $O(N \log N)$ redundant string allocations during the sorting phase.
**Action:** When optimizing frontend performance, pre-calculate sorting weights or normalized strings in an $O(N)$ loop or `useMemo` block before executing the sort operation to eliminate redundant allocations.
## 2026-07-26 - Static lookup dictionaries for repeated inline strings
**Learning:** Extracting repeated string manipulation operations (e.g. `status.toLowerCase() === 'todo'`) inside a React component render loop into an external, static lookup dictionary (`STATUS_COLORS`) prevents unnecessary string memory allocations and provides faster O(1) attribute access per iteration.
**Action:** When optimizing React component performance, extract redundant inline string operations and conditional ternary chains evaluated during every render cycle into static O(1) lookup dictionaries defined outside the component.

## 2026-07-29 - Pre-calculating Date objects before array sorting
**Learning:** Calling  inside  comparators causes redundant O(N log N) string-to-date parsing overhead, creating a hidden performance bottleneck.
**Action:** Always pre-calculate parsed timestamps in an O(N) loop (e.g. into a Map or parallel array) before executing the sorting operation to ensure O(1) attribute access during the sort.

## 2026-07-29 - Pre-calculating Date objects before array sorting
**Learning:** Calling `new Date(string).getTime()` inside `Array.prototype.sort()` comparators causes redundant O(N log N) string-to-date parsing overhead, creating a hidden performance bottleneck.
**Action:** Always pre-calculate parsed timestamps in an O(N) loop (e.g. into a Map or parallel array) before executing the sorting operation to ensure O(1) attribute access during the sort.

## 2026-07-29 - Pre-calculating Date objects before array sorting
**Learning:** Calling `new Date(string).getTime()` inside `Array.prototype.sort()` comparators causes redundant O(N log N) string-to-date parsing overhead, creating a hidden performance bottleneck.
**Action:** Always pre-calculate parsed timestamps in an O(N) loop (e.g. into a Map or parallel array) before executing the sorting operation to ensure O(1) attribute access during the sort.

## 2024-05-24 - Pre-calculating lowercase lookup maps outside of Array.map render loops
**Learning:** In React components that render lists (like `IdentityMatrix`), calling `.find()` with `.toLowerCase()` transformations inside the `.map()` render loop causes O(N*M) redundant string memory allocations on every render cycle.
**Action:** Always pre-calculate case-insensitive lookup dictionaries (e.g., using `useMemo` and `Map`) outside of the render loop to guarantee fast O(1) property access without string allocations during iterative rendering.

## 2024-05-18 - Preserving Array.find() behavior with Map caching
**Learning:** When optimizing a loop by replacing `Array.prototype.find()` with a pre-calculated `Map` for $O(1)$ lookups, simply calling `map.set()` for every item creates a 'last match wins' regression, because `find()` inherently returns the *first* match.
**Action:** When converting `find()` to a `Map`, always ensure duplicate keys are handled gracefully to mimic `find()`'s 'first match' behavior by checking `if (!map.has(key)) { map.set(key, value); }`.
## 2026-07-29 - Pre-calculating Date parsing before array sorting
**Learning:** Calling `Date.parse(string)` inside `Array.prototype.sort()` comparators causes redundant O(N log N) string-to-date parsing overhead, creating a hidden performance bottleneck similar to `new Date().getTime()`.
**Action:** Always pre-calculate parsed timestamps in an O(N) loop (e.g. into a Map or parallel array) before executing the sorting operation to ensure O(1) attribute access during the sort.

## 2024-05-18 - Extracting inline React components from render functions
**Learning:** Defining a React component (e.g., `KanbanColumn`) inside the render function of its parent component (`BrandDashboardView`) causes React to create a new component type reference on every single parent render. This bypasses React's reconciliation engine, forcing it to unmount and entirely remount the DOM sub-tree on every state change, destroying local state and causing massive performance overhead.
**Action:** Always extract inline component definitions outside of the parent component's body. If the child component needs data or callbacks from the parent, pass them explicitly as props (e.g., `onUpdateStatus`, `columnPosts`).

## 2024-05-18 - Pre-calculating complex string manipulations with static lookup dictionaries
**Learning:** Performing multiple chained string manipulations like `status.toUpperCase().replace('_', ' ')` inside a `.map()` render loop allocates several new strings per item on every render cycle. This is significantly slower and generates more garbage collection overhead than retrieving a pre-formatted string from a dictionary.
**Action:** Extract repetitive and chained inline string operations into a static $O(1)$ lookup dictionary defined completely outside the component to prevent unnecessary memory allocations during list rendering.
## 2024-05-19 - Pre-calculating Date parsing before array sorting
**Learning:** Calling `new Date(string).getTime()` inside `Array.prototype.sort()` comparators causes redundant O(N log N) string-to-date parsing overhead, creating a hidden performance bottleneck.
**Action:** Always pre-calculate parsed timestamps in an O(N) loop (e.g. into a Map or parallel array) before executing the sorting operation to ensure O(1) attribute access during the sort.

## 2024-08-10 - Mapping arrays inside render cycles
**Learning:** Performing `Array.prototype.map()` inside the main body of a React component creates redundant object allocations on every render cycle, even if the underlying array data has not changed. This triggers unnecessary reconciliation effort and garbage collection overhead.
**Action:** When a computed array (like `feedSources` in `BrandDashboardView`) is derived from props or state using `.map()`, wrap the operation in `React.useMemo()` to guarantee that memory is only re-allocated when the dependencies genuinely change.

## 2026-08-11 - Pre-calculating lookup maps to replace Array.prototype.find() in render loops
**Learning:** Calling `Array.prototype.find()` inside React render loops or inside `Array.prototype.sort()` comparators causes O(N) or O(N log N) overhead on every render cycle. This scales poorly when the arrays grow large.
**Action:** Always pre-calculate lookup maps (using `useMemo` and `Map`) outside of the render loop to guarantee fast O(1) property access.

## 2026-08-12 - Re-evaluating inline string manipulations vs Object creation
**Learning:** Extracting simple inline string manipulations (like `.replace(/_/g, ' ').toUpperCase()`) into static caching dictionaries was flagged as a *non-blocking* nitpick during code review, as modern JS engines execute these in nanoseconds and property lookup overhead can sometimes cancel out theoretical benefits for very simple operations. However, for the sake of strict memory allocation reduction inside large render loops, it remains a valid micro-optimization. The more critical learning is the necessity of providing robust fallback logic (e.g., `|| r.replace('_', ' ').toUpperCase()`) to prevent functional regressions if unknown enums or data are passed to the UI.
**Action:** When creating static lookup dictionaries to replace runtime operations, *always* include a runtime fallback that performs the original operation for unknown keys, ensuring forward compatibility with backend data changes. Also, ensure dictionaries are not duplicated across files to adhere to DRY principles.

## 2024-05-24 - Extracting chained ternary string operations into static lookup dictionaries
**Learning:** Performing complex, chained ternary string operations inside a `.map()` render loop allocates several new strings per item on every render cycle. This is significantly slower and generates more garbage collection overhead than retrieving a pre-formatted string from a dictionary.
**Action:** Extract repetitive and chained inline string operations into a static $O(1)$ lookup dictionary defined completely outside the component to prevent unnecessary memory allocations during list rendering.
## 2025-02-15 - Memoizing Leaf Presentational Components in Lists
**Learning:** When rendering primitive-prop leaf components like badges (`PriorityBadge`, `StatusBadge`) inside large array mappings (`ListView`, `TableView`, `KanbanView`), they will needlessly re-render whenever the parent list state changes unless they are wrapped in `React.memo()`.
**Action:** Always verify if small, frequently rendered presentational components that compute styles based on primitive string props (like string replacement or lowercasing) are memoized to avoid multiplying CPU overhead by O(N) list items.

## 2026-08-17 - Optimize string operations in map loops
**Learning:** Using inline string manipulations like `.toUpperCase().replace('_', ' ')` inside a `.map()` render loop forces unnecessary string allocations and regex executions on every re-render.
**Action:** Pre-calculate and consolidate all possible formatted status string combinations into a single static O(1) lookup dictionary outside the React component.

## 2024-05-18 - Replacing O(N*M) nested render loop searches with O(1) module-level Maps
**Learning:** Performing nested loop searches using `Array.prototype.find()` inside a React component's render function to locate static config items creates an O(N*M) performance bottleneck that executes on every render cycle.
**Action:** When a component relies on static configuration data imported from another file, extract the lookup logic by pre-calculating a flat `Map` at the module level (outside the component). This guarantees O(1) constant-time property access during rendering without needing `useMemo` overhead.

## 2024-10-25 - React.memo Component Wrapping for Rendering Optimization
**Learning:** In heavily nested list view components (like `VictoryFeedList` rendering a long array of `ContentSource`), any unrelated state update in the parent layout component causes the entire list to completely re-render, creating an O(N) rendering bottleneck. Wrapping `Array.prototype.find()` in `useMemo` for tiny lists, or using `Map.get()` for < 5 item static configurations are anti-patterns due to the memory allocation overhead exceeding linear search performance.
**Action:** Always wrap leaf list view components (`VictoryFeedList`, `KanbanColumn`) with `React.memo` to intercept unnecessary reconciliation when parent component state updates. Do not attempt `useMemo` on primitive arrays or O(1) Dictionary conversions for arrays smaller than 5 items.
## 2024-05-18 - React.memo fails with unmemoized callbacks
**Learning:** When passing callback props (like `onEditRole`, `onViewActivity`) to a `React.memo()` optimized component inside a list (e.g. `TeamMemberCard`), if the parent component does not wrap these callbacks in `useCallback`, the shallow comparison will always fail on every render. This completely negates the benefit of `React.memo` and adds useless CPU overhead.
**Action:** Always verify that components utilizing `React.memo()` only receive memoized callback functions or static props from their parents, especially within map iterations.

## 2024-11-20 - Pre-calculating lookup maps to replace Array.prototype.find() in render loops with partial matching fallback
**Learning:** Calling `Array.prototype.find()` inside React render loops causes O(N*M) overhead on every render cycle. While exact matching (like `source_id`) can be easily optimized with a `Map` for O(1) lookups, fallback logic that requires partial matching (like `message?.includes(url)`) cannot be easily mapped.
**Action:** Always pre-calculate lookup maps (using `useMemo` and `Map`) outside of the render loop to guarantee fast O(1) property access for the exact match fast-path. Retain the `Array.prototype.find()` ONLY as a fallback for complex/partial matching conditions, ensuring the vast majority of items bypass the O(N) array scan.
## 2024-11-21 - Memoizing callback props to maintain list virtualization performance
**Learning:** When passing locally defined functions (like `getPermissionsForRole`) down to list item components that are rendered dynamically via `.map()`, creating a new function reference on every parent render destroys any potential for React's shallow comparison (like in `React.memo`) to optimize rendering. This forces $O(N)$ re-renders of list item subtrees even when their explicit props haven't conceptually changed.
**Action:** Always wrap functions passed to list items in `React.useCallback`, ensuring correct dependencies, to preserve the stable function identity required for child rendering optimizations.

## 2024-11-21 - Optimize repetitive enum string manipulations in map iterations
**Learning:** Using `Object.values(Enum).map(v => v.replace(/_/g, ' ').toUpperCase())` inside of a React render loop (e.g. for dropdowns in modals) causes unnecessary O(N) regex evaluation and string allocation for every render, creating a performance bottleneck when rendering lists.
**Action:** Extract this operation into a pre-calculated static array and a dictionary map in the types definition file to perform it exactly once at load time, and reuse the pre-calculated list inside render cycles, changing O(N) runtime overhead to O(1) property lookup.
