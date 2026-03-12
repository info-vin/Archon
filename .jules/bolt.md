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
