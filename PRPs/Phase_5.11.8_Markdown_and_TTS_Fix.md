# Phase 5.11.8: Frontend Markdown Rendering & TTS Resilience Fix

## 1. 任務背景與問題描述 (Background & Issues)
在進行 Brand Hub 行銷草稿生成與審查流程時，發現以下三個連鎖問題：
1. **TTS 語音崩潰 (TTS Failure)**：點擊 Workbench 上的 "Play Audio" 時，系統報錯 `Failed` (HTTP 500)。
2. **封面照片遺失 (Missing Cover Photo)**：將文章送出至 Approvals 後，審查畫面未能顯示封面圖片。
3. **Markdown 排版失效 (Missing Markdown Styles)**：在 Gatekeeper Console (Approvals) 中，包含 Markdown 語法（如 `# 標題`）的草稿，視覺上全數被渲染成無格式的純文字，無法進行有效閱讀與審查。

## 2. 物理鑑識與根本原因 (Root Cause Analysis)

### 2.1 TTS 崩潰與封面照片遺失
- **問題根源**：AI 生成的草稿首行通常為帶有龐大 Base64 編碼的 SVG 圖片語法 `![AI Image](data:image/svg+xml;base64,PHN2Zy...)`。
- **觸發機制**：`EditorBody.tsx` 中的 `<AudioPlayer>` 在未過濾的情況下，直接擷取草稿的前 500 個字元送交後端。這導致 Google Gemini TTS API 接收到無意義的 Base64 亂碼，進而因無法解析或觸發 Safety Filter 而拋出失敗。
- **連鎖反應**：為了讓 TTS 發聲，使用者必須「手動刪除」草稿中的圖片語法。但此舉導致在按下 Submit 時，`useBrandLogic.ts` 內的 `cleanAIImageReference` 函數無法擷取到圖片 URL，使得資料庫 `blog_posts` 的 `image_url` 變成 `None`，最終導致審核台失去封面圖片。

### 2.2 Markdown 排版失效
- **問題根源**：Tailwind CSS 的預設行為 (Preflight) 會清除所有 HTML 標籤（包含 `<h1>`, `<h2>`, `<ul>` 等）的預設樣式。
- **觸發機制**：在 `ContentReviewPanel.tsx` 中，開發者使用了 `<ReactMarkdown>` 元件來渲染文章，但並未對其套用 Tailwind Typography 的專屬類別 (`prose`)，導致渲染出的 HTML 標籤全數失去樣式，視覺上退化為純文字。

## 3. 修復計畫 (Proposed Changes)

本計畫嚴格遵守 SSOT 原則，不更動資料庫與後端架構，純粹進行前端組件的資料清洗與樣式歸位。

### 3.1 修正 TTS 資料流清洗
- **目標檔案**：`enduser-ui-fe/src/features/marketing/components/workbench/EditorBody.tsx`
- **修改邏輯**：在傳遞文字給 `<AudioPlayer>` 之前，使用正規表達式 `replace(/!\[.*?\]\(.*?\)/g, '')` 動態過濾掉所有的 Markdown 圖片語法，然後才擷取前 500 個字元。
- **效益**：確保 TTS 永遠只收到乾淨的人類可讀文本，徹底解決崩潰問題。同時保留編輯器內的圖片，讓後續的 Submit 流程能正常萃取封面照。

### 3.2 歸位 Markdown 渲染樣式
- **目標檔案**：`enduser-ui-fe/src/features/manager/components/ContentReviewPanel.tsx`
- **修改邏輯**：在 `<ReactMarkdown>` 的父容器或元件上，加入 `@tailwindcss/typography` 提供的樣式類別：`className="prose prose-indigo dark:prose-invert max-w-none"`。
- **效益**：恢復 H1~H6、粗體、清單等排版視覺，讓管理層在審查文章時能獲得正確且美觀的閱讀體驗。

## 4. 驗證計畫 (Verification Plan)
1. 進入 Brand Hub，生成包含 `![AI Image]` 的草稿，點擊 Play Audio 確認語音能正常播放且不報錯。
2. 直接點擊 Submit 送出草稿，確認不需要手動刪除圖片。
3. 進入 Approvals 畫面，確認草稿清單能正確顯示截取出的封面照片。
4. 點開草稿內容，確認 `# 標題` 等 Markdown 語法能被正確渲染為大字體與粗體排版。
