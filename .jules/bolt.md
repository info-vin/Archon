## 2024-05-15 - [Pre-compiled Regex for Loop Performance]
**Learning:** Re-creating lists and doing substring checks (`any(p in s for p in list)`) inside tight loops (like model capability discovery) causes significant CPU overhead in Python due to repeated object allocation.
**Action:** Always extract static pattern lists into module-level variables. For optimal string matching performance in loops, compile them into regular expressions (`re.compile(r"pattern1|pattern2")`) and use `.search()`.
