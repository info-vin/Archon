import re

with open("archon-agency-tycoon/Scripts/Main.gd", "r") as f:
    content = f.read()

# 1. 宣告 AgentRouter
content = content.replace("var agent_views = {}", "var agent_views = {}\nvar agent_router: AgentRouter = AgentRouter.new()")

# 2. 修改 _update_ui 迴圈邏輯
old_loop = """	var room_agent_counts = {
		"dev": 0,
		"sales": 0,
		"qa": 0,
		"break": 0
	}
	
	var walk_speed = 180.0
	var door_pos = Vector2(180, 300)
	
	for agent_id in agent_views.keys():
		var agent = agent_manager.get_agent(agent_id)
		var view = agent_views[agent_id]
		if not agent or not view: continue
			
		var target_info = _get_agent_target(agent, room_agent_counts)
		var target_room = target_info.room
		var target_pos = target_info.pos
				
		if target_room:
			view.update_state_and_move(agent, target_room, target_pos, instant_positioning, walk_speed)"""

new_loop = """	agent_router.reset_counts()
	var walk_speed = 180.0
	var rooms_dict = {"dev": dev_room, "sales": sales_room, "qa": qa_room, "break": break_room}
	
	for agent_id in agent_views.keys():
		var agent = agent_manager.get_agent(agent_id)
		var view = agent_views[agent_id]
		if not agent or not view: continue
			
		var target_info = agent_router.calculate_route(agent, rooms_dict)
		if target_info.room:
			view.walk_to(agent, target_info.room, target_info.pos, instant_positioning, walk_speed)"""

content = content.replace(old_loop, new_loop)

# 3. 刪除 Main.gd 中已經搬移的 _get_agent_target 和 _get_marker_pos
pattern = r"func _get_agent_target\(agent, counts: Dictionary\) -> Dictionary:.*?return \{\"room\": room, \"pos\": pos\}\n\n"
content = re.sub(pattern, "", content, flags=re.DOTALL)

pattern2 = r"func _get_marker_pos\(room: Control, slot: int, prefix: String, fallback: Vector2\) -> Vector2:.*?(?=var current_lang_index)"
content = re.sub(pattern2, "", content, flags=re.DOTALL)

with open("archon-agency-tycoon/Scripts/Main.gd", "w") as f:
    f.write(content)
print("Main.gd refactored.")
