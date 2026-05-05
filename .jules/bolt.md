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
