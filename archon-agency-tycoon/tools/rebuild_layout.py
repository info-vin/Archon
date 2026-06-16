import os

tscn_path = 'archon-agency-tycoon/Scenes/Main/Main.tscn'
gd_path = 'archon-agency-tycoon/Scripts/Main.gd'

with open(tscn_path, 'r') as f:
    tscn = f.read()

# 1. Wrap GameArea in an HBoxMain
tscn = tscn.replace(
    '[node name="GameArea" type="ScrollContainer" parent="VBox"]\nlayout_mode = 2\nsize_flags_vertical = 3',
    '[node name="HBoxMain" type="HBoxContainer" parent="VBox"]\nlayout_mode = 2\nsize_flags_vertical = 3\n\n[node name="GameArea" type="ScrollContainer" parent="VBox/HBoxMain"]\nlayout_mode = 2\nsize_flags_horizontal = 3\nsize_flags_vertical = 3'
)

# 2. Update all GameArea children paths
tscn = tscn.replace('parent="VBox/GameArea', 'parent="VBox/HBoxMain/GameArea')

# 3. Inject RightPanel before BottomBar
right_panel_nodes = """[node name="RightPanel" type="PanelContainer" parent="VBox/HBoxMain"]
custom_minimum_size = Vector2(250, 0)
layout_mode = 2

[node name="VBox" type="VBoxContainer" parent="VBox/HBoxMain/RightPanel"]
layout_mode = 2

[node name="EventLogLabel" type="Label" parent="VBox/HBoxMain/RightPanel/VBox"]
layout_mode = 2
text = "EVENT LOG"
horizontal_alignment = 1

[node name="EventLog" type="RichTextLabel" parent="VBox/HBoxMain/RightPanel/VBox"]
layout_mode = 2
size_flags_vertical = 3
bbcode_enabled = true
scroll_following = true

[node name="HSeparator" type="HSeparator" parent="VBox/HBoxMain/RightPanel/VBox"]
layout_mode = 2

[node name="AgentStatusLabel" type="Label" parent="VBox/HBoxMain/RightPanel/VBox"]
layout_mode = 2
text = "AGENT STATUS"
horizontal_alignment = 1

[node name="AgentStatusList" type="VBoxContainer" parent="VBox/HBoxMain/RightPanel/VBox"]
layout_mode = 2
size_flags_vertical = 3

[node name="BottomBar" type="PanelContainer" parent="VBox"]"""

tscn = tscn.replace('[node name="BottomBar" type="PanelContainer" parent="VBox"]', right_panel_nodes)

# 4. Shrink BottomBar and hide the giant Backlog by default
tscn = tscn.replace('custom_minimum_size = Vector2(0, 150)', 'custom_minimum_size = Vector2(0, 80)')
tscn = tscn.replace(
    '[node name="TaskContainer" type="HBoxContainer" parent="VBox/BottomBar/VBox"]\nlayout_mode = 2',
    '[node name="TaskContainer" type="HBoxContainer" parent="VBox/BottomBar/VBox"]\nvisible = false\nlayout_mode = 2'
)

with open(tscn_path, 'w') as f:
    f.write(tscn)

# 5. Update Main.gd paths
with open(gd_path, 'r') as f:
    gd = f.read()

gd = gd.replace('$VBox/GameArea/', '$VBox/HBoxMain/GameArea/')

with open(gd_path, 'w') as f:
    f.write(gd)

print("✅ Layout successfully rebuilt!")
