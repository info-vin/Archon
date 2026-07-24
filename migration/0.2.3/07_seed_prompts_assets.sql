-- Source: 31_seed_art_asset_prompts.sql
-- Phase 5.9.7: Seed Art Asset Prompts from Art_Asset_Prompts.md
INSERT INTO public.archon_prompts (prompt_name, category, description, prompt, metadata)
VALUES
('ART_ASSET_BG_VECTOR_GRID', 'ART_ASSET', '1.1 戰鬥場景背景 (GameBoard Background)', '  POV flying into the matrix, an infinite 3D wireframe cyberspace grid tunnel, extreme deep perspective with a distant vanishing point, glowing neon digital rain cascading down invisible walls, retro-futuristic hacker aesthetic, intense faux-3D virtual reality depth of field, high contrast black background with vibrant glowing lines, cinematic motion blur, crisp game asset, sci-fi concept art.
  --ar 16:9 --no text, watermark, characters, people, UI elements, bright light.
  (⚠️ 畫師/產圖工具注意：匯出解析度限制 1920x1080, 儲存為 .webp 或壓縮 .png)', '{"group": "1. 環境背景 (Environments)", "subgroup": "1.1 戰鬥場景背景 (GameBoard Background)", "target_file": "recontextualization/assets/images/bg_vector_grid.png", "theme": "深邃的量子資料庫內部，呈現《駭客任務》般強烈的假 3D 視覺縱深與無限網格。"}'::jsonb),
('ART_ASSET_BG_SYNTHESIZER', 'ART_ASSET', '1.2 合成工坊背景 (Workshop Background)', '  A high-tech quantum synthesizer furnace in a dark cyberpunk laboratory, intense glowing orange and amber core, electrical sparks, heavy industrial machinery, holographic blueprints floating in the air, cinematic lighting, dramatic shadows, highly detailed concept art.
  --ar 16:9 --no text, people, bright room, clean sterile environment.
  (⚠️ 畫師/產圖工具注意：匯出解析度限制 1920x1080, 儲存為 .webp 或壓縮 .png)', '{"group": "1. 環境背景 (Environments)", "subgroup": "1.2 合成工坊背景 (Workshop Background)", "target_file": "recontextualization/assets/images/bg_synthesizer.png", "theme": "高溫、充滿電火花與機械臂的卡牌量子融合爐。"}'::jsonb),
('ART_ASSET_CARD_FRAME_BLANK', 'ART_ASSET', '🏆 【進階】通用實體卡牌框 (Shared Blank Card Frame Template)', '  A blank collectible Trading Card frame template, futuristic sci-fi border layout, cyberpunk UI elements, empty glowing central container for artwork, large empty dark text box area at the bottom for card description, highly detailed 2d vector art style, clean dark background.
  --no text, typography, letters, words, icons, characters
  --ar 11:16
  (⚠️ 產出後，請將中央挖空，並確保卡牌「下方」有足夠乾淨的空間(約1/3)或文字框，用來放置卡牌的說明文字)', '{"group": "2. 實體卡牌圖示 (Card Icons)", "subgroup": "🏆 【進階】通用實體卡牌框 (Shared Blank Card Frame Template)", "target_file": "recontextualization/assets/images/card_frame_blank.png", "theme": ""}'::jsonb),
('ART_ASSET_CHIP_GREEN_TARGET', 'ART_ASSET', '2.1 黃金資料晶片 (Data Core / Target Chunk)', '  A glowing emerald green cyberpunk microchip, intricate golden circuit patterns, floating in dark void, high contrast, macro photography, 3d render, glowing edges, straight front view, centered, symmetrical, slight 3D depth, highly detailed sci-fi tech artifact.
  --no text, typography, letters, words
  --ar 1:1', '{"group": "2. 實體卡牌圖示 (Card Icons)", "subgroup": "2.1 黃金資料晶片 (Data Core / Target Chunk)", "target_file": "recontextualization/assets/images/chip_green_target.png", "theme": "極具價值的無污染資料核心。"}'::jsonb),
('ART_ASSET_CHIP_RED_NOISE', 'ART_ASSET', '2.2 毒性雜訊晶片 (Noise / Corrupted Chunk)', '  A corrupted cyberpunk microchip, glowing sinister crimson red, fractured and shattered edges, digital glitch effects, dark void background, high contrast, macro photography, dangerous aura, straight front view, centered, symmetrical, slight 3D depth, highly detailed sci-fi tech artifact.
  --no text, typography, letters, words
  --ar 1:1', '{"group": "2. 實體卡牌圖示 (Card Icons)", "subgroup": "2.2 毒性雜訊晶片 (Noise / Corrupted Chunk)", "target_file": "recontextualization/assets/images/chip_red_noise.png", "theme": "遭到病毒感染、破圖與閃爍的危險資料。"}'::jsonb),
('ART_ASSET_ACTION_KEYWORD', 'ART_ASSET', '3.1 Keyword Search (L1)', '  A minimalist futuristic sniper crosshair symbol, glowing neon cyan, geometric shapes, cyberpunk UI element, dark background, sharp lines, straight front view, centered, symmetrical, slight 3D depth, highly detailed 2d vector art style.
  --no text, typography, letters, words
  --ar 1:1
  (⚠️ 畫師/產圖工具注意：匯出解析度限制 512x512, 背景建議為純黑或透明的 .png/.webp)', '{"group": "3. 行動卡圖示 (Action Cards)", "subgroup": "3.1 Keyword Search (L1)", "target_file": "recontextualization/assets/images/action_keyword.png", "theme": "精準的狙擊鎖定。"}'::jsonb),
('ART_ASSET_ACTION_DENSE', 'ART_ASSET', '3.2 Dense Vector (L2)', '  A futuristic hyper-kinetic sniper bullet in slow motion piercing digital armor, shattering glass effects, metallic dark silver and glowing cyan energy, extremely high detail, cinematic lighting, dark background, dynamic composition, straight front view, centered, symmetrical, slight 3D depth, highly detailed 2d vector art style.
  --no text, typography, letters, words
  --ar 1:1', '{"group": "3. 行動卡圖示 (Action Cards)", "subgroup": "3.2 Dense Vector (L2)", "target_file": "recontextualization/assets/images/action_dense.png", "theme": "一擊必殺、威力驚人的實體子彈或動能武器。"}'::jsonb),
('ART_ASSET_GEM_NEW_CAREER', 'ART_ASSET', '8.1 新遊戲 (New Career)', '  A hyper-realistic glowing emerald green and cyan genesis data core gem, floating in a pure black void. Extreme photorealism, physically based rendering, real light refraction, internal glowing matrix structure, subsurface scattering, frameless, no borders, isolated on black background, 8k resolution, cinematic real lighting, macro photography.
  --no text, letters, UI, borders, frames, human, background elements
  --ar 1:1', '{"group": "8. 主選單寶石圖示 (Main Menu Gems)", "subgroup": "8.1 新遊戲 (New Career)", "target_file": "recontextualization/assets/images/gem_new_career.png", "theme": "創世資料核心 (Genesis Data Core)"}'::jsonb),
('ART_ASSET_GEM_CONTINUE', 'ART_ASSET', '8.2 繼續遊戲 (Continue)', '  A hyper-realistic golden amber gem shaped like an hourglass or temporal matrix, floating in a pure black void. Extreme photorealism, physically based rendering, real light refraction, internal glowing golden sand-like energy, subsurface scattering, frameless, no borders, isolated on black background, 8k resolution, cinematic real lighting, macro photography.
  --no text, letters, UI, borders, frames, human, background elements
  --ar 1:1', '{"group": "8. 主選單寶石圖示 (Main Menu Gems)", "subgroup": "8.2 繼續遊戲 (Continue)", "target_file": "recontextualization/assets/images/gem_continue.png", "theme": "時空記憶矩陣 (Temporal Memory Matrix)"}'::jsonb),
('ART_ASSET_GEM_TEAMMATE', 'ART_ASSET', '8.3 夥伴儀表板 (Teammate Dashboard)', '  A hyper-realistic sapphire blue prism gem with interconnected glowing neural nodes inside, floating in a pure black void. Extreme photorealism, physically based rendering, real light refraction, internal pulsing blue energy network, subsurface scattering, frameless, no borders, isolated on black background, 8k resolution, cinematic real lighting, macro photography.
  --no text, letters, UI, borders, frames, human, background elements
  --ar 1:1', '{"group": "8. 主選單寶石圖示 (Main Menu Gems)", "subgroup": "8.3 夥伴儀表板 (Teammate Dashboard)", "target_file": "recontextualization/assets/images/gem_teammate.png", "theme": "群體智慧稜鏡 (Hive-mind Prism)"}'::jsonb),
('ART_ASSET_GEM_CARD_MANAGEMENT', 'ART_ASSET', '8.4 卡牌管理 (Card Management)', '  A hyper-realistic sharp geometric obsidian diamond gem, emitting sleek purple and silver neon light, floating in a pure black void. Extreme photorealism, physically based rendering, real light refraction, sharp flawless facets, frameless, no borders, isolated on black background, 8k resolution, cinematic real lighting, macro photography.
  --no text, letters, UI, borders, frames, human, background elements
  --ar 1:1', '{"group": "8. 主選單寶石圖示 (Main Menu Gems)", "subgroup": "8.4 卡牌管理 (Card Management)", "target_file": "recontextualization/assets/images/gem_card_management.png", "theme": "架構師黑曜石 (Architect Obsidian)"}'::jsonb),
('ART_ASSET_GEM_QUIT', 'ART_ASSET', '8.5 離開遊戲 (Quit Game)', '  A hyper-realistic fractured dark ruby red crystal gem, glowing with a dangerous intense crimson heat, floating in a pure black void. Extreme photorealism, physically based rendering, real light refraction, cracking and slowly shattering, frameless, no borders, isolated on black background, 8k resolution, cinematic real lighting, macro photography.
  --no text, letters, UI, borders, frames, human, background elements
  --ar 1:1', '{"group": "8. 主選單寶石圖示 (Main Menu Gems)", "subgroup": "8.5 離開遊戲 (Quit Game)", "target_file": "recontextualization/assets/images/gem_quit.png", "theme": "終止執行晶體 (Termination Crystal)"}'::jsonb),
('ART_ASSET_ACTION_RERANKER', 'ART_ASSET', '3.3 Reranker (L3)', '  A glowing neon gold hexagonal energy shield, complex geometric fractal patterns inside, cyberpunk UI element, dark background, sharp lines, straight front view, centered, symmetrical, slight 3D depth, highly detailed 2d vector art style.
  --no text, typography, letters, words
  --ar 1:1
  (⚠️ 畫師/產圖工具注意：匯出解析度限制 512x512, 背景建議為純黑或透明的 .png/.webp)', '{"group": "3. 行動卡圖示 (Action Cards)", "subgroup": "3.3 Reranker (L3)", "target_file": "recontextualization/assets/images/action_reranker.png", "theme": "完美的六角形量子護盾/重組器。"}'::jsonb),
('ART_ASSET_ACTION_GRAPHRAG', 'ART_ASSET', '3.4 GraphRAG Navigation (L5)', '  A glowing neon data node constellation structure showing multi-hop connections, complex glowing fiber optic network, cyberpunk UI element, dark background, sharp lines, straight front view, centered, symmetrical, slight 3D depth, highly detailed 2d vector art style.
  --no text, typography, letters, words
  --ar 1:1
  (⚠️ 畫師/產圖工具注意：匯出解析度限制 512x512, 背景建議為純黑或透明的 .png/.webp)', '{"group": "3. 行動卡圖示 (Action Cards)", "subgroup": "3.4 GraphRAG Navigation (L5)", "target_file": "recontextualization/assets/images/action_graphrag.png", "theme": "知識圖譜連鎖，展示數據節點多跳關聯的纖維星座結構。"}'::jsonb),
('ART_ASSET_ACTION_NEUROTOXIN', 'ART_ASSET', '3.5 Neurotoxin (L4)', '  A glowing neon toxic biohazard symbol dissolving into dripping corrupted digital code, green and purple acid theme, cyberpunk UI element, dark background, sharp lines, straight front view, centered, symmetrical, slight 3D depth, highly detailed 2d vector art style.
  --no text, typography, letters, words
  --ar 1:1
  (⚠️ 畫師/產圖工具注意：匯出解析度限制 512x512, 背景建議為純黑或透明的 .png/.webp)', '{"group": "3. 行動卡圖示 (Action Cards)", "subgroup": "3.5 Neurotoxin (L4)", "target_file": "recontextualization/assets/images/action_neurotoxin.png", "theme": "滴落的綠色或紫色劇毒液體、溶解的代碼。"}'::jsonb),
('ART_ASSET_ACTION_XRAY', 'ART_ASSET', '3.6 X-Ray Scan (L1)', '  A futuristic glowing cybernetic eye scanning through digital layers, radar waves emitting, neon cyan and white, geometric cyberpunk UI element, dark background, sharp lines, straight front view, centered, symmetrical, slight 3D depth, highly detailed 2d vector art style.
  --no text, typography, letters, words
  --ar 1:1
  (⚠️ 畫師/產圖工具注意：匯出解析度限制 512x512, 背景建議為純黑或透明的 .png/.webp)', '{"group": "3. 行動卡圖示 (Action Cards)", "subgroup": "3.6 X-Ray Scan (L1)", "target_file": "recontextualization/assets/images/action_xray.png", "theme": "透視掃描的雷達波或發光眼睛。"}'::jsonb),
('ART_ASSET_ACTION_OVERCLOCK', 'ART_ASSET', '3.7 Core Overclock (L4)', '  A glowing fiery core overheating with intense electrical lightning arcs around a digital clock dial, neon orange and yellow, overclocked CPU concept, cyberpunk UI element, dark background, sharp lines, straight front view, centered, symmetrical, slight 3D depth, highly detailed 2d vector art style.
  --no text, typography, letters, words
  --ar 1:1
  (⚠️ 畫師/產圖工具注意：匯出解析度限制 512x512, 背景建議為純黑或透明的 .png/.webp)', '{"group": "3. 行動卡圖示 (Action Cards)", "subgroup": "3.7 Core Overclock (L4)", "target_file": "recontextualization/assets/images/action_overclock.png", "theme": "高溫燃燒的時鐘、或閃電纏繞的超頻晶片。"}'::jsonb),
('ART_ASSET_ACTION_TROJAN', 'ART_ASSET', '3.8 Stealth Trojan (L2)', '  A glowing neon stealth phantom mask or digital trojan horse partially cloaked in pixelated optical camouflage, dark violet and magenta, cyberpunk UI element, dark background, sharp lines, straight front view, centered, symmetrical, slight 3D depth, highly detailed 2d vector art style.
  --no text, typography, letters, words
  --ar 1:1
  (⚠️ 畫師/產圖工具注意：匯出解析度限制 512x512, 背景建議為純黑或透明的 .png/.webp)', '{"group": "3. 行動卡圖示 (Action Cards)", "subgroup": "3.8 Stealth Trojan (L2)", "target_file": "recontextualization/assets/images/action_trojan.png", "theme": "披著光學迷彩的木馬或幽靈面具。"}'::jsonb),
('ART_ASSET_ACTION_EMP', 'ART_ASSET', '3.9 EMP Blast (L5)', '  An explosive neon blue electromagnetic pulse shockwave radiating outwards, intense energy blast, geometric cyberpunk UI element, dark background, sharp lines, straight front view, centered, symmetrical, slight 3D depth, highly detailed 2d vector art style.
  --no text, typography, letters, words
  --ar 1:1
  (⚠️ 畫師/產圖工具注意：匯出解析度限制 512x512, 背景建議為純黑或透明的 .png/.webp)', '{"group": "3. 行動卡圖示 (Action Cards)", "subgroup": "3.9 EMP Blast (L5)", "target_file": "recontextualization/assets/images/action_emp.png", "theme": "向外擴散的強烈電磁衝擊波。"}'::jsonb),
('ART_ASSET_ACTION_LEECH', 'ART_ASSET', '3.10 Data Leech (L1)', '  A glowing neon green robotic leech or cybernetic tentacle siphoning digital data streams, parasitic cyber-ware, cyberpunk UI element, dark background, sharp lines, straight front view, centered, symmetrical, slight 3D depth, highly detailed 2d vector art style.
  --no text, typography, letters, words
  --ar 1:1
  (⚠️ 畫師/產圖工具注意：匯出解析度限制 512x512, 背景建議為純黑或透明的 .png/.webp)', '{"group": "3. 行動卡圖示 (Action Cards)", "subgroup": "3.10 Data Leech (L1)", "target_file": "recontextualization/assets/images/action_leech.png", "theme": "虹吸能量的機械水蛭或資料觸手。"}'::jsonb),
('ART_ASSET_TRANSITION_OS_BOOT', 'ART_ASSET', '4.1 遊戲啟動/主選單開場 (Archon OS Bootup)', '  A fast-paced retro-futuristic hacker operating system boot screen, monolithic cyberpunk terminal, glowing monochrome green phosphor text rapidly scrolling, geometric logos quickly flashing on a deep black background, short visual blast, extremely detailed UI design, crisp game asset, cinematic lighting, highly detailed tech art.
  --ar 16:9
  (⚠️ 注意：請生成動態完整的影片後再自行裁切至 3~6 秒，儲存為 .mp4 供 Agent 轉檔)', '{"group": "4. 轉場動畫 (Video Transitions)", "subgroup": "4.1 遊戲啟動/主選單開場 (Archon OS Bootup)", "target_file": "recontextualization/assets/vfx/transition_os_boot.mp4", "theme": ""}'::jsonb),
('ART_ASSET_TRANSITION_BATTLE_INTRO', 'ART_ASSET', '4.2 戰鬥開場 (Uplink Established)', '  POV flying forward rapidly into a futuristic cyberpunk hacking interface initializing, quick transition, a massive glowing neon blue gateway quickly bursting open in cyberspace, data streams rushing forward in high speed perspective, intense motion blur effect, fast-paced action, crisp game asset, cinematic lighting, highly detailed tech art.
  --ar 16:9
  (⚠️ 注意：請生成動態完整的影片後再自行裁切至 3 秒，儲存為 .mp4 供 Agent 轉檔)', '{"group": "4. 轉場動畫 (Video Transitions)", "subgroup": "4.2 戰鬥開場 (Uplink Established)", "target_file": "recontextualization/assets/vfx/transition_battle_intro.mp4", "theme": ""}'::jsonb),
('ART_ASSET_TRANSITION_VICTORY', 'ART_ASSET', '4.3 戰鬥勝利 (Data Extracted)', '  Fast-paced triumphant cyberpunk victory screen background, glowing emerald green geometric patterns rapidly expanding, quick transition, bright neon light burst, floating holographic data cubes being quickly secured, dark cyberspace background, highly detailed tech art.
  --ar 16:9
  (⚠️ 注意：請生成動態完整的影片後再自行裁切至 5 秒，儲存為 .mp4 供 Agent 轉檔)', '{"group": "4. 轉場動畫 (Video Transitions)", "subgroup": "4.3 戰鬥勝利 (Data Extracted)", "target_file": "recontextualization/assets/vfx/transition_victory.mp4", "theme": ""}'::jsonb),
('ART_ASSET_TRANSITION_DEFEAT_GLITCH', 'ART_ASSET', '4.4 戰鬥失敗 - 破圖警告 (System Compromised)', '  Severe rapid digital glitch art, screen tearing, short visual blast, intense glowing crimson red warning signals violently flashing, quick transition, distorted typography and rapid pixel sorting effects, dark cyberspace environment, high contrast, terrifying fast-paced atmosphere.
  --ar 16:9
  (⚠️ 注意：請生成動態完整的影片後再自行裁切至 2 秒，儲存為 .mp4 供 Agent 轉檔)', '{"group": "4. 轉場動畫 (Video Transitions)", "subgroup": "4.4 戰鬥失敗 - 破圖警告 (System Compromised)", "target_file": "recontextualization/assets/vfx/transition_defeat_glitch.mp4", "theme": ""}'::jsonb),
('ART_ASSET_TRANSITION_DEFEAT_SHUTDOWN', 'ART_ASSET', '4.5 戰鬥失敗 - 斷電停機 (Connection Terminated)', '  A dead cyberpunk terminal screen rapidly powering down, rapid transformation, fast fading glowing red embers, quick transition to a cracked screen glass reflecting a dark empty void, deep shadows, cinematic lighting, melancholic cyber atmosphere.
  --ar 16:9
  (⚠️ 注意：請生成動態完整的影片後再自行裁切至 3 秒，儲存為 .mp4 供 Agent 轉檔)', '{"group": "4. 轉場動畫 (Video Transitions)", "subgroup": "4.5 戰鬥失敗 - 斷電停機 (Connection Terminated)", "target_file": "recontextualization/assets/vfx/transition_defeat_shutdown.mp4", "theme": ""}'::jsonb),
('ART_ASSET_BADGE_RANK_C', 'ART_ASSET', '5.1 權限階級 C (Rank C: Script Kiddie)', '  A minimalist cyberpunk rank badge, bronze and rusted copper texture, simple geometric circuit patterns, dimly lit, dark background, 2d vector art style, game UI icon, sharp edges.
  --ar 1:1
  (⚠️ 畫師/產圖工具注意：匯出解析度限制 512x512, 背景需為黑色或透明的 .png/.webp)', '{"group": "5. 玩家階級與徽章 (Player Ranks & Badges)", "subgroup": "5.1 權限階級 C (Rank C: Script Kiddie)", "target_file": "recontextualization/assets/images/badge_rank_c.png", "theme": "初階駭客，生鏽或青銅材質的基礎電路徽章。"}'::jsonb),
('ART_ASSET_BADGE_RANK_B', 'ART_ASSET', '5.2 權限階級 B (Rank B: Node Runner)', '  An advanced cyberpunk rank badge, sleek silver and brushed steel texture, glowing neon blue circuit patterns, dark background, 2d vector art style, game UI icon, highly detailed.
  --ar 1:1
  (⚠️ 畫師/產圖工具注意：匯出解析度限制 512x512, 背景需為黑色或透明的 .png/.webp)', '{"group": "5. 玩家階級與徽章 (Player Ranks & Badges)", "subgroup": "5.2 權限階級 B (Rank B: Node Runner)", "target_file": "recontextualization/assets/images/badge_rank_b.png", "theme": "進階操作員，白銀與鋼鐵材質，帶有微弱藍光的徽章。"}'::jsonb),
('ART_ASSET_BADGE_RANK_A', 'ART_ASSET', '5.3 權限階級 A (Rank A: Elite Netrunner)', '  An elite cyberpunk rank badge, gleaming gold and amber texture, complex intricate glowing microchip circuit patterns, dark background, 2d vector art style, game UI icon, premium quality, highly detailed.
  --ar 1:1
  (⚠️ 畫師/產圖工具注意：匯出解析度限制 512x512, 背景需為黑色或透明的 .png/.webp)', '{"group": "5. 玩家階級與徽章 (Player Ranks & Badges)", "subgroup": "5.3 權限階級 A (Rank A: Elite Netrunner)", "target_file": "recontextualization/assets/images/badge_rank_a.png", "theme": "菁英駭客，閃耀黃金與琥珀色光芒的複雜晶片徽章。"}'::jsonb),
('ART_ASSET_BADGE_RANK_S', 'ART_ASSET', '5.4 權限階級 S (Rank S: Archon Admin)', '  The ultimate cyberpunk rank badge, floating glowing quantum core, neon platinum and purple energy, holographic geometry, dark background, 2d vector art style, game UI icon, masterpiece, highly detailed.
  --ar 1:1
  (⚠️ 畫師/產圖工具注意：匯出解析度限制 512x512, 背景需為黑色或透明的 .png/.webp)', '{"group": "5. 玩家階級與徽章 (Player Ranks & Badges)", "subgroup": "5.4 權限階級 S (Rank S: Archon Admin)", "target_file": "recontextualization/assets/images/badge_rank_s.png", "theme": "最高管理員，懸浮的量子核心，散發霓虹白金與紫色的極致光芒。"}'::jsonb),
('ART_ASSET_AVATAR_DEFAULT', 'ART_ASSET', '6.1 預設駭客頭像 (Default Hacker Avatar)', '  A mysterious cyberpunk hacker silhouette wearing a high-tech glowing visor, hooded figure, glowing neon accents, dark background, pure grayscale color palette, monochromatic, game UI portrait, 2d vector art style, highly detailed.
  --ar 1:1
  (⚠️ 畫師/產圖工具注意：必須是灰階/黑白圖像，解析度限制 512x512，背景建議為純黑或透明)', '{"group": "6. 使用者介面元素 (UI Elements)", "subgroup": "6.1 預設駭客頭像 (Default Hacker Avatar)", "target_file": "recontextualization/assets/images/avatar_default.png", "theme": "一個神秘的賽博龐克駭客輪廓或高科技面罩，採用灰階或單色系（Grayscale），以便在 Godot 中透過程式碼 (Modulate) 依權限動態上色。"}'::jsonb),
('ART_ASSET_AVATAR_ALICE', 'ART_ASSET', '7.1 社交者助理 - Alice (Socializer Agent)', '  A cyberpunk female hacker avatar named Alice, friendly and charismatic expression, wearing sleek futuristic headset with glowing pink and cyan neon lights, stylish casual cyberpunk street wear, neon-lit cityscape in the background, anime-influenced highly detailed portrait, 2d vector art style, game UI portrait, distinct pink and cyan color theme, recognizable silhouette.
  --no text, typography, letters, words, dark gloomy colors
  --ar 1:1
  (⚠️ 畫師/產圖工具注意：解析度限制 256x256)', '{"group": "7. 代理團隊與裝備 (Agent Teammates & Equipment)", "subgroup": "7.1 社交者助理 - Alice (Socializer Agent)", "target_file": "recontextualization/assets/images/avatar_alice.png", "theme": "親切、活潑且善於溝通的賽博龐克接線生或社群經理風格。以「粉紅與亮青色 (Pink & Cyan)」為主要視覺特徵，輪廓圓潤具親和力。"}'::jsonb),
('ART_ASSET_AVATAR_BOB', 'ART_ASSET', '7.2 推論者助理 - Bob (Deductor Agent)', '  A cyberpunk male detective hacker avatar named Bob, serious and analytical expression, wearing a high-tech augmented reality monocle glowing with amber data streams, tailored futuristic dark suit, dimly lit server room background, film noir cyberpunk aesthetic, highly detailed portrait, 2d vector art style, game UI portrait, distinct amber and gold color theme, sharp tailored silhouette.
  --no text, typography, letters, words, bright cheerful colors
  --ar 1:1
  (⚠️ 畫師/產圖工具注意：解析度限制 256x256)', '{"group": "7. 代理團隊與裝備 (Agent Teammates & Equipment)", "subgroup": "7.2 推論者助理 - Bob (Deductor Agent)", "target_file": "recontextualization/assets/images/avatar_bob.png", "theme": "冷靜、嚴謹、像偵探或分析師的 ReAct 推理大師。以「琥珀與黃金色 (Amber & Gold)」為主要視覺特徵，輪廓俐落且穿著正裝。"}'::jsonb),
('ART_ASSET_AVATAR_CHARLIE', 'ART_ASSET', '7.3 檢索者助理 - Charlie (Retriever Agent)', '  A heavy-duty cyberpunk data miner avatar named Charlie, rugged and focused expression, wearing a bulky neural-dive helmet with multiple glowing green optical sensors, thick cables connecting to the suit, deep matrix grid background, industrial sci-fi aesthetic, highly detailed portrait, 2d vector art style, game UI portrait, distinct industrial green color theme, bulky heavy silhouette.
  --no text, typography, letters, words
  --ar 1:1
  (⚠️ 畫師/產圖工具注意：解析度限制 256x256)', '{"group": "7. 代理團隊與裝備 (Agent Teammates & Equipment)", "subgroup": "7.3 檢索者助理 - Charlie (Retriever Agent)", "target_file": "recontextualization/assets/images/avatar_charlie.png", "theme": "專注於深度潛入資料庫的礦工或導航員。以「工業綠與鐵灰色 (Industrial Green & Iron Grey)」為主要視覺特徵，輪廓厚重且帶有重裝備。"}'::jsonb),
('ART_ASSET_ICON_EQUIPMENT_SLOT', 'ART_ASSET', '7.4 裝備插槽圖示 (Equipment Slot Icon)', '  An empty futuristic equipment slot icon for a microchip, glowing UI outline, minimalist cyberpunk design, dark empty placeholder in the center, faint blue holographic grid pattern, 2d vector art style, sharp lines, clean dark background.
  --ar 1:1
  --no text, letters, typography
  (⚠️ 畫師/產圖工具注意：解析度限制 256x256)', '{"group": "7. 代理團隊與裝備 (Agent Teammates & Equipment)", "subgroup": "7.4 裝備插槽圖示 (Equipment Slot Icon)", "target_file": "recontextualization/assets/images/icon_equipment_slot.png", "theme": "等待插入大語言模型 (LLM) 晶片的空裝備槽位。"}'::jsonb)

ON CONFLICT (prompt_name) DO UPDATE SET
    category = EXCLUDED.category,
    description = EXCLUDED.description,
    prompt = EXCLUDED.prompt,
    metadata = EXCLUDED.metadata,
    is_system_protected = true;


-- Source: 32_seed_nav_icons_prompts.sql
-- Phase 5.9.8: Seed Left Navigation Icon Prompts
INSERT INTO public.archon_prompts (prompt_name, category, description, prompt, metadata)
VALUES
('ART_ASSET_ICON_NAV_CHARACTER', 'ART_ASSET', '9.1 角色導航圖示 (Nav Icon: Character)', '  A minimalist futuristic holographic ID badge or user profile silhouette, glowing neon cyan and white, geometric shapes, cyberpunk UI element, dark background, sharp lines, straight front view, centered, symmetrical, slight 3D depth, highly detailed 2d vector art style, game UI icon.
  --no text, typography, letters, words
  --ar 1:1
  (⚠️ 畫師/產圖工具注意：匯出解析度限制 512x512, 背景建議為純黑或透明的 .png/.webp)', '{"group": "9. 左側垂直導航圖示 (Left Nav Icons)", "subgroup": "9.1 角色導航圖示 (Nav Icon: Character)", "target_file": "recontextualization/assets/images/icon_nav_character.png", "theme": "代表玩家身分與屬性的全息識別牌或頭像。"}'::jsonb),

('ART_ASSET_ICON_NAV_CARD', 'ART_ASSET', '9.2 卡牌導航圖示 (Nav Icon: Card Management)', '  A stack of futuristic glowing digital data cards fanning out, neon purple and silver, cyberpunk UI element, dark background, sharp lines, straight front view, centered, symmetrical, slight 3D depth, highly detailed 2d vector art style, game UI icon.
  --no text, typography, letters, words
  --ar 1:1
  (⚠️ 畫師/產圖工具注意：匯出解析度限制 512x512, 背景建議為純黑或透明的 .png/.webp)', '{"group": "9. 左側垂直導航圖示 (Left Nav Icons)", "subgroup": "9.2 卡牌導航圖示 (Nav Icon: Card Management)", "target_file": "recontextualization/assets/images/icon_nav_card.png", "theme": "代表牌組管理的數位資料卡堆。"}'::jsonb),

('ART_ASSET_ICON_NAV_WORKSHOP', 'ART_ASSET', '9.3 工坊導航圖示 (Nav Icon: Workshop)', '  A futuristic cybernetic wrench crossed with a glowing plasma soldering iron, neon orange and amber, cyberpunk UI element, dark background, sharp lines, straight front view, centered, symmetrical, slight 3D depth, highly detailed 2d vector art style, game UI icon.
  --no text, typography, letters, words
  --ar 1:1
  (⚠️ 畫師/產圖工具注意：匯出解析度限制 512x512, 背景建議為純黑或透明的 .png/.webp)', '{"group": "9. 左側垂直導航圖示 (Left Nav Icons)", "subgroup": "9.3 工坊導航圖示 (Nav Icon: Workshop)", "target_file": "recontextualization/assets/images/icon_nav_workshop.png", "theme": "代表卡牌合成與強化的賽博扳手與電焊槍。"}'::jsonb),

('ART_ASSET_ICON_NAV_TEAMMATE', 'ART_ASSET', '9.4 夥伴導航圖示 (Nav Icon: Teammate)', '  Two glowing neural nodes interconnected by bright fiber optic data streams, symbolizing network connections and teamwork, neon blue and green, cyberpunk UI element, dark background, sharp lines, straight front view, centered, symmetrical, slight 3D depth, highly detailed 2d vector art style, game UI icon.
  --no text, typography, letters, words
  --ar 1:1
  (⚠️ 畫師/產圖工具注意：匯出解析度限制 512x512, 背景建議為純黑或透明的 .png/.webp)', '{"group": "9. 左側垂直導航圖示 (Left Nav Icons)", "subgroup": "9.4 夥伴導航圖示 (Nav Icon: Teammate)", "target_file": "recontextualization/assets/images/icon_nav_teammate.png", "theme": "代表代理人團隊的神經節點與網路連線。"}'::jsonb)

ON CONFLICT (prompt_name) DO UPDATE SET
    category = EXCLUDED.category,
    description = EXCLUDED.description,
    prompt = EXCLUDED.prompt,
    metadata = EXCLUDED.metadata,
    is_system_protected = true;


