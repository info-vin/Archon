## 2024-05-24 - Inline RegExp vs useMemo Parallel String Arrays
**Learning:** In the `ComboBox` component, creating parallel arrays containing `toLowerCase()` strings inside `useMemo` specifically for case-insensitive filtering caused unnecessary up-front memory allocation.
**Action:** Replace `useMemo` array transformations with an inline `RegExp` pattern match when doing simple case-insensitive substring searches to reduce memory bloat in frequently rendered components like ComboBoxes.

