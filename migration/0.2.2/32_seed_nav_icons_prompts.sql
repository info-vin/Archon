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
