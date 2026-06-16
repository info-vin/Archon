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
		# We need to tell Main to assign this task to Alice (Agent 0)
		# We can send a signal up or call a method on owner (Main)
		if owner.has_method("_on_task_dropped_on_agent"):
			owner._on_task_dropped_on_agent(task_id, 0) # Assuming agent 0 is Alice
