## 2026-07-15 - Found Missing ARIA Loading States
**Learning:** Found that loading/disabled buttons (like the ClockInWidget button) often use standard HTML `disabled` but lack the corresponding `aria-disabled` and `aria-busy` attributes necessary for screen readers to announce loading states effectively. They also sometimes lack visible keyboard focus rings.
**Action:** Always verify that interactive loading states include `aria-busy` and `aria-disabled` alongside standard `disabled` and ensure `focus-visible` is implemented.
