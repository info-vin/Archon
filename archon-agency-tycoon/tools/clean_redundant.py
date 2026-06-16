import os

tscn_path = 'archon-agency-tycoon/Scenes/Main/Main.tscn'

with open(tscn_path, 'r') as f:
    tscn = f.read()

backlog_label = """[node name="Label" type="Label" parent="VBox/BottomBar/VBox"]
layout_mode = 2
text = "UI_BACKLOG"
horizontal_alignment = 1

"""

tscn = tscn.replace(backlog_label, "")

with open(tscn_path, 'w') as f:
    f.write(tscn)

print("✅ Redundant backlog label removed from tscn!")
