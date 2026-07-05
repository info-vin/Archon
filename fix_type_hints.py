import glob
import os
import re

files_to_fix = [
    'recontextualization/src/managers/tutorial/states/State_02_Search.gd',
    'recontextualization/src/managers/tutorial/states/State_03_DragData.gd',
    'recontextualization/src/managers/tutorial/states/State_04_Deliver.gd',
    'recontextualization/src/managers/tutorial/TutorialManager.gd',
    'recontextualization/src/network/BackendClient.gd',
    'recontextualization/src/views/CardWorkshop.gd',
    'recontextualization/src/views/CharacterDashboard.gd',
    'recontextualization/src/views/MainMenu.gd',
    'recontextualization/src/views/PlayArea.gd'
]

for filepath in files_to_fix:
    if not os.path.exists(filepath): continue
    with open(filepath, 'r') as f:
        content = f.read()

    # Replace var sm = -> var sm: Node =
    content = re.sub(r'var\s+sm\s*=\s*\(Engine\.get_singleton', r'var sm: Node = (Engine.get_singleton', content)
    
    # Replace var game_state = -> var game_state: Node =
    content = re.sub(r'var\s+game_state\s*=\s*\(Engine\.get_singleton', r'var game_state: Node = (Engine.get_singleton', content)
    
    # Replace var event_bus = -> var event_bus: Node =
    content = re.sub(r'var\s+event_bus\s*=\s*\(Engine\.get_singleton', r'var event_bus: Node = (Engine.get_singleton', content)

    # In State_04_Deliver
    content = re.sub(r'var\s+current_scene\s*=\s*manager\.get_tree', r'var current_scene: Node = manager.get_tree', content)
    content = re.sub(r'var\s+deliver_btn\s*=\s*current_scene\.find_child', r'var deliver_btn: Node = current_scene.find_child', content)
    
    # In State_03_DragData and State_02_Search
    content = re.sub(r'var\s+hand_container\s*=\s*current_scene\.find_child', r'var hand_container: Node = current_scene.find_child', content)
    content = re.sub(r'var\s+query_bar\s*=\s*current_scene\.find_child', r'var query_bar: Node = current_scene.find_child', content)

    with open(filepath, 'w') as f:
        f.write(content)
    print(f"Added type hints to {filepath}")

