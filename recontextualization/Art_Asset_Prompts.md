# Archon: Phase 5.8.7 AI 美術提示詞清單 (Art Prompts Library)

這份文件用於管理所有需要透過 SDXL / Flux 生成的靜態美術圖。
您可以直接複製下方各項目的 `[Prompt & Settings]` 區塊，該區塊已內含所有生成與壓縮的警告提醒，方便您一次性複製貼上。

---

## 1. 環境背景 (Environments)

### 1.1 戰鬥場景背景 (GameBoard Background)
* **目標檔案**：`recontextualization/assets/images/bg_vector_grid.png`
* **主題**：深邃的量子資料庫內部，呈現《駭客任務》般強烈的假 3D 視覺縱深與無限網格。
* **Prompt & Settings**:
  ```text
  POV flying into the matrix, an infinite 3D wireframe cyberspace grid tunnel, extreme deep perspective with a distant vanishing point, glowing neon digital rain cascading down invisible walls, retro-futuristic hacker aesthetic, intense faux-3D virtual reality depth of field, high contrast black background with vibrant glowing lines, cinematic motion blur, crisp game asset, sci-fi concept art.
  --ar 16:9
  (⚠️ 畫師/產圖工具注意：匯出解析度限制 1920x1080, 儲存為 .webp 或壓縮 .png)
  ```
* **Negative Prompt**:
  > text, watermark, characters, people, UI elements, bright light.

### 1.2 合成工坊背景 (Workshop Background)
* **目標檔案**：`recontextualization/assets/images/bg_synthesizer.png`
* **主題**：高溫、充滿電火花與機械臂的卡牌量子融合爐。
* **Prompt & Settings**:
  ```text
  A high-tech quantum synthesizer furnace in a dark cyberpunk laboratory, intense glowing orange and amber core, electrical sparks, heavy industrial machinery, holographic blueprints floating in the air, cinematic lighting, dramatic shadows, highly detailed concept art.
  --ar 16:9
  (⚠️ 畫師/產圖工具注意：匯出解析度限制 1920x1080, 儲存為 .webp 或壓縮 .png)
  ```
* **Negative Prompt**:
  > text, people, bright room, clean sterile environment.

---

## 2. 實體卡牌圖示 (Card Icons)

### 2.1 黃金資料晶片 (Data Core / Target Chunk)
* **目標檔案**：`recontextualization/assets/images/chip_green_target.png`
* **主題**：極具價值的無污染資料核心。
* **Prompt & Settings**:
  ```text
  A glowing emerald green cyberpunk microchip, intricate golden circuit patterns, floating in dark void, high contrast, macro photography, 3d render, glowing edges, highly detailed sci-fi tech artifact.
  --ar 1:1
  (⚠️ 畫師/產圖工具注意：匯出解析度限制 512x512, 背景需為黑色或透明的 .png/.webp)
  ```

### 2.2 毒性雜訊晶片 (Noise / Corrupted Chunk)
* **目標檔案**：`recontextualization/assets/images/chip_red_noise.png`
* **主題**：遭到病毒感染、破圖與閃爍的危險資料。
* **Prompt & Settings**:
  ```text
  A corrupted cyberpunk microchip, glowing sinister crimson red, fractured and shattered edges, digital glitch effects, dark void background, high contrast, macro photography, dangerous aura, highly detailed sci-fi tech artifact.
  --ar 1:1
  (⚠️ 畫師/產圖工具注意：匯出解析度限制 512x512, 背景需為黑色或透明的 .png/.webp)
  ```

---

## 3. 行動卡圖示 (Action Cards)

### 3.1 Keyword Search (L1)
* **目標檔案**：`recontextualization/assets/images/action_keyword.png`
* **主題**：精準的狙擊鎖定。
* **Prompt & Settings**:
  ```text
  A minimalist futuristic sniper crosshair symbol, glowing neon cyan, geometric shapes, cyberpunk UI element, dark background, sharp lines, highly detailed 2d vector art style.
  --ar 1:1
  (⚠️ 畫師/產圖工具注意：匯出解析度限制 512x512, 背景需為黑色或透明的 .png/.webp)
  ```

### 3.2 Dense Vector (L2)
* **目標檔案**：`recontextualization/assets/images/action_dense.png`
* **主題**：深層穿透的雷射光束。
* **Prompt & Settings**:
  ```text
  A futuristic glowing laser beam piercing through digital layers, neon purple and blue, geometric cyberpunk UI element, dark background, sharp lines, dynamic composition, highly detailed 2d vector art style.
  --ar 1:1
  (⚠️ 畫師/產圖工具注意：匯出解析度限制 512x512, 背景需為黑色或透明的 .png/.webp)
  ```

### 3.3 Reranker (L3)
* **目標檔案**：`recontextualization/assets/images/action_reranker.png`
* **主題**：完美的六角形量子護盾/重組器。
* **Prompt & Settings**:
  ```text
  A glowing neon gold hexagonal energy shield, complex geometric fractal patterns inside, cyberpunk UI element, dark background, sharp lines, highly detailed 2d vector art style.
  --ar 1:1
  (⚠️ 畫師/產圖工具注意：匯出解析度限制 512x512, 背景需為黑色或透明的 .png/.webp)
  ```

---

## 4. 轉場動畫 (Video Transitions)

這些檔案將作為 Godot `VideoStreamPlayer` 播放的動態影片。因應不同階段的過渡需求，我們將轉場拆分為 **5 支精準的短影片**。
您只需要產出 **.mp4** 格式的影片放進資料夾，我會用自動化腳本將它們轉檔為 Godot 支援的 `.ogv` 格式。

### 4.1 遊戲啟動/主選單開場 (Archon OS Bootup)
* **目標檔案**：`recontextualization/assets/vfx/transition_os_boot.mp4`
* **用途**：玩家剛開啟遊戲、進入主選單時的宏觀開場（建議總長約 3~6 秒，可生成完整影片後由剪輯軟體加速或裁切）。
* **Prompt & Settings**:
  ```text
  A fast-paced retro-futuristic hacker operating system boot screen, monolithic cyberpunk terminal, glowing monochrome green phosphor text rapidly scrolling, geometric logos quickly flashing on a deep black background, short visual blast, extremely detailed UI design, crisp game asset, cinematic lighting, highly detailed tech art.
  --ar 16:9
  (⚠️ 注意：請生成動態完整的影片後再自行裁切至 3~6 秒，儲存為 .mp4 供 Agent 轉檔)
  ```

### 4.2 戰鬥開場 (Uplink Established)
* **目標檔案**：`recontextualization/assets/vfx/transition_battle_intro.mp4`
* **用途**：從選單切換至戰鬥場景時，呈現「潛入節點」的流暢影片（建議總長約 3 秒，可生成完整影片後由剪輯軟體加速或裁切）。
* **Prompt & Settings**:
  ```text
  POV flying forward rapidly into a futuristic cyberpunk hacking interface initializing, quick transition, a massive glowing neon blue gateway quickly bursting open in cyberspace, data streams rushing forward in high speed perspective, intense motion blur effect, fast-paced action, crisp game asset, cinematic lighting, highly detailed tech art.
  --ar 16:9
  (⚠️ 注意：請生成動態完整的影片後再自行裁切至 3 秒，儲存為 .mp4 供 Agent 轉檔)
  ```

### 4.3 戰鬥勝利 (Data Extracted)
* **目標檔案**：`recontextualization/assets/vfx/transition_victory.mp4`
* **用途**：打敗所有病毒時的過關影片（建議總長約 5 秒，可生成完整影片後由剪輯軟體加速或裁切）。
* **Prompt & Settings**:
  ```text
  Fast-paced triumphant cyberpunk victory screen background, glowing emerald green geometric patterns rapidly expanding, quick transition, bright neon light burst, floating holographic data cubes being quickly secured, dark cyberspace background, highly detailed tech art.
  --ar 16:9
  (⚠️ 注意：請生成動態完整的影片後再自行裁切至 5 秒，儲存為 .mp4 供 Agent 轉檔)
  ```

### 4.4 戰鬥失敗 - 破圖警告 (System Compromised)
* **目標檔案**：`recontextualization/assets/vfx/transition_defeat_glitch.mp4`
* **用途**：SLA 歸零瞬間，遭受致命打擊的紅色強烈破圖警告影片（建議總長約 2 秒，非常短促，建議剪輯軟體裁切）。
* **Prompt & Settings**:
  ```text
  Severe rapid digital glitch art, screen tearing, short visual blast, intense glowing crimson red warning signals violently flashing, quick transition, distorted typography and rapid pixel sorting effects, dark cyberspace environment, high contrast, terrifying fast-paced atmosphere.
  --ar 16:9
  (⚠️ 注意：請生成動態完整的影片後再自行裁切至 2 秒，儲存為 .mp4 供 Agent 轉檔)
  ```

### 4.5 戰鬥失敗 - 斷電停機 (Connection Terminated)
* **目標檔案**：`recontextualization/assets/vfx/transition_defeat_shutdown.mp4`
* **用途**：破圖警告之後，接續的系統強制斷電影片（建議總長約 3 秒，可生成完整影片後由剪輯軟體裁切）。
* **Prompt & Settings**:
  ```text
  A dead cyberpunk terminal screen rapidly powering down, rapid transformation, fast fading glowing red embers, quick transition to a cracked screen glass reflecting a dark empty void, deep shadows, cinematic lighting, melancholic cyber atmosphere.
  --ar 16:9
  (⚠️ 注意：請生成動態完整的影片後再自行裁切至 3 秒，儲存為 .mp4 供 Agent 轉檔)
  ```

## 5. 玩家階級與徽章 (Player Ranks & Badges)

為了配合 Phase 5.8.6 實裝的「權限評級 (Clearance Rating)」與「認知等級 (Cognitive Level)」系統，我們需要幾款駭客階級徽章，用於玩家個人檔案與通關結算畫面的展示。

### 5.1 權限階級 C (Rank C: Script Kiddie)
* **目標檔案**：`recontextualization/assets/images/badge_rank_c.png`
* **主題**：初階駭客，生鏽或青銅材質的基礎電路徽章。
* **Prompt & Settings**:
  ```text
  A minimalist cyberpunk rank badge, bronze and rusted copper texture, simple geometric circuit patterns, dimly lit, dark background, 2d vector art style, game UI icon, sharp edges.
  --ar 1:1
  (⚠️ 畫師/產圖工具注意：匯出解析度限制 512x512, 背景需為黑色或透明的 .png/.webp)
  ```

### 5.2 權限階級 B (Rank B: Node Runner)
* **目標檔案**：`recontextualization/assets/images/badge_rank_b.png`
* **主題**：進階操作員，白銀與鋼鐵材質，帶有微弱藍光的徽章。
* **Prompt & Settings**:
  ```text
  An advanced cyberpunk rank badge, sleek silver and brushed steel texture, glowing neon blue circuit patterns, dark background, 2d vector art style, game UI icon, highly detailed.
  --ar 1:1
  (⚠️ 畫師/產圖工具注意：匯出解析度限制 512x512, 背景需為黑色或透明的 .png/.webp)
  ```

### 5.3 權限階級 A (Rank A: Elite Netrunner)
* **目標檔案**：`recontextualization/assets/images/badge_rank_a.png`
* **主題**：菁英駭客，閃耀黃金與琥珀色光芒的複雜晶片徽章。
* **Prompt & Settings**:
  ```text
  An elite cyberpunk rank badge, gleaming gold and amber texture, complex intricate glowing microchip circuit patterns, dark background, 2d vector art style, game UI icon, premium quality, highly detailed.
  --ar 1:1
  (⚠️ 畫師/產圖工具注意：匯出解析度限制 512x512, 背景需為黑色或透明的 .png/.webp)
  ```

### 5.4 權限階級 S (Rank S: Archon Admin)
* **目標檔案**：`recontextualization/assets/images/badge_rank_s.png`
* **主題**：最高管理員，懸浮的量子核心，散發霓虹白金與紫色的極致光芒。
* **Prompt & Settings**:
  ```text
  The ultimate cyberpunk rank badge, floating glowing quantum core, neon platinum and purple energy, holographic geometry, dark background, 2d vector art style, game UI icon, masterpiece, highly detailed.
  --ar 1:1
  (⚠️ 畫師/產圖工具注意：匯出解析度限制 512x512, 背景需為黑色或透明的 .png/.webp)
  ```

