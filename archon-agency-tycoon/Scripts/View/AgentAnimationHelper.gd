extends RefCounted
class_name AgentAnimationHelper

func setup_animations(anim_player: AnimationPlayer) -> void:
	if not anim_player:
		return
	if anim_player.has_animation_library(""):
		anim_player.remove_animation_library("")
	
	var lib := AnimationLibrary.new()
	
	# 1. idle
	var idle_anim := Animation.new()
	idle_anim.loop_mode = Animation.LOOP_LINEAR
	idle_anim.length = 1.0
	var track_body_scale = idle_anim.add_track(Animation.TYPE_VALUE)
	idle_anim.track_set_path(track_body_scale, "BaseBody:scale")
	idle_anim.track_insert_key(track_body_scale, 0.0, Vector2(1.0, 1.0))
	idle_anim.track_insert_key(track_body_scale, 0.5, Vector2(1.0, 0.97))
	idle_anim.track_insert_key(track_body_scale, 1.0, Vector2(1.0, 1.0))
	var track_outfit_scale = idle_anim.add_track(Animation.TYPE_VALUE)
	idle_anim.track_set_path(track_outfit_scale, "Outfit:scale")
	idle_anim.track_insert_key(track_outfit_scale, 0.0, Vector2(1.0, 1.0))
	idle_anim.track_insert_key(track_outfit_scale, 0.5, Vector2(1.0, 0.97))
	idle_anim.track_insert_key(track_outfit_scale, 1.0, Vector2(1.0, 1.0))
	lib.add_animation("idle", idle_anim)
	
	# 2. walk
	var walk_anim := Animation.new()
	walk_anim.loop_mode = Animation.LOOP_LINEAR
	walk_anim.length = 0.6
	var track_body_pos = walk_anim.add_track(Animation.TYPE_VALUE)
	walk_anim.track_set_path(track_body_pos, "BaseBody:position")
	walk_anim.track_insert_key(track_body_pos, 0.0, Vector2.ZERO)
	walk_anim.track_insert_key(track_body_pos, 0.15, Vector2(0, -6))
	walk_anim.track_insert_key(track_body_pos, 0.3, Vector2.ZERO)
	walk_anim.track_insert_key(track_body_pos, 0.45, Vector2(0, -6))
	walk_anim.track_insert_key(track_body_pos, 0.6, Vector2.ZERO)
	var track_body_rot = walk_anim.add_track(Animation.TYPE_VALUE)
	walk_anim.track_set_path(track_body_rot, "BaseBody:rotation_degrees")
	walk_anim.track_insert_key(track_body_rot, 0.0, 0.0)
	walk_anim.track_insert_key(track_body_rot, 0.15, 3.0)
	walk_anim.track_insert_key(track_body_rot, 0.3, 0.0)
	walk_anim.track_insert_key(track_body_rot, 0.45, -3.0)
	walk_anim.track_insert_key(track_body_rot, 0.6, 0.0)
	var track_walk_method = walk_anim.add_track(Animation.TYPE_METHOD)
	walk_anim.track_set_path(track_walk_method, ".")
	walk_anim.track_insert_key(track_walk_method, 0.0, {"method": "_swap_walk_texture", "args": [0]})
	walk_anim.track_insert_key(track_walk_method, 0.15, {"method": "_swap_walk_texture", "args": [1]})
	walk_anim.track_insert_key(track_walk_method, 0.3, {"method": "_swap_walk_texture", "args": [0]})
	walk_anim.track_insert_key(track_walk_method, 0.45, {"method": "_swap_walk_texture", "args": [2]})
	lib.add_animation("walk", walk_anim)
	
	# 3. work
	var work_anim := Animation.new()
	work_anim.loop_mode = Animation.LOOP_LINEAR
	work_anim.length = 0.8
	var track_work_tool_y = work_anim.add_track(Animation.TYPE_VALUE)
	work_anim.track_set_path(track_work_tool_y, "Tool:position:y")
	work_anim.track_insert_key(track_work_tool_y, 0.0, 6.0)
	work_anim.track_insert_key(track_work_tool_y, 0.2, -8.0)
	work_anim.track_insert_key(track_work_tool_y, 0.4, 6.0)
	work_anim.track_insert_key(track_work_tool_y, 0.6, -8.0)
	work_anim.track_insert_key(track_work_tool_y, 0.8, 6.0)
	var track_work_tool_rot = work_anim.add_track(Animation.TYPE_VALUE)
	work_anim.track_set_path(track_work_tool_rot, "Tool:rotation_degrees")
	work_anim.track_insert_key(track_work_tool_rot, 0.0, 0.0)
	work_anim.track_insert_key(track_work_tool_rot, 0.2, 15.0)
	work_anim.track_insert_key(track_work_tool_rot, 0.4, 0.0)
	work_anim.track_insert_key(track_work_tool_rot, 0.6, 15.0)
	work_anim.track_insert_key(track_work_tool_rot, 0.8, 0.0)
	var track_work_body_scale = work_anim.add_track(Animation.TYPE_VALUE)
	work_anim.track_set_path(track_work_body_scale, "BaseBody:scale:y")
	work_anim.track_insert_key(track_work_body_scale, 0.0, 1.0)
	work_anim.track_insert_key(track_work_body_scale, 0.2, 0.95)
	work_anim.track_insert_key(track_work_body_scale, 0.4, 1.0)
	work_anim.track_insert_key(track_work_body_scale, 0.6, 0.95)
	work_anim.track_insert_key(track_work_body_scale, 0.8, 1.0)
	var track_work_method = work_anim.add_track(Animation.TYPE_METHOD)
	work_anim.track_set_path(track_work_method, ".")
	work_anim.track_insert_key(track_work_method, 0.0, {"method": "_swap_walk_texture", "args": [0]})
	work_anim.track_insert_key(track_work_method, 0.2, {"method": "_swap_walk_texture", "args": [1]})
	work_anim.track_insert_key(track_work_method, 0.4, {"method": "_swap_walk_texture", "args": [0]})
	work_anim.track_insert_key(track_work_method, 0.6, {"method": "_swap_walk_texture", "args": [2]})
	lib.add_animation("work", work_anim)
	
	# 4. rest
	var rest_anim := Animation.new()
	rest_anim.loop_mode = Animation.LOOP_LINEAR
	rest_anim.length = 1.6
	var track_rest_body_scale = rest_anim.add_track(Animation.TYPE_VALUE)
	rest_anim.track_set_path(track_rest_body_scale, "BaseBody:scale:y")
	rest_anim.track_insert_key(track_rest_body_scale, 0.0, 1.0)
	rest_anim.track_insert_key(track_rest_body_scale, 0.8, 0.95)
	rest_anim.track_insert_key(track_rest_body_scale, 1.6, 1.0)
	var track_rest_outfit_scale = rest_anim.add_track(Animation.TYPE_VALUE)
	rest_anim.track_set_path(track_rest_outfit_scale, "Outfit:scale:y")
	rest_anim.track_insert_key(track_rest_outfit_scale, 0.0, 1.0)
	rest_anim.track_insert_key(track_rest_outfit_scale, 0.8, 0.95)
	rest_anim.track_insert_key(track_rest_outfit_scale, 1.6, 1.0)
	var track_rest_eyes_mod = rest_anim.add_track(Animation.TYPE_VALUE)
	rest_anim.track_set_path(track_rest_eyes_mod, "Eyes:modulate:a")
	rest_anim.track_insert_key(track_rest_eyes_mod, 0.0, 1.0)
	rest_anim.track_insert_key(track_rest_eyes_mod, 0.8, 0.2)
	rest_anim.track_insert_key(track_rest_eyes_mod, 1.6, 1.0)
	lib.add_animation("rest", rest_anim)
	
	# 5. strike
	var strike_anim := Animation.new()
	strike_anim.loop_mode = Animation.LOOP_LINEAR
	strike_anim.length = 0.4
	var track_strike_pos_x = strike_anim.add_track(Animation.TYPE_VALUE)
	strike_anim.track_set_path(track_strike_pos_x, "BaseBody:position:x")
	strike_anim.track_insert_key(track_strike_pos_x, 0.0, 0.0)
	strike_anim.track_insert_key(track_strike_pos_x, 0.1, -2.0)
	strike_anim.track_insert_key(track_strike_pos_x, 0.2, 2.0)
	strike_anim.track_insert_key(track_strike_pos_x, 0.3, -2.0)
	strike_anim.track_insert_key(track_strike_pos_x, 0.4, 0.0)
	var track_strike_modulate = strike_anim.add_track(Animation.TYPE_VALUE)
	strike_anim.track_set_path(track_strike_modulate, "BaseBody:modulate")
	strike_anim.track_insert_key(track_strike_modulate, 0.0, Color.WHITE)
	strike_anim.track_insert_key(track_strike_modulate, 0.2, Color(1.0, 0.5, 0.5))
	strike_anim.track_insert_key(track_strike_modulate, 0.4, Color.WHITE)
	lib.add_animation("strike", strike_anim)
	
	anim_player.add_animation_library("", lib)
