extends RefCounted
class_name AgentLocomotion

func walk_to(agent_view: Node2D, agent_data: AgentResource, target_room: Node2D, target_pos: Vector2, is_instant: bool = false, walk_speed: float = 180.0) -> void:
	var old_parent = agent_view.get_parent()
	
	if is_instant:
		if old_parent != target_room and is_instance_valid(old_parent) and is_instance_valid(target_room):
			old_parent.remove_child(agent_view)
			target_room.add_child(agent_view)
		agent_view.position = target_pos
		agent_view.apply_agent_data(agent_data)
		return
		
	if agent_view.has_meta("walk_tween"):
		var old_tween = agent_view.get_meta("walk_tween")
		if old_tween and old_tween.is_valid():
			old_tween.kill()

	if old_parent != target_room:
		agent_view.play_walk_animation(agent_data)
		var door_pos = Vector2(180, 300)
		var dist1 = agent_view.position.distance_to(door_pos)
		var time1 = dist1 / walk_speed if dist1 > 0 else 0.05
		
		var walk_tween = agent_view.create_tween()
		agent_view.set_meta("walk_tween", walk_tween)
		
		walk_tween.tween_property(agent_view, "position", door_pos, time1)
		walk_tween.tween_callback(func():
			if is_instance_valid(agent_view) and is_instance_valid(old_parent) and is_instance_valid(target_room):
				if agent_view.get_parent() == old_parent:
					old_parent.remove_child(agent_view)
					target_room.add_child(agent_view)
				agent_view.position = door_pos
		)
		
		var dist2 = door_pos.distance_to(target_pos)
		var time2 = dist2 / walk_speed if dist2 > 0 else 0.05
		walk_tween.tween_property(agent_view, "position", target_pos, time2)
		walk_tween.tween_callback(func():
			if is_instance_valid(agent_view): agent_view.apply_agent_data(agent_data)
		)
	else:
		var dist = agent_view.position.distance_to(target_pos)
		if dist > 10:
			agent_view.play_walk_animation(agent_data)
			var walk_tween = agent_view.create_tween()
			agent_view.set_meta("walk_tween", walk_tween)
			walk_tween.tween_property(agent_view, "position", target_pos, dist / walk_speed)
			walk_tween.tween_callback(func():
				if is_instance_valid(agent_view): agent_view.apply_agent_data(agent_data)
			)
		else:
			agent_view.position = target_pos
			agent_view.apply_agent_data(agent_data)
