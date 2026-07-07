import os, glob, re

for f in glob.glob("src/views/*Controller.gd"):
    with open(f, "r") as file:
        content = file.read()
    
    # Change @export var xyz: PackedScene to var xyz = "res://..." (if possible, or just String)
    content = re.sub(r'@export var (\w+)_scene: PackedScene', r'var \1_scene = "res://src/views/\1.tscn"', content, flags=re.IGNORECASE)
    # Some variables might be differently named
    content = content.replace("var main_menu_scene = \"res://src/views/main_menu.tscn\"", "var main_menu_scene = \"res://src/views/MainMenu.tscn\"")
    content = content.replace("var game_board_scene = \"res://src/views/game_board.tscn\"", "var game_board_scene = \"res://src/views/GameBoard.tscn\"")
    content = content.replace("var teammate_dash_scene = \"res://src/views/teammate_dash.tscn\"", "var teammate_dash_scene = \"res://src/views/TeammateDashboard.tscn\"")
    content = content.replace("var teammate_dashboard_scene = \"res://src/views/teammate_dashboard.tscn\"", "var teammate_dashboard_scene = \"res://src/views/TeammateDashboard.tscn\"")
    content = content.replace("var card_menu_scene = \"res://src/views/card_menu.tscn\"", "var card_menu_scene = \"res://src/views/CardManagementMenu.tscn\"")
    
    content = content.replace("change_scene_to_packed", "change_scene_to_file")
    
    with open(f, "w") as file:
        file.write(content)

for f in glob.glob("src/views/*.tscn"):
    with open(f, "r") as file:
        content = file.read()
    
    # Remove lines like: game_board_scene = ExtResource("3_gb")
    content = re.sub(r'^\w+_scene = ExtResource\("[^"]+"\)\n', '', content, flags=re.MULTILINE)
    # Remove [ext_resource type="PackedScene" ... ]
    content = re.sub(r'^\[ext_resource type="PackedScene" [^\]]+\]\n', '', content, flags=re.MULTILINE)
    
    with open(f, "w") as file:
        file.write(content)
