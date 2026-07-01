## 2023-10-27 - Button Loading States
**Learning:** Adding `animate-spin` to inline SVG icons inside buttons is a lightweight, low-friction way to significantly improve user feedback for asynchronous operations, especially in list views where global loading overlays are disruptive. Tracking the specific item ID in state is critical to avoid spinning all buttons simultaneously.
**Action:** When adding async operations to list items, always maintain a specific `processingId` in local state or the state machine instead of a generic `isProcessing` boolean.
