extends RefCounted
class_name AgentRouter

var room_agent_counts = {
	"dev": 0,
	"sales": 0,
	"qa": 0,
	"break": 0
}

func reset_counts() -> void:
	room_agent_counts = {"dev": 0, "sales": 0, "qa": 0, "break": 0}

func calculate_route(agent_data: AgentResource, rooms: Dictionary) -> Dictionary:
	var target_room = null
	var target_pos = Vector2(180, 200) # Fallback center
	
	var role_keys = {1: "dev", 0: "sales", 2: "qa"}
	var room_nodes = {
		1: rooms.get("dev"),
		0: rooms.get("sales"),
		2: rooms.get("qa")
	}
	
	match agent_data.state:
		1: # WORKING
			var key = role_keys.get(agent_data.role, "dev")
			target_room = room_nodes.get(agent_data.role, rooms.get("dev"))
			var slot = room_agent_counts[key]
			target_pos = _get_marker_pos(target_room, slot, "DeskPoint", Vector2(180, 200))
			room_agent_counts[key] = slot + 1
			
		2: # RESTING
			target_room = rooms.get("break")
			var slot = room_agent_counts["break"]
			target_pos = _get_marker_pos(target_room, slot, "DeskPoint", Vector2(180, 200))
			room_agent_counts["break"] = slot + 1
			
		_: # IDLE / EXHAUSTED
			var key = role_keys.get(agent_data.role, "dev")
			target_room = room_nodes.get(agent_data.role, rooms.get("dev"))
			var slot = room_agent_counts[key]
			target_pos = _get_marker_pos(target_room, slot, "StandPoint", Vector2(180, 200))
			room_agent_counts[key] = slot + 1

	return {"room": target_room, "pos": target_pos}

func _get_marker_pos(room: Node2D, slot: int, prefix: String, fallback: Vector2) -> Vector2:
	if not room: return fallback
	var markers = []
	for child in room.get_children():
		if child is Marker2D and child.name.begins_with(prefix):
			markers.append(child)
	if markers.size() > 0:
		markers.sort_custom(func(a, b): return String(a.name) < String(b.name))
		return markers[slot % markers.size()].position
	return fallback
