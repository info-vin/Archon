extends Node2D
class_name ModularAgentView

# References to the Sprite2D layers
@onready var body_sprite: Sprite2D = $BaseBody
@onready var eyes_sprite: Sprite2D = $Eyes
@onready var hair_sprite: Sprite2D = $Hair
@onready var outfit_sprite: Sprite2D = $Outfit
@onready var tool_sprite: Sprite2D = $Tool

@onready var energy_bar: ProgressBar = $EnergyBar
@onready var status_bubble: Sprite2D = $StatusBubble

var active_tween: Tween
var default_scale_x: float = 1.0
var current_gender: int = 0
var is_custom_equipped: bool = false

# Data-driven default layout parameters loaded dynamically from the editor node properties
var default_body_pos: Vector2
var default_body_scale: Vector2
var default_eyes_pos: Vector2
var default_eyes_scale: Vector2
var default_hair_pos: Vector2
var default_hair_scale: Vector2
var default_outfit_pos: Vector2
var default_outfit_scale: Vector2
var default_tool_pos: Vector2
var default_tool_scale: Vector2

# Force default styling offsets and scaling dynamically using editor presets
func reset_layout_for_option_a() -> void:
    if body_sprite:
        body_sprite.position = default_body_pos
        body_sprite.scale = default_body_scale
        body_sprite.rotation = 0.0
        body_sprite.modulate = Color.WHITE
        
    if eyes_sprite:
        eyes_sprite.position = default_eyes_pos
        eyes_sprite.scale = default_eyes_scale
        eyes_sprite.rotation = 0.0
        
    if hair_sprite:
        hair_sprite.position = default_hair_pos
        hair_sprite.scale = default_hair_scale
        hair_sprite.rotation = 0.0
        
    if outfit_sprite:
        outfit_sprite.position = default_outfit_pos
        outfit_sprite.scale = default_outfit_scale
        outfit_sprite.rotation = 0.0
        outfit_sprite.modulate = Color.WHITE
        
    if tool_sprite:
        tool_sprite.position = default_tool_pos
        tool_sprite.scale = default_tool_scale
        tool_sprite.rotation = 0.0
        tool_sprite.modulate = Color.WHITE


func _ready() -> void:
    default_scale_x = scale.x
    
    # Dynamically record editor layout configurations
    if body_sprite:
        default_body_pos = body_sprite.position
        default_body_scale = body_sprite.scale
    if eyes_sprite:
        default_eyes_pos = eyes_sprite.position
        default_eyes_scale = eyes_sprite.scale
    if hair_sprite:
        default_hair_pos = hair_sprite.position
        default_hair_scale = hair_sprite.scale
    if outfit_sprite:
        default_outfit_pos = outfit_sprite.position
        default_outfit_scale = outfit_sprite.scale
    if tool_sprite:
        default_tool_pos = tool_sprite.position
        default_tool_scale = tool_sprite.scale
        
    if tool_sprite:
        tool_sprite.visible = true
    if status_bubble:
        status_bubble.visible = false
    _setup_animations()

func _setup_animations() -> void:
    var anim_player: AnimationPlayer = $AnimationPlayer
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

func _swap_walk_texture(frame: int) -> void:
    if is_custom_equipped:
        return
    if current_gender == 0:
        if frame == 0: equip_part("body", preload("res://Assets/Characters/Alice_Parts/part_006.png"))
        elif frame == 1: equip_part("body", preload("res://Assets/Characters/Alice_Parts/part_007.png"))
        elif frame == 2: equip_part("body", preload("res://Assets/Characters/Alice_Parts/part_008.png"))
    else:
        if frame == 0: equip_part("body", preload("res://Assets/Characters/Alice_Parts/part_010.png"))
        elif frame == 1: equip_part("body", preload("res://Assets/Characters/Alice_Parts/part_011.png"))
        elif frame == 2: equip_part("body", preload("res://Assets/Characters/Alice_Parts/part_012.png"))

# Function to equip or change a specific layer
func equip_part(layer_name: String, texture: Texture2D) -> void:
    match layer_name:
        "body":
            body_sprite.texture = texture
        "eyes":
            eyes_sprite.texture = texture
        "hair":
            hair_sprite.texture = texture
        "outfit":
            outfit_sprite.texture = texture
        "tool":
            tool_sprite.texture = texture
        _:
            push_warning("ModularAgentView: Unknown layer '%s'" % layer_name)

# Helper function to configure the appearance based on an AgentResource
func apply_agent_data(agent_data: AgentResource) -> void:
    if not is_inside_tree():
        await ready

    # Option A: Check if we have custom equipped items
    var custom_used = false
    if agent_data.equipped_hair != "":
        var tex = load(agent_data.equipped_hair)
        if tex:
            equip_part("hair", tex)
            custom_used = true
    if agent_data.equipped_outfit != "":
        var tex = load(agent_data.equipped_outfit)
        if tex:
            equip_part("outfit", tex)
            custom_used = true
    if agent_data.equipped_tool != "":
        var tex = load(agent_data.equipped_tool)
        if tex:
            equip_part("tool", tex)
            custom_used = true

    if custom_used:
        reset_layout_for_option_a()
    else:
        # 1. Base Skeleton Gender Assembly
        if agent_data.gender == 0:
            equip_part("body", preload("res://Assets/Characters/Alice_Parts/part_006.png")) # Female skeleton
        else:
            equip_part("body", preload("res://Assets/Characters/Alice_Parts/part_010.png")) # Male skeleton
            
        # 2. Eye Style
        equip_part("eyes", preload("res://Assets/Characters/Alice_Parts/part_016.png"))
        
        # 3. Hair Style Assembly
        var hair_tex = null
        match agent_data.hair_style:
            1:
                hair_tex = preload("res://Assets/Characters/Alice_Parts/part_001.png") # Long hair bow
            2:
                hair_tex = preload("res://Assets/Characters/Alice_Parts/part_015.png") # Short hair
            3:
                hair_tex = preload("res://Assets/Characters/Alice_Parts/part_017.png") # Medium pigtails
            _:
                hair_tex = preload("res://Assets/Characters/Alice_Parts/part_001.png")
        equip_part("hair", hair_tex)
        if hair_sprite:
            hair_sprite.modulate = agent_data.hair_color
            
        # 4. Outfit Style Assembly
        var outfit_tex = null
        match agent_data.outfit_style:
            1:
                outfit_tex = preload("res://Assets/Characters/Alice_Parts/part_021.png") # Mage Robe
            2:
                outfit_tex = preload("res://Assets/Characters/Alice_Parts/part_020.png") # Formal Vest
            _:
                outfit_tex = preload("res://Assets/Characters/Alice_Parts/part_021.png")
        equip_part("outfit", outfit_tex)
        
        # 5. Tool Style Assembly
        var tool_tex = null
        match agent_data.tool_style:
            1:
                tool_tex = preload("res://Assets/Characters/Alice_Parts/part_033.png") # DEV Wand
            2:
                tool_tex = preload("res://Assets/Characters/Alice_Parts/part_031.png") # SALES Cards
            3:
                tool_tex = preload("res://Assets/Characters/Alice_Parts/part_026.png") # QA Spell shield
            _:
                tool_tex = preload("res://Assets/Characters/Alice_Parts/part_033.png")
        equip_part("tool", tool_tex)
        
        reset_layout_for_option_a()

    # Update Energy Bar values & modulate color
    if energy_bar:
        energy_bar.value = agent_data.energy
        if agent_data.energy > 50:
            energy_bar.modulate = Color(0.2, 1, 0.2) # green
        elif agent_data.energy > 25:
            energy_bar.modulate = Color(1, 1, 0.2) # yellow
        else:
            energy_bar.modulate = Color(1, 0.2, 0.2) # red

    # Update status bubbles (Icon representation)
    if status_bubble:
        match agent_data.state:
            AgentResource.AgentState.WORKING:
                status_bubble.visible = true
                status_bubble.texture = preload("res://Assets/Icons/icon_coin.svg")
            AgentResource.AgentState.RESTING:
                status_bubble.visible = true
                status_bubble.texture = preload("res://Assets/Icons/icon_star.svg")
            AgentResource.AgentState.EXHAUSTED, AgentResource.AgentState.STRIKE:
                status_bubble.visible = true
                status_bubble.texture = preload("res://Assets/Icons/icon_alert.svg")
            _:
                status_bubble.visible = false

    # Alignment chair positioning & flipping
    # If working, look at computer screen direction (DEV sits right of desk, so looks left. QA looks left. SALES sits left of desk, looks right)
    if agent_data.state == AgentResource.AgentState.WORKING:
        if agent_data.role == AgentResource.AgentRole.DEV:
            scale.x = -default_scale_x
        elif agent_data.role == AgentResource.AgentRole.QA:
            scale.x = -default_scale_x
        else:
            scale.x = default_scale_x
    else:
        scale.x = default_scale_x

    # Set state fields for swap callback
    is_custom_equipped = custom_used
    current_gender = agent_data.gender

    # Automatically play correct animation based on state
    match agent_data.state:
        AgentResource.AgentState.WORKING:
            play_work_animation(agent_data)
        AgentResource.AgentState.RESTING:
            play_rest_animation(agent_data)
        AgentResource.AgentState.STRIKE:
            play_strike_animation(agent_data)
        _:
            play_idle_animation(agent_data)

# Animation hook for working state
func play_work_animation(_agent_data: AgentResource) -> void:
    if tool_sprite:
        tool_sprite.visible = true
    var anim_player: AnimationPlayer = $AnimationPlayer
    if anim_player:
        anim_player.play("work")

# Animation hook for walking state
func play_walk_animation(_agent_data: AgentResource) -> void:
    if tool_sprite:
        tool_sprite.visible = false
    var anim_player: AnimationPlayer = $AnimationPlayer
    if anim_player:
        anim_player.play("walk")

# Animation hook for resting state
func play_rest_animation(_agent_data: AgentResource) -> void:
    if tool_sprite:
        tool_sprite.visible = false
    var anim_player: AnimationPlayer = $AnimationPlayer
    if anim_player:
        anim_player.play("rest")

# Animation hook for strike state
func play_strike_animation(_agent_data: AgentResource) -> void:
    if tool_sprite:
        tool_sprite.visible = false
    var anim_player: AnimationPlayer = $AnimationPlayer
    if anim_player:
        anim_player.play("strike")

# Animation hook for idle state
func play_idle_animation(_agent_data: AgentResource) -> void:
    var anim_player: AnimationPlayer = $AnimationPlayer
    if anim_player:
        anim_player.play("idle")

func stop_animation() -> void:
    var anim_player: AnimationPlayer = $AnimationPlayer
    if anim_player:
        anim_player.stop()
        
    # Reset all transforms to default values
    if body_sprite:
        body_sprite.scale = Vector2.ONE
        body_sprite.position = Vector2.ZERO
        body_sprite.rotation = 0.0
        body_sprite.modulate = Color.WHITE
    if outfit_sprite:
        outfit_sprite.scale = Vector2.ONE
        outfit_sprite.position = Vector2.ZERO
        outfit_sprite.rotation = 0.0
    if tool_sprite:
        tool_sprite.scale = Vector2(0.8, 0.8)
        tool_sprite.position = Vector2(18, 6)
        tool_sprite.rotation = 0.0
        tool_sprite.visible = true
    if eyes_sprite:
        eyes_sprite.modulate.a = 1.0

# --- Entity Autonomy (Locomotion & Routing) ---

func walk_to(agent_data: AgentResource, target_room: Control, target_pos: Vector2, is_instant: bool = false, walk_speed: float = 180.0) -> void:
    var old_parent = get_parent()
    
    if is_instant:
        if old_parent != target_room and is_instance_valid(old_parent) and is_instance_valid(target_room):
            old_parent.remove_child(self)
            target_room.add_child(self)
        position = target_pos
        apply_agent_data(agent_data)
        return
        
    if has_meta("walk_tween"):
        var old_tween = get_meta("walk_tween")
        if old_tween and old_tween.is_valid():
            old_tween.kill()

    if old_parent != target_room:
        play_walk_animation(agent_data)
        var door_pos = Vector2(180, 300)
        var dist1 = position.distance_to(door_pos)
        var time1 = dist1 / walk_speed if dist1 > 0 else 0.05
        
        var walk_tween = create_tween()
        set_meta("walk_tween", walk_tween)
        
        walk_tween.tween_property(self, "position", door_pos, time1)
        walk_tween.tween_callback(func():
            if is_instance_valid(self) and is_instance_valid(old_parent) and is_instance_valid(target_room):
                if get_parent() == old_parent:
                    old_parent.remove_child(self)
                    target_room.add_child(self)
                position = door_pos
        )
        
        var dist2 = door_pos.distance_to(target_pos)
        var time2 = dist2 / walk_speed if dist2 > 0 else 0.05
        walk_tween.tween_property(self, "position", target_pos, time2)
        walk_tween.tween_callback(func():
            if is_instance_valid(self): apply_agent_data(agent_data)
        )
    else:
        var dist = position.distance_to(target_pos)
        if dist > 10:
            play_walk_animation(agent_data)
            var walk_tween = create_tween()
            set_meta("walk_tween", walk_tween)
            walk_tween.tween_property(self, "position", target_pos, dist / walk_speed)
            walk_tween.tween_callback(func():
                if is_instance_valid(self): apply_agent_data(agent_data)
            )
        else:
            position = target_pos
            apply_agent_data(agent_data)


