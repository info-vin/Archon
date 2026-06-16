import os

tscn_path = 'archon-agency-tycoon/Scenes/Main/Main.tscn'

with open(tscn_path, 'r') as f:
    tscn = f.read()

# Make sure icon_lang.svg is added
new_res = '[ext_resource type="Texture2D" path="res://Assets/Icons/icon_lang.svg" id="icon_lang"]\n'
if "icon_lang.svg" not in tscn:
    parts = tscn.split('\n[node name="Main" type="Control"]')
    tscn = parts[0] + "\n" + new_res + '\n[node name="Main" type="Control"]' + parts[1]

# Rebuild TopBar
old_top_bar = """[node name="TopBar" type="PanelContainer" parent="VBox"]
custom_minimum_size = Vector2(0, 60)
layout_mode = 2

[node name="HBox" type="HBoxContainer" parent="VBox/TopBar"]
layout_mode = 2
alignment = 1

[node name="FundsLabel" type="Label" parent="VBox/TopBar/HBox"]
layout_mode = 2
text = "UI_FUNDS"

[node name="FundsValue" type="Label" parent="VBox/TopBar/HBox"]
layout_mode = 2
text = "$500"

[node name="Spacer" type="Control" parent="VBox/TopBar/HBox"]
custom_minimum_size = Vector2(50, 0)
layout_mode = 2

[node name="RepLabel" type="Label" parent="VBox/TopBar/HBox"]
layout_mode = 2
text = "UI_REP"

[node name="RepValue" type="Label" parent="VBox/TopBar/HBox"]
layout_mode = 2
text = "100"

[node name="Spacer2" type="Control" parent="VBox/TopBar/HBox"]
custom_minimum_size = Vector2(50, 0)
layout_mode = 2

[node name="LangButton" type="Button" parent="VBox/TopBar/HBox"]
custom_minimum_size = Vector2(150, 40)
layout_mode = 2
text = "Language: 中文"

[node name="GameTickTimer" type="Timer" parent="."]"""

new_top_bar = """[node name="TopBar" type="PanelContainer" parent="VBox"]
custom_minimum_size = Vector2(0, 30)
layout_mode = 2

[node name="HBox" type="HBoxContainer" parent="VBox/TopBar"]
layout_mode = 2
alignment = 1

[node name="TickerLabel" type="RichTextLabel" parent="VBox/TopBar/HBox"]
layout_mode = 2
size_flags_horizontal = 3
bbcode_enabled = true
text = "[color=#888888]ARCHON CORP | DATE:[/color] [color=#ffffff]OCT 26[/color] [color=#888888]| FUNDS:[/color] [color=#39ff14]$500[/color] [color=#888888]| REP:[/color] [color=#39ff14]100[/color]"
scroll_active = false
autowrap_mode = 0

[node name="LangButton" type="Button" parent="VBox/TopBar/HBox"]
custom_minimum_size = Vector2(24, 24)
layout_mode = 2
tooltip_text = "Language"
icon = ExtResource("icon_lang")
icon_alignment = 1
expand_icon = true

[node name="GameTickTimer" type="Timer" parent="."]"""

tscn = tscn.replace(old_top_bar, new_top_bar)

# Apply neon cyan color to Bottom Action Buttons
tscn = tscn.replace('[node name="TasksBtn" type="Button" parent="VBox/BottomBar/VBox/ActionHBox"]\n', '[node name="TasksBtn" type="Button" parent="VBox/BottomBar/VBox/ActionHBox"]\nmodulate = Color(0, 1.5, 1.5, 1)\n')
tscn = tscn.replace('[node name="RecruitBtn" type="Button" parent="VBox/BottomBar/VBox/ActionHBox"]\n', '[node name="RecruitBtn" type="Button" parent="VBox/BottomBar/VBox/ActionHBox"]\nmodulate = Color(0, 1.5, 1.5, 1)\n')
tscn = tscn.replace('[node name="ExpandRoomBtn" type="Button" parent="VBox/BottomBar/VBox/ActionHBox"]\n', '[node name="ExpandRoomBtn" type="Button" parent="VBox/BottomBar/VBox/ActionHBox"]\nmodulate = Color(0, 1.5, 1.5, 1)\n')

with open(tscn_path, 'w') as f:
    f.write(tscn)

print("✅ Top Bar Rebuilt!")
