import re
import os

tscn_path = "archon-agency-tycoon/Scenes/Main/Main.tscn"
if not os.path.exists(tscn_path):
    print(f"Error: {tscn_path} not found.")
    exit(1)

with open(tscn_path, "r") as f:
    content = f.read()

# 1. RightPanel 防壓扁: 確保其 size_flags_horizontal = 8 (SHRINK_END)
content = re.sub(
    r'\[node name="RightPanel" type="PanelContainer" parent="VBox/HBoxMain"\]\nlayout_mode = 2',
    r'[node name="RightPanel" type="PanelContainer" parent="VBox/HBoxMain"]\nlayout_mode = 2\nsize_flags_horizontal = 8',
    content
)

# 2. 底端按鈕放大: 從 Vector2(60, 60) 放大至 Vector2(80, 80)
# 這個正則會找到 ActionHBox 下面的四個按鈕的 custom_minimum_size
content = re.sub(
    r'custom_minimum_size = Vector2\(60, 60\)',
    r'custom_minimum_size = Vector2(80, 80)',
    content
)

# 3. 跑馬燈呼吸空間: TopBar custom_minimum_size 從 (0, 30) 改為 (0, 40)
content = re.sub(
    r'\[node name="TopBar" type="PanelContainer" parent="VBox"\]\ncustom_minimum_size = Vector2\(0, 30\)',
    r'[node name="TopBar" type="PanelContainer" parent="VBox"]\ncustom_minimum_size = Vector2(0, 40)',
    content
)

# 5. 小地圖 Padding: 我們透過改變 MinimapContainer 的 anchors/offsets 來達到內縮效果，而非增加新節點以避免破壞腳本參照
# 尋找 MinimapContainer 下的 BG ColorRect 並增加 Margin (將 anchor 縮進)
# 這段正則將 BG 稍微往內縮 (left=8, top=8, right=-8, bottom=-8)
bg_rect_pattern = r'\[node name="BG" type="ColorRect" parent="VBox/HBoxMain/RightPanel/VBox/MinimapContainer"\]\nlayout_mode = 1\nanchors_preset = 15\nanchor_right = 1.0\nanchor_bottom = 1.0\ngrow_horizontal = 2\ngrow_vertical = 2'
bg_rect_replacement = """[node name="BG" type="ColorRect" parent="VBox/HBoxMain/RightPanel/VBox/MinimapContainer"]
layout_mode = 1
anchors_preset = 15
anchor_right = 1.0
anchor_bottom = 1.0
offset_left = 8.0
offset_top = 8.0
offset_right = -8.0
offset_bottom = -8.0
grow_horizontal = 2
grow_vertical = 2"""
content = content.replace(bg_rect_pattern, bg_rect_replacement)


with open(tscn_path, "w") as f:
    f.write(content)

print("Successfully applied UI and RWD layout optimizations to Main.tscn.")
