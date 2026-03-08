## 2024-05-18 - String split vs find for extracting occurrences
**Learning:** Using `string.find("```", pos)` inside a while loop to extract all occurrences in a large text is significantly slower (~30-50% slower) than simply using `string.split("```")` and calculating the positions, or using `re.finditer`.
**Action:** When extracting all positions of a substring in a large document, prefer `re.finditer` or string splitting with length accumulation instead of sequential `.find()` calls in a while loop.

## 2024-05-18 - Pre-compiled arrays vs inline arrays in loops
**Learning:** Defining constant arrays (like lists of stop words or syntax indicators) inside a function that runs in a tight loop is surprisingly costly due to repeated object creation and allocation overhead in Python. Pulling them out into module-level constants speeds up execution.
**Action:** Always extract constant reference lists and tuples to module-level variables (e.g. `_DOC_INDICATORS`) when used inside loops, especially in text processing functions like `extract_code_blocks`.
