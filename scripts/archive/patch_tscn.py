import re

with open("src/views/GameBoard.tscn", "r") as f:
    content = f.read()

# 1. Add ext_resources for the new components right after the last ext_resource
ext_resources = """
[ext_resource type="PackedScene" uid="uid://cxgb456hud1" path="res://src/views/components/GameHUD.tscn" id="1_hud"]
[ext_resource type="PackedScene" uid="uid://cxgb456tut1" path="res://src/views/components/TutorialPanel.tscn" id="2_tut"]
[ext_resource type="PackedScene" uid="uid://cxgb456gov1" path="res://src/views/components/GameOverPanel.tscn" id="3_gov"]
"""

# Find the last ext_resource
last_ext_idx = content.rfind("[ext_resource")
end_of_last_ext_line = content.find("\n", last_ext_idx)
content = content[:end_of_last_ext_line+1] + ext_resources.strip() + "\n" + content[end_of_last_ext_line+1:]

# 2. Replace the TopBar node block with GameHUD instance
# We need to remove from [node name="TopBar" to the next [node name="QueryBar"
start_idx = content.find('[node name="TopBar"')
end_idx = content.find('[node name="QueryBar"')

hud_instance = '[node name="GameHUD" parent="MarginContainer/VBoxContainer" instance=ExtResource("1_hud")]\n\n'
content = content[:start_idx] + hud_instance + content[end_idx:]

# 3. Replace TutorialPanel block
start_idx = content.find('[node name="TutorialPanel"')
end_idx = content.find('[node name="GameOverPanel"')
tut_instance = '[node name="TutorialPanel" parent="." instance=ExtResource("2_tut")]\n\n'
content = content[:start_idx] + tut_instance + content[end_idx:]

# 4. Replace GameOverPanel block
start_idx = content.find('[node name="GameOverPanel"')
# The GameOverPanel block ends either at the end of the file, or at the next node.
# Let's find the next node.
end_idx = content.find('[node name="PauseMenu"', start_idx)
gov_instance = '[node name="GameOverPanel" parent="." instance=ExtResource("3_gov")]\n\n'
content = content[:start_idx] + gov_instance + content[end_idx:]

with open("src/views/GameBoard.tscn", "w") as f:
    f.write(content)
