---
name: "Phase 4.2.1: Sales Intelligence Implementation Detail (銷售情資實作技術規格)"
description: |
  A detailed technical specification for the Sales Intelligence module, bridging the gap between high-level business goals and actual code implementation.
  (銷售情資模組的詳細技術規格書，旨在填補高層商業目標與實際程式碼實作之間的落差。)

---

# 1. 業務交付成果 (Business Deliverables)
> **給非技術同事的摘要 (Summary for Non-Technical Colleagues)**
> 本階段我們將交付一套「自動化業務開發助手」，具體包含以下三項成果：

### A. 潛在客戶捕捉器 (Lead Capture System)
*   **功能**: 系統會自動將我們搜尋到的「正在招募的公司」轉換為「潛在客戶名單」。
*   **情境**: 當你在系統搜尋「數據分析師」職缺時，系統不僅顯示職缺，還會自動將發布職缺的公司（例如：某某零售公司）存入我們的客戶資料庫，並標記他們的需求為「需要 BI 工具」。
*   **價值**: 讓業務不再需要手動 Excel 記錄客戶，搜尋即建檔。

### B. 智能話術生成器 (Smart Pitch Generator)
*   **功能**: 點擊一個按鈕，系統會根據客戶的痛點，寫好一封引用了我們成功案例的開發信。
*   **情境**: 針對上述的「某某零售公司」，系統會自動生成一封信：「您好，看到貴司正在招募數據分析師，分享一個我們協助零售業提升 30% 營收的案例給您參考...」
*   **價值**: 確保每位業務發出的信件都具備高品質與高關聯性，大幅縮短備課時間。

### C. 內容資產庫 (Content Assets)
*   **功能**: 我們將預先建立兩篇高品質的「成功案例」文章，供系統引用。
*   **內容**:
    1.  **行銷趨勢文**: 「2025 年數據驅動行銷的五大趨勢」——用於吸引行銷主管。
    2.  **銷售案例文**: 「零售巨頭如何利用數據分析提升 30% 營收」——用於說服技術/業務主管。

---

# 2. 技術實作規格 (Technical Specifications)
> **給開發者的藍圖 (Blueprint for Developers)**

## 2.1 資料庫設計 (Database Schema)
*File: `migration/006_create_sales_intel_tables.sql`*

我們需要兩個新資料表來支撐上述功能：

```sql
-- 1. 潛在客戶表 (Leads Table)
-- 用於儲存從外部來源 (如 104) 識別出的潛在客戶
CREATE TABLE leads (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    company_name TEXT NOT NULL,          -- 公司名稱 (e.g. Retail Corp)
    source_job_url TEXT,                 -- 來源職缺連結 (e.g. 104 URL)
    status TEXT DEFAULT 'new',           -- 狀態: new (新名單), contacted (已聯繫), qualified (合格), converted (已成交)
    identified_need TEXT,                -- 識別出的需求 (e.g. "Hiring Data Analyst -> Needs BI Tool")
    assigned_sales_id UUID REFERENCES auth.users(id), -- 分配給哪位業務 (可為 NULL)
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- 2. 市場洞察表 (Market Insights Table)
-- 用於儲存 Agent 分析後的摘要與關聯文章建議
CREATE TABLE market_insights (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    keyword TEXT NOT NULL,               -- 搜尋關鍵字 (e.g. "Business Analyst")
    insight_summary TEXT,                -- Agent 生成的市場分析摘要
    related_blog_id UUID REFERENCES blog_posts(id), -- 建議搭配的部落格文章 (作為銷售素材)
    created_at TIMESTAMPTZ DEFAULT NOW()
);
```

## 2.2 假資料注入計畫 (Mock Data Injection)
*File: `migration/seed_blog_posts.sql` (Update)*

為了讓「智能話術生成器」有素材可引用，我們必須注入兩篇特定的 Blog Post：

### Case 4: Marketer (Inbound Lead Gen)
*   **Title**: 2025年商業數據分析的五大趨勢
*   **Slug**: `2025-data-analytics-trends`
*   **Concept**: 討論企業為何需要數據化營運，文末帶入 Archon 的分析功能。

### Case 5: Sales Rep (Sales Collateral)
*   **Title**: 零售巨頭如何利用數據分析提升 30% 營收
*   **Slug**: `retail-success-story-30-percent-growth`
*   **Concept**: 一個具體的 Case Study，描述某零售商使用我們的工具後解決了庫存問題。這是 **Sales Pitch** 生成時必須引用的核心文章。

## 2.3 端對端驗證劇本 (Integration/E2E Verification Scenario)
*File: `enduser-ui-fe/tests/e2e/sales-intelligence.spec.tsx`*

我們將使用 **Vitest + React Testing Library + MSW** 模擬完整的業務操作流程。

**測試目標**: 驗證「搜尋 -> 識別 -> 生成話術」的完整迴路。

```typescript
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { http, HttpResponse } from 'msw';
import { setupServer } from 'msw/node';
import MarketingPage from '@/pages/MarketingPage';

// 1. 設定 Mock Server (MSW)
const server = setupServer(
  http.get('/api/marketing/job-search', () => {
    return HttpResponse.json({
      results: [
        { company: "Retail Corp", jobTitle: "Senior Data Analyst", url: "http://mock-104/job1" }
      ]
    });
  })
);

beforeAll(() => server.listen());
afterEach(() => server.resetHandlers());
afterAll(() => server.close());

test('Sales Rep flows: Search, Identify Lead, Generate Pitch', async () => {
  render(<MarketingPage />);

  // 2. 執行搜尋
  const input = screen.getByPlaceholderText(/輸入職稱/i);
  fireEvent.change(input, { target: { value: 'Data Analyst' } });
  fireEvent.click(screen.getByText(/Analyze Market/i));

  // 3. 驗證潛在客戶識別 (Verify Lead Identification)
  await waitFor(() => {
    expect(screen.getByText('Retail Corp')).toBeInTheDocument();
  });
  expect(screen.getByText(/Potential Need: BI Tool/i)).toBeInTheDocument();

  // 4. 生成話術 (Generate Pitch)
  fireEvent.click(screen.getByText(/Generate Pitch/i));

  // 5. 驗證話術內容 (Verify Content)
  await waitFor(() => {
    const textarea = screen.getByDisplayValue(/零售巨頭如何利用數據分析/i);
    expect(textarea).toBeInTheDocument();
    expect(textarea.value).toContain('Retail Corp');
  });
});
```

---

# 3. 執行檢查清單 (Execution Checklist)

- [ ] **DB Migration**: 建立 `006_create_sales_intel_tables.sql` 並執行遷移。
- [ ] **Seed Data**: 更新 `seed_blog_posts.sql` 並重新注入資料。
- [ ] **Backend API**: 更新 `job_board_service.py` 以實作資料寫入邏輯 (寫入 `leads` 表)。
- [ ] **Frontend UI**: 更新 `MarketingPage.tsx` 以顯示識別出的 Leads 並觸發話術生成。
- [ ] **E2E Test**: 撰寫並通過 `sales-intelligence.spec.tsx`。
