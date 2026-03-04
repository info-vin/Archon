## 2024-03-01 - [Disabled States and Click Feedback]
**Learning:** Native `disabled` buttons swallow `onClick` events, preventing any embedded helpful alerts or warnings from firing (e.g., `if (!title) alert(...)`). When relying on a button's disabled state for validation, users receive zero feedback on *why* it's disabled unless explicitly communicated.
**Action:** Always provide a `title` attribute or an ARIA tooltip explaining *why* an action is currently unavailable when conditionally disabling a button.
