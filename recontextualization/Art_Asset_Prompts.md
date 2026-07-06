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
* **需求數量**：總共 5 款獨特的卡牌美術（2 款資料晶片 + 3 款行動卡）。
* **格式建議**：若只產出圖示 (Icon) 供 UI 框架套用，請維持正方形比例並加上無文字的負向提示詞。若希望產出整張完整實體卡牌，請改用 `--ar 11:16`。

### 🏆 【進階】通用實體卡牌框 (Shared Blank Card Frame Template)
* **目標檔案**：`recontextualization/assets/images/card_frame_blank.png`
* **說明**：如果您希望自己在修圖軟體中，將上述的「純圖示」合成到一張完整的卡牌上，您只需要用這個提示詞產出**幾張共用的空白卡牌底框**即可。後續只要更換顏色與微調特效，就能套用在所有卡牌上！
* **Prompt & Settings**:
  ```text
  A blank collectible Trading Card frame template, futuristic sci-fi border layout, cyberpunk UI elements, empty glowing central container for artwork, large empty dark text box area at the bottom for card description, highly detailed 2d vector art style, clean dark background.
  --no text, typography, letters, words, icons, characters
  --ar 11:16
  (⚠️ 產出後，請將中央挖空，並確保卡牌「下方」有足夠乾淨的空間(約1/3)或文字框，用來放置卡牌的說明文字)
  ```

### 2.1 黃金資料晶片 (Data Core / Target Chunk)
* **目標檔案**：`recontextualization/assets/images/chip_green_target.png`
* **主題**：極具價值的無污染資料核心。
* **【唯一產圖選項：純圖示 (配合共用卡牌框)】**
  ```text
  A glowing emerald green cyberpunk microchip, intricate golden circuit patterns, floating in dark void, high contrast, macro photography, 3d render, glowing edges, straight front view, centered, symmetrical, slight 3D depth, highly detailed sci-fi tech artifact.
  --no text, typography, letters, words
  --ar 1:1
  ```

### 2.2 毒性雜訊晶片 (Noise / Corrupted Chunk)
* **目標檔案**：`recontextualization/assets/images/chip_red_noise.png`
* **主題**：遭到病毒感染、破圖與閃爍的危險資料。
* **【唯一產圖選項：純圖示 (配合共用卡牌框)】**
  ```text
  A corrupted cyberpunk microchip, glowing sinister crimson red, fractured and shattered edges, digital glitch effects, dark void background, high contrast, macro photography, dangerous aura, straight front view, centered, symmetrical, slight 3D depth, highly detailed sci-fi tech artifact.
  --no text, typography, letters, words
  --ar 1:1
  ```

---

## 3. 行動卡圖示 (Action Cards)

### 3.1 Keyword Search (L1)
* **目標檔案**：`recontextualization/assets/images/action_keyword.png`
* **主題**：精準的狙擊鎖定。
* **【唯一產圖選項：純圖示 (配合共用卡牌框)】**
  ```text
  A minimalist futuristic sniper crosshair symbol, glowing neon cyan, geometric shapes, cyberpunk UI element, dark background, sharp lines, straight front view, centered, symmetrical, slight 3D depth, highly detailed 2d vector art style.
  --no text, typography, letters, words
  --ar 1:1
  ```

### 3.2 Dense Vector (L2)
* **目標檔案**：`recontextualization/assets/images/action_dense.png`
* **主題**：深層穿透的雷射光束。
* **【唯一產圖選項：純圖示 (配合共用卡牌框)】**
  ```text
  A futuristic glowing laser beam piercing through digital layers, neon purple and blue, geometric cyberpunk UI element, dark background, sharp lines, dynamic composition, straight front view, centered, symmetrical, slight 3D depth, highly detailed 2d vector art style.
  --no text, typography, letters, words
  --ar 1:1
  ```

### 3.3 Reranker (L3)
* **目標檔案**：`recontextualization/assets/images/action_reranker.png`
* **主題**：完美的六角形量子護盾/重組器。
* **【唯一產圖選項：純圖示 (配合共用卡牌框)】**
  ```text
  A glowing neon gold hexagonal energy shield, complex geometric fractal patterns inside, cyberpunk UI element, dark background, sharp lines, straight front view, centered, symmetrical, slight 3D depth, highly detailed 2d vector art style.
  --no text, typography, letters, words
  --ar 1:1
  ```

### 3.4 GraphRAG Navigation (L5)
* **目標檔案**：`recontextualization/assets/images/action_graphrag.png`
* **主題**：知識圖譜連鎖，展示數據節點多跳關聯的纖維星座結構。
* **【唯一產圖選項：純圖示 (配合共用卡牌框)】**
  ```text
  A glowing neon data node constellation structure showing multi-hop connections, complex glowing fiber optic network, cyberpunk UI element, dark background, sharp lines, straight front view, centered, symmetrical, slight 3D depth, highly detailed 2d vector art style.
  --no text, typography, letters, words
  --ar 1:1
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




## 6. 使用者介面元素 (UI Elements)

為了配合 Phase 5.8.7 的「角色管理 UI (Character Dashboard)」以及 RBAC 系統中「依權限變色的使用者頭像」功能，我們需要一個高質感的預設頭像。

### 6.1 預設駭客頭像 (Default Hacker Avatar)
* **目標檔案**：`recontextualization/assets/images/avatar_default.png`
* **主題**：一個神秘的賽博龐克駭客輪廓或高科技面罩，採用灰階或單色系（Grayscale），以便在 Godot 中透過程式碼 (Modulate) 依權限動態上色。
* **Prompt & Settings**:
  ```text
  A mysterious cyberpunk hacker silhouette wearing a high-tech glowing visor, hooded figure, glowing neon accents, dark background, pure grayscale color palette, monochromatic, game UI portrait, 2d vector art style, highly detailed.
  --ar 1:1
  (⚠️ 畫師/產圖工具注意：必須是灰階/黑白圖像，解析度限制 512x512，背景建議為純黑或透明)
  ```

## 7. 代理團隊與裝備 (Agent Teammates & Equipment)

為了配合 Phase 5.8.9 的「AI 代理終端面板」與「雙腦架構」，我們需要為不同的 Agent 隊友生成具備專屬性格的頭像，以及在裝備欄中顯示的空插槽圖示。

### 7.1 社交者助理 - Alice (Socializer Agent)
* **目標檔案**：`recontextualization/assets/images/avatar_alice.png`
* **主題**：親切、活潑且善於溝通的賽博龐克接線生或社群經理風格。以「粉紅與亮青色 (Pink & Cyan)」為主要視覺特徵，輪廓圓潤具親和力。
* **Prompt & Settings**:
  ```text
  A cyberpunk female hacker avatar named Alice, friendly and charismatic expression, wearing sleek futuristic headset with glowing pink and cyan neon lights, stylish casual cyberpunk street wear, neon-lit cityscape in the background, anime-influenced highly detailed portrait, 2d vector art style, game UI portrait, distinct pink and cyan color theme, recognizable silhouette.
  --no text, typography, letters, words, dark gloomy colors
  --ar 1:1
  (⚠️ 畫師/產圖工具注意：解析度限制 256x256)
  ```

### 7.2 推論者助理 - Bob (Deductor Agent)
* **目標檔案**：`recontextualization/assets/images/avatar_bob.png`
* **主題**：冷靜、嚴謹、像偵探或分析師的 ReAct 推理大師。以「琥珀與黃金色 (Amber & Gold)」為主要視覺特徵，輪廓俐落且穿著正裝。
* **Prompt & Settings**:
  ```text
  A cyberpunk male detective hacker avatar named Bob, serious and analytical expression, wearing a high-tech augmented reality monocle glowing with amber data streams, tailored futuristic dark suit, dimly lit server room background, film noir cyberpunk aesthetic, highly detailed portrait, 2d vector art style, game UI portrait, distinct amber and gold color theme, sharp tailored silhouette.
  --no text, typography, letters, words, bright cheerful colors
  --ar 1:1
  (⚠️ 畫師/產圖工具注意：解析度限制 256x256)
  ```

### 7.3 檢索者助理 - Charlie (Retriever Agent)
* **目標檔案**：`recontextualization/assets/images/avatar_charlie.png`
* **主題**：專注於深度潛入資料庫的礦工或導航員。以「工業綠與鐵灰色 (Industrial Green & Iron Grey)」為主要視覺特徵，輪廓厚重且帶有重裝備。
* **Prompt & Settings**:
  ```text
  A heavy-duty cyberpunk data miner avatar named Charlie, rugged and focused expression, wearing a bulky neural-dive helmet with multiple glowing green optical sensors, thick cables connecting to the suit, deep matrix grid background, industrial sci-fi aesthetic, highly detailed portrait, 2d vector art style, game UI portrait, distinct industrial green color theme, bulky heavy silhouette.
  --no text, typography, letters, words
  --ar 1:1
  (⚠️ 畫師/產圖工具注意：解析度限制 256x256)
  ```

### 7.4 裝備插槽圖示 (Equipment Slot Icon)
* **目標檔案**：`recontextualization/assets/images/icon_equipment_slot.png`
* **主題**：等待插入大語言模型 (LLM) 晶片的空裝備槽位。
* **Prompt & Settings**:
  ```text
  An empty futuristic equipment slot icon for a microchip, glowing UI outline, minimalist cyberpunk design, dark empty placeholder in the center, faint blue holographic grid pattern, 2d vector art style, sharp lines, clean dark background.
  --ar 1:1
  --no text, letters, typography
  (⚠️ 畫師/產圖工具注意：解析度限制 256x256)
  ```

---

## 8. 自動化美術處理腳本 (Automated Asset Processing)

在生成 AI 美術資源後，原始檔案（通常大於 5MB）必須經過安全降轉與裁切，才能匯入 Godot 專案。我們統一使用 Python 腳本 `optimize_assets.py` 進行處理。

### 8.1 執行降轉腳本 (Image Optimizer)
* **腳本位置**：`recontextualization/optimize_assets.py`
* **功能**：自動進行完美的中心正方裁切 (Center Crop)，並使用 Lanczos 高品質無損演算法降採樣至各類別規定的解析度。
* **執行規範 (強制使用 uv 環境)**：
  為避免系統 Python 版本 (3.7 vs 3.12) 混亂，請一律透過後端的 `uv` 環境執行此腳本。
  ```bash
  # 進入後端目錄以使用 uv 環境 (內建 Python 3.12)
  cd ../python
  # 確保安裝 Pillow 影像處理庫
  uv pip install Pillow
  # 執行前端的美術優化腳本
  uv run python ../recontextualization/optimize_assets.py
  ```
* **注意**：絕不可使用粗糙的自動去背演算法。所有頭像與 UI 底框皆應保留原始背景，透過 Godot UI 系統的 `MarginContainer` 或 Shader 進行遮罩 (Masking)，以避免鋸齒毛邊。
