# Archon UI 介面標準規範

**對象**：執行自動化 UI 審計與重構的 AI 代理人
**目的**：UI 模式、違規行為與自動化檢測的唯一事實來源
**用法**：執行 `/archon:archon-ui-consistency-review` 以針對這些標準掃描程式碼

---

## 1. TAILWIND V4

### 規則
- **禁止動態類別建構** - Tailwind 在建構時會將原始碼視為純文字掃描
  - 絕對禁止： `` `bg-${color}-500` ``, `` `ring-${color}-500` ``, `` `shadow-${size}` ``
  - 應改用靜態查找物件 (Static Lookup Objects)
- **CSS 變數中使用原始 HSL 值** - 禁止包裹 `hsl()`
  - 正確：`--background: 0 0% 98%;`
  - 錯誤：`--background: hsl(0 0% 98%);`
- **任意值中允許使用 CSS 變數** - 工具名稱必須是靜態的
  - 正確：`bg-[var(--accent)]`
  - 錯誤： `` `bg-[var(--${colorName})]` ``
- **使用內聯 @theme** 將 CSS 變數映射到 Tailwind 工具類
- **定義 @custom-variant dark** - 這是讓 `dark:` 在 v4 中運作的必要條件

### 反面模式 (Anti-Patterns)
```tsx
// ❌ 動態類別 (不會產生 CSS)
const color = "cyan";
<div className={`bg-${color}-500`} />
<div className={`focus-visible:ring-${color}-500`} />  // 常見遺漏！

// ❌ 使用內聯樣式處理視覺 CSS
<div style={{ backgroundColor: "#fff" }} />
```

### 正確範例
```tsx
// ✅ 離散變體的靜態查找
const colorClasses = {
  cyan: "bg-cyan-500 text-cyan-900 ring-cyan-500",
  purple: "bg-purple-500 text-purple-900 ring-purple-500",
};
<div className={colorClasses[color]} />

// ✅ 動態值的 CSS 變數
<div
  className="bg-[var(--accent)] ring-[var(--accent)]"
  style={{ "--accent": "oklch(0.75 0.12 210)" }}
/>
```

---

## 2. 佈局與響應式 (LAYOUT & RESPONSIVE)

### 規則
- **響應式網格 (Responsive grids)** - 絕對禁止在沒有斷點的情況下設定固定列數
  - 應使用：`grid-cols-1 md:grid-cols-2 lg:grid-cols-4`
- **限制水平捲動** - 父層必須具備 `w-full` 或 `max-w-*`
- **隱藏捲動軸** - 為所有 `overflow-x-auto` 容器添加 `scrollbar-hide`
- **Flex 父層必須具備 min-w-0** - 若包含捲動容器，這能防止頁面異常擴張
- **文字截斷** - 務必使用 `truncate`, `line-clamp-N`, 或 `break-words`
- **桌面優先 (Desktop-primary)** - 優先針對桌面版優化，再向下添加響應式斷點

### 反面模式
```tsx
// ❌ 固定網格 (會破壞手機版)
<div className="grid grid-cols-4">

// ❌ 未受限的捲動 (導致整個頁面可水平捲動)
<div className="overflow-x-auto">
  <div className="min-w-max">

// ❌ 缺少 min-w-0 的 Flex 父層 (導致頁面撐開)
<div className="flex gap-6">
  <main className="flex-1">  {/* 缺少 min-w-0！ */}
    <div className="overflow-x-auto">
```

---

## 3. 主題化 (THEMING)

### 規則
- **每個可見顏色都需要 `dark:` 變體**
- **主題間結構一致** - 僅改變顏色/透明度
- **使用 Token** - 同時定義淺色與深色 Token (`--bg` 並在 `.dark` 中重新定義)

### 正確範例
```tsx
// ✅ 兼顧雙主題
<div className="bg-white dark:bg-black text-gray-900 dark:text-white">
```

---

## 4. RADIX UI

### 規則
- **使用 Radix Primitives** - 絕對禁止使用原生 `<select>`, `<input type="checkbox">`, `<input type="radio">`
- **使用 asChild 組合** - 不要包裹，而是將行為附加到你的組件上
- **透過 Data Attributes 設定樣式** - `[data-state="open"]`, `[data-disabled]`
- **對覆蓋層 (Overlays) 使用 Portal** - 並確保正確的 z-index
- **同時支援受控 (Controlled) 與非受控 (Uncontrolled) 模式** - 所有表單組件必須在兩種模式下皆能運作

### 受控 vs 非受控表單組件

**關鍵鐵律**：表單組件（Switch, Checkbox, Select 等）必須同時支援受控與非受控模式。

---

## 5. 中央樣式管理 (styles.ts)

### 關鍵鐵律：務必使用 styles.ts 中的 glassCard 與 glassmorphism

**位置**：`@/features/ui/primitives/styles.ts`

所有樣式定義必須來自 `styles.ts` 中的中央物件。禁止在組件中重複定義樣式物件。

### 正確範例
```tsx
// ✅ 正確 - 使用中央定義
const edgeStyle = glassCard.edgeColors[edgeColor];
<div className={edgeStyle.border}>
  <div className={edgeStyle.solid} />
  <div className={edgeStyle.gradient} />
</div>

// ✅ 正確 - 使用 glassCard 變體
const glowVariant = glassCard.variants[glowColor];
<div className={cn(glowVariant.border, glowVariant.glow, glowVariant.hover)} />
```

---

## 6. 無障礙性 (ACCESSIBILITY)

### 規則
- **所有互動元素必須具備鍵盤支援**
  - `<div onClick={...}>` 需要 `role="button"`, `tabIndex={0}`, `onKeyDown`
  - 需處理 Enter 與 Space 鍵
- **ARIA 屬性** - `aria-selected`, `aria-current`, `aria-expanded`, `aria-pressed`
- **絕對禁止移除焦點框 (Focus Rings)** - 必須是特定顏色且靜態的
- **僅圖示按鈕必須具備 aria-label** - 螢幕閱讀器必要
- **裝飾性圖示必須具備 aria-hidden="true"** - 防止閱讀器朗讀

---

## 7. TYPESCRIPT 與 API 規範

### 規則
- **非同步函式回傳 Promise<void>** - 若被 await，則不應僅標註為 `void`
- **所有 Prop 必須被使用** - 介面中的 Prop 必須影響渲染
- **顏色類型一致性** - 全系統統一使用 "green" 而非 "emerald" (完全避免使用 emerald)
- **執行 `tsc --noEmit`** 以捕捉型別錯誤
- **對查找物件使用 `satisfies`** - 強制顏色變體的型別覆蓋
- **120 字元行長限制** - 將長 class 字串拆分為陣列並使用 `.join(" ")`

---

## 評分標準 (SCORING VIOLATIONS)

### 致命錯誤 (Critical, 每個 -3 分)
- 動態類別建構 (Dynamic class construction)
- 互動元素缺少鍵盤支援
- 非響應式網格導致水平捲動
- TypeScript 型別錯誤

### 高優先級 (High, 每個 -2 分)
- 未受限的捲動容器
- Prop 沒做事 (Unused props)
- 功能不全的 UI 邏輯 (篩選/排序/拖放)
- 缺少深色模式變體

### 中優先級 (Medium, 每個 -1 分)
- 原生 HTML 表單元素
- 硬編碼的毛玻璃效果 (Hardcoded glassmorphism)
- 缺少文字截斷處理
- 顏色類型不一致

**評等標準：**
- 0 個致命錯誤：A (9-10/10)
- 1 個致命錯誤：B (7-8/10)
- 2-3 個致命錯誤：C (5-6/10)
- 4 個以上致命錯誤：F (1-4/10)
