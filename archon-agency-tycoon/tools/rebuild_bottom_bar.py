import os

tscn_path = 'archon-agency-tycoon/Scenes/Main/Main.tscn'

with open(tscn_path, 'r') as f:
    tscn = f.read()

# Make sure we add ExtResources for the new icons at the top if they don't exist
new_resources = """[ext_resource type="Texture2D" path="res://Assets/Icons/icon_recruit.svg" id="icon_recruit"]
[ext_resource type="Texture2D" path="res://Assets/Icons/icon_build.svg" id="icon_build"]
[ext_resource type="Texture2D" path="res://Assets/Icons/icon_tasks.svg" id="icon_tasks"]
"""

# Completely replace the ActionHBox contents to guarantee the text is gone and icons are in
start_marker = '[node name="ActionHBox" type="HBoxContainer" parent="VBox/BottomBar/VBox"]'
end_marker = '[node name="RightPanel" type="PanelContainer" parent="VBox/HBoxMain"]'

if start_marker in tscn and end_marker in tscn:
    parts = tscn.split(start_marker)
    sub_parts = parts[1].split(end_marker)
    
    new_action_hbox = """
layout_mode = 2
theme_override_constants/separation = 20
alignment = 1

[node name="TasksBtn" type="Button" parent="VBox/BottomBar/VBox/ActionHBox"]
custom_minimum_size = Vector2(80, 80)
layout_mode = 2
tooltip_text = "UI_BACKLOG"
icon = ExtResource("icon_tasks")
icon_alignment = 1
expand_icon = true

[node name="RecruitBtn" type="Button" parent="VBox/BottomBar/VBox/ActionHBox"]
custom_minimum_size = Vector2(80, 80)
layout_mode = 2
tooltip_text = "UI_CHARACTER_CREATOR"
icon = ExtResource("icon_recruit")
icon_alignment = 1
expand_icon = true

[node name="ExpandRoomBtn" type="Button" parent="VBox/BottomBar/VBox/ActionHBox"]
custom_minimum_size = Vector2(80, 80)
layout_mode = 2
tooltip_text = "UI_EXPAND_ROOM"
icon = ExtResource("icon_build")
icon_alignment = 1
expand_icon = true

"""
    tscn = parts[0] + start_marker + new_action_hbox + end_marker + sub_parts[1]

with open(tscn_path, 'w') as f:
    f.write(tscn)

print("✅ Buttons upgraded to Icons forcefully!")
