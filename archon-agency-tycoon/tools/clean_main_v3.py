import re
with open("archon-agency-tycoon/Scripts/Main.gd", "r") as f:
    content = f.read()
# 強制刪除 _get_marker_pos
pattern = r"func _get_marker_pos\(room: Control, slot: int, prefix: String, fallback: Vector2\) -> Vector2:.*?(?=\n\nvar help_menu_instance)"
content = re.sub(pattern, "", content, flags=re.DOTALL)
with open("archon-agency-tycoon/Scripts/Main.gd", "w") as f:
    f.write(content)
