## 2024-06-29 - Global Focus Visible States
**Learning:** Custom UI components without explicitly defined focus states become inaccessible to keyboard users, especially when the default browser focus ring is overridden or suppressed by Tailwind resets.
**Action:** Always include `focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-offset-2` variants when creating or modifying custom interactive elements (like custom Buttons) to guarantee keyboard navigability without compromising mouse user experience.
