import re

files_to_fix = [
    "archon-agency-tycoon/Tests/Unit/test_office_view.gd",
    "archon-agency-tycoon/Tests/Unit/test_help_menu.gd",
    "archon-agency-tycoon/Tests/Unit/test_l2_main_integration.gd"
]

for file in files_to_fix:
    with open(file, "r") as f:
        content = f.read()
    
    # 針對 root_node 替換 (因為有些測試是用 root_node 有些是用 view)
    content = content.replace("root_node.instant_positioning = true", "root_node.agent_router = AgentRouter.new()\n\troot_node.instant_positioning = true")
    # 針對 view 替換
    content = content.replace("view.instant_positioning = true", "view.agent_router = AgentRouter.new()\n\tview.instant_positioning = true")
    
    with open(file, "w") as f:
        f.write(content)

print("Tests restored and fixed")
