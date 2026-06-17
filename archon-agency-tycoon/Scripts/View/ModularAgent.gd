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

# Force zero offset and standard scaling if using standard parts
func reset_layout_for_option_a() -> void:
    # 1. Base skeleton positioning
    if body_sprite:
        body_sprite.position = Vector2.ZERO
        body_sprite.scale = Vector2.ONE
        body_sprite.rotation = 0.0
        body_sprite.modulate = Color.WHITE
        
    # 2. Eyes reside on head: Y-offset is -27
    if eyes_sprite:
        eyes_sprite.position = Vector2(0, -27)
        eyes_sprite.scale = Vector2.ONE
        eyes_sprite.rotation = 0.0
        
    # 3. Hair sits on top of skull: Y-offset is -18
    if hair_sprite:
        hair_sprite.position = Vector2(0, -18)
        hair_sprite.scale = Vector2.ONE
        hair_sprite.rotation = 0.0
        
    # 4. Outfit covers torso: Y-offset is 2
    if outfit_sprite:
        outfit_sprite.position = Vector2(0, 2)
        outfit_sprite.scale = Vector2.ONE
        outfit_sprite.rotation = 0.0
        outfit_sprite.modulate = Color.WHITE
        
    # 5. Tool held in hand: X-offset is 18, Y-offset is 6, scaled to 0.8
    if tool_sprite:
        tool_sprite.position = Vector2(18, 6)
        tool_sprite.scale = Vector2(0.8, 0.8)
        tool_sprite.rotation = 0.0
        tool_sprite.modulate = Color.WHITE


func _ready() -> void:
    default_scale_x = scale.x
    if tool_sprite:
        tool_sprite.visible = true
    if status_bubble:
        status_bubble.visible = false

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
            AgentResource.AgentState.EXHAUSTED:
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

    # Automatically play correct animation based on state
    match agent_data.state:
        AgentResource.AgentState.WORKING:
            play_work_animation(agent_data)
        AgentResource.AgentState.RESTING:
            play_rest_animation(agent_data)
        _:
            stop_animation()

# Animation hook for working state
func play_work_animation(agent_data: AgentResource) -> void:
    stop_animation()
    
    if tool_sprite:
        tool_sprite.visible = true
    
    active_tween = create_tween().set_loops()
    # Tool swings back and forth
    active_tween.tween_property(tool_sprite, "position:y", -8.0, 0.2).set_trans(Tween.TRANS_SINE)
    active_tween.parallel().tween_property(tool_sprite, "rotation_degrees", 15.0, 0.2)
    active_tween.tween_property(tool_sprite, "position:y", 0.0, 0.2).set_trans(Tween.TRANS_SINE)
    active_tween.parallel().tween_property(tool_sprite, "rotation_degrees", 0.0, 0.2)
    
    # Body bobs slightly
    active_tween.parallel().tween_property(body_sprite, "scale:y", 0.95, 0.2)
    active_tween.tween_property(body_sprite, "scale:y", 1.0, 0.2)
    
    # 🏃 Sequence frame swapping step (Working action frames loop)
    # We swap textures in parallel to simulate hands typing / working
    if agent_data.gender == 0:
        # Female action sequence (part_006: Stand, part_007: Move leg left, part_008: Move leg right)
        active_tween.parallel().tween_callback(func(): equip_part("body", preload("res://Assets/Characters/Alice_Parts/part_007.png"))).set_delay(0.1)
        active_tween.tween_callback(func(): equip_part("body", preload("res://Assets/Characters/Alice_Parts/part_008.png"))).set_delay(0.2)
        active_tween.tween_callback(func(): equip_part("body", preload("res://Assets/Characters/Alice_Parts/part_006.png"))).set_delay(0.1)
    else:
        # Male action sequence (part_010: Stand, part_011: Move leg left, part_012: Move leg right)
        active_tween.parallel().tween_callback(func(): equip_part("body", preload("res://Assets/Characters/Alice_Parts/part_011.png"))).set_delay(0.1)
        active_tween.tween_callback(func(): equip_part("body", preload("res://Assets/Characters/Alice_Parts/part_012.png"))).set_delay(0.2)
        active_tween.tween_callback(func(): equip_part("body", preload("res://Assets/Characters/Alice_Parts/part_010.png"))).set_delay(0.1)

# Animation hook for walking state
func play_walk_animation(agent_data: AgentResource) -> void:
    stop_animation()
    
    if tool_sprite:
        tool_sprite.visible = false
        
    active_tween = create_tween().set_loops()
    # Body bobs up and down quickly
    active_tween.tween_property(body_sprite, "position:y", -4.0, 0.15).set_trans(Tween.TRANS_SINE)
    active_tween.tween_property(body_sprite, "position:y", 0.0, 0.15).set_trans(Tween.TRANS_SINE)
    
    # Swap leg textures
    if agent_data.gender == 0:
        active_tween.parallel().tween_callback(func(): equip_part("body", preload("res://Assets/Characters/Alice_Parts/part_007.png"))).set_delay(0.07)
        active_tween.tween_callback(func(): equip_part("body", preload("res://Assets/Characters/Alice_Parts/part_008.png"))).set_delay(0.15)
        active_tween.tween_callback(func(): equip_part("body", preload("res://Assets/Characters/Alice_Parts/part_006.png"))).set_delay(0.07)
    else:
        active_tween.parallel().tween_callback(func(): equip_part("body", preload("res://Assets/Characters/Alice_Parts/part_011.png"))).set_delay(0.07)
        active_tween.tween_callback(func(): equip_part("body", preload("res://Assets/Characters/Alice_Parts/part_012.png"))).set_delay(0.15)
        active_tween.tween_callback(func(): equip_part("body", preload("res://Assets/Characters/Alice_Parts/part_010.png"))).set_delay(0.07)

# Animation hook for resting state
func play_rest_animation(agent_data: AgentResource) -> void:
    stop_animation()
    
    if tool_sprite:
        tool_sprite.visible = false
        
    active_tween = create_tween().set_loops()
    # Breathing effect: Body and Outfit scale up and down slowly
    active_tween.tween_property(body_sprite, "scale:y", 0.95, 0.8).set_trans(Tween.TRANS_SINE)
    if outfit_sprite:
        active_tween.parallel().tween_property(outfit_sprite, "scale:y", 0.95, 0.8).set_trans(Tween.TRANS_SINE)
    
    active_tween.tween_property(body_sprite, "scale:y", 1.0, 0.8).set_trans(Tween.TRANS_SINE)
    if outfit_sprite:
        active_tween.parallel().tween_property(outfit_sprite, "scale:y", 1.0, 0.8).set_trans(Tween.TRANS_SINE)
        
    # Dim eyes (sleepy/eyes closed effect)
    if eyes_sprite:
        active_tween.parallel().tween_property(eyes_sprite, "modulate:a", 0.2, 0.8)
        active_tween.tween_property(eyes_sprite, "modulate:a", 1.0, 0.8)

func stop_animation() -> void:
    if active_tween and active_tween.is_valid():
        active_tween.kill()
        active_tween = null
        
    # Reset all transforms to default values
    if body_sprite:
        body_sprite.scale = Vector2.ONE
        body_sprite.position = Vector2.ZERO
        body_sprite.rotation = 0.0
    if outfit_sprite:
        outfit_sprite.scale = Vector2.ONE
        outfit_sprite.position = Vector2.ZERO
        outfit_sprite.rotation = 0.0
    if tool_sprite:
        tool_sprite.scale = Vector2.ONE
        tool_sprite.position = Vector2.ZERO
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


