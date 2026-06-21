extends "res://Scripts/UI/OfficeRoom.gd"
class_name DevRoomDropZone

# This script is attached to the DevRoom or the agent to handle drops

func _can_drop_data(at_position: Vector2, data: Variant) -> bool:
	if typeof(data) == TYPE_DICTIONARY and data.has("type") and data["type"] == "task":
		return true
	return false

func _drop_data(at_position: Vector2, data: Variant) -> void:
	if typeof(data) == TYPE_DICTIONARY and data.has("type") and data["type"] == "task":
		var task_id = data["task_id"]
		var role = 1 # DEV by default
		if "Sales" in room_name:
			role = 0
		elif "QA" in room_name:
			role = 2
		
		if owner.has_method("_assign_task_to_free_agent_in_role"):
			owner._assign_task_to_free_agent_in_role(task_id, role)
