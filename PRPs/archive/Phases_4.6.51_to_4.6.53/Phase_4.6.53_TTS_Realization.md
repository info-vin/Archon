# Phase 4.6.53 實體發聲與戰情報告廣播 (TTS Realization)

## 1. 目標 (Objective)
將 `gemini-3.1-flash-tts-preview` 的 Text-To-Speech (TTS) 核心技術與前端系統 (5173/3737) 實體打通。我們將導入「動態 Prompt 劇本」管理，並為 Charlie 打造全新的「天氣預報式戰情報告」。

## 2. 核心釋疑與架構確認
*   **Prompt Manager 掛載點**: 沒錯！經過實體源碼追蹤 (`enduser-ui-fe/src/services/api/ops.ts`)，Prompt 管理介面確實是掛載於 **5173 (End-User UI)**。這符合我們在 Phase 4.6.49 確立的「Role-Based Access」策略，讓具備 `MCP_MANAGE` 或高階管理權限的 Charlie 或 Admin 能夠在主要的工作平台 (5173) 直接動態調整系統提示詞。
*   **TTS 範本動態化**: 未來所有的 TTS 導演筆記（如 `tts_marketing_pitch`, `tts_commander_briefing`）都會寫入資料庫的 `archon_prompts` 中，讓 5173 的管理員可以隨時調整語氣，而不需要重啟後端。

## 3. 應用場景規劃 (Use Cases)

### [場景一] Charlie 的日常報告：Manager Nexus「天氣預報」 (Weather Forecast Briefing)
這是一個將死板數據擬人化的極佳應用！與其讓 Charlie 盯著 Dashboard 尋找異常，不如在每天早上登入 `5173/nexus` 時，提供一段約 30 秒的語音簡報。
*   **資料匯總 (Data Gathering)**: 後端 API 蒐集前一天的 Stale Leads 數量、Alice/Bob 的轉換率與待審核任務。
*   **LLM 語義化轉譯 (Semantic Translation by Agent)**: 為了避免前端死板的字串拼接，後端接收到 JSON 狀態後，會先呼叫語言模型 (LLM)，並注入 `tts_commander_briefing` 提示詞，讓 Agent 將冰冷數據翻譯成溫暖的講稿。
    > `[Voice style: Charon] [calm and authoritative] 各位早安，我是 Archon。今天的專案「天氣」有些波動。目前有 3 筆潛在客戶處於「降溫」停滯狀態，需要您的立即關注... [laughs] 別擔心，Alice 的開發進度依然如陽光般耀眼。`
*   **動態生成與審計**: 每次的報告內容皆由 LLM 動態生成，不僅活潑多變，而且完整的文字講稿與 Token 消耗都會被記錄，符合企業的法遵審計與 ROI 控制。
*   **UI 呈現**: 在 Nexus 儀表板的標題列 (`NexusHeader.tsx`) 右側，放置一個類似 Apple Music 懸浮播放組件的 `[🎙️ 播放今日戰情報告]` 按鈕。點擊後展開顯示動態聲波圖 (Waveform)。

### [場景二] Bob 的行銷錄音室 (Brand Voice Studio)
*   **運作邏輯**: 在 5173 的 Marketing 介面中，針對自動生成的 Sales Pitch，增加一個「試聽講稿」功能。
*   **劇本生成**: `[Voice style: Puck] [enthusiastic and convincing] {pitch_content}`。

---

## 4. 實作任務 (Implementation Tasks)
- [ ] **Task 4.1**: 後端建立 `/api/audio/generate` 端點，以 `StreamingResponse` 串流回傳 `audio/wav`，全程 In-Memory 不佔用硬碟。
- [ ] **Task 4.2**: 建立並初始化 `tts_commander_briefing` 與 `tts_marketing_pitch` 至 Prompt Manager 資料庫。
- [ ] **Task 4.3**: 在 5173 前端實作共用的 `<AudioPlayer />` 波形與播放控制元件。
- [ ] **Task 4.4**: 實作 Charlie 的 Manager Nexus「天氣預報」API 與前端整合 (修改 `NexusHeader.tsx`)。

---

## 5. 附錄：歷史技術分析與決策報告 (Reference)

*(以下為 Phase 4.6.52 結案時的技術評估備忘錄，留作後續開發參考)*

### 5.1 音檔格式與播放器相容性 (WAV vs MP3)
| 特性 | WAV (目前實作) | MP3 / AAC | 
| :--- | :--- | :--- |
| **壓縮方式** | 無損未壓縮 (Raw PCM) | 破壞性高壓縮 |
| **生成成本** | **極低** (只要加 44 byte 標頭即可直接推播) | **較高** (伺服器需使用 FFmpeg 進行 CPU 編碼) |
| **播放器支援度**| Chrome, Safari, Edge, iOS/Android 皆 **100% 內建支援** | 皆 100% 支援 |

**決策**: Gemini TTS 吐出來預設為生肉 (Raw PCM)。為了減輕伺服器 CPU 負擔與延遲，初期我們將維持使用 **WAV** 並直接以串流 (Stream) 形式透過 HTTP Response 送給前端的 HTML5 `<audio>` 標籤播放。

### 5.2 儲存策略：資料夾 vs 串流
*   **In-Memory Streaming (一次性試聽)**: 像 Bob 的行銷試聽或 Charlie 的每日預報，這種「聽完即丟」的音訊，後端**不需要產生實體檔案**。API 會直接把 Bytes 吐給前端，全程只存在於記憶體中，既安全又節省硬碟。
*   **Cloud Storage (永久保存)**: 若未來有「保留法遵語音紀錄」的需求，則不可存在本地資料夾 (因容器重啟會被清空)，必須上傳至 Supabase Storage 並將公開 URL 存入 DB。

### 5.3 容錯機制：Tenacity 與 429/503 的終結
經過對 4.6 系列文件的物理掃描，我們確認了 `tenacity` 是針對 Gemini Free Tier 嚴苛限制的工業級解法：
*   **隨機抖動 (Jitter)**: 透過 `wait_exponential_jitter`，避免多個因 429 失敗的請求在同一個時間點一起重試，有效防止 503 的雪崩效應 (Thundering Herd)。
*   **精準攔截**: 自訂了 `custom_retry_condition`，僅針對 `429 (Rate Limit)` 或 `503 (Overloaded)` 觸發退避，其餘語法錯誤則立刻中斷。這取代了過去在 `ThreadingService` 中暴力的 32 秒強制等待機制。

### 5.4 UX 決策：播報按鈕的放置位置 (Nexus 面板上方 vs 全域側邊欄)
*   **選項 A (Nexus 面板上方 - 採用)**: 放在 `NexusHeader.tsx`。優點是情境高度結合，Charlie 能「邊聽邊看」下方的數據圖表，最符合「儀表板早報」的直覺。
*   **選項 B (全域側邊欄 - 捨棄)**: 放在 `MainLayout.tsx` 的 UserAvatar 下方。缺點是破壞導覽層級（將業務簡報按鈕與系統級的登出/設定混在一起），且在手機版或視窗縮小時會讓寶貴的側邊欄空間過於擁擠。
**決策**: 鎖定修改 `NexusHeader.tsx`，在右上方新增一個類似 Apple Music 的懸浮播放小組件 (Widget)。