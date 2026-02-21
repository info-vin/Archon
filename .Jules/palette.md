## 2025-05-24 - Custom Radio Group Accessibility
**Learning:** Custom "button-based" radio groups (like LevelSelector) that implement `role="radiogroup"` but lack roving tabindex logic (arrow keys) become inaccessible to keyboard users if they enforce `tabIndex="-1"` on unselected items. This traps users on the selected item.
**Action:** For simple custom radio groups, either implement full roving tabindex with arrow key support OR allow all items to be naturally tabbable (remove `tabIndex` manipulation) so users can navigate via Tab key.
