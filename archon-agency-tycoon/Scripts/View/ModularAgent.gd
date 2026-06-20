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

# Layout data configurations mapping for the two paper doll asset styles (Pixel Art vs Legacy SVG)
const PIXEL_LAYOUT = {
    "body": {"pos": Vector2.ZERO, "scale": Vector2.ONE},
    "eyes": {"pos": Vector2(0, -27), "scale": Vector2.ONE},
    "hair": {"pos": Vector2(0, -18), "scale": Vector2.ONE},
    "outfit": {"pos": Vector2(0, 2), "scale": Vector2.ONE},
    "tool": {"pos": Vector2(18, 6), "scale": Vector2(0.8, 0.8)}
}

const SVG_LAYOUT = {
    "body": {"pos": Vector2.ZERO, "scale": Vector2.ONE},
    "eyes": {"pos": Vector2(0, -180), "scale": Vector2(0.12, 0.12)},
    "hair": {"pos": Vector2(0, -220), "scale": Vector2(0.7, 0.7)},
    "outfit": {"pos": Vector2(0, 10), "scale": Vector2(0.75, 0.75)},
    "tool": {"pos": Vector2(150, -50), "scale": Vector2(0.4, 0.4)}
}

# Force default styling offsets and scaling dynamically using editor presets
func reset_layout_for_option_a() -> void:
    if body_sprite:
        body_sprite.position = PIXEL_LAYOUT.body.pos
        body_sprite.scale = PIXEL_LAYOUT.body.scale
        body_sprite.rotation = 0.0
        body_sprite.modulate = Color.WHITE
        
    if eyes_sprite:
        eyes_sprite.position = PIXEL_LAYOUT.eyes.pos
        eyes_sprite.scale = PIXEL_LAYOUT.eyes.scale
        eyes_sprite.rotation = 0.0
        
    if hair_sprite:
        hair_sprite.position = PIXEL_LAYOUT.hair.pos
        hair_sprite.scale = PIXEL_LAYOUT.hair.scale
        hair_sprite.rotation = 0.0
        
    if outfit_sprite:
        outfit_sprite.position = PIXEL_LAYOUT.outfit.pos
        outfit_sprite.scale = PIXEL_LAYOUT.outfit.scale
        outfit_sprite.rotation = 0.0
        outfit_sprite.modulate = Color.WHITE
        
    if tool_sprite:
        tool_sprite.position = PIXEL_LAYOUT.tool.pos
        tool_sprite.scale = PIXEL_LAYOUT.tool.scale
        tool_sprite.rotation = 0.0
        tool_sprite.modulate = Color.WHITE

func reset_layout_for_option_b() -> void:
    if body_sprite:
        body_sprite.position = SVG_LAYOUT.body.pos
        body_sprite.scale = SVG_LAYOUT.body.scale
        body_sprite.rotation = 0.0
        body_sprite.modulate = Color.WHITE
        
    if eyes_sprite:
        eyes_sprite.position = SVG_LAYOUT.eyes.pos
        eyes_sprite.scale = SVG_LAYOUT.eyes.scale
        eyes_sprite.rotation = 0.0
        
    if hair_sprite:
        hair_sprite.position = SVG_LAYOUT.hair.pos
        hair_sprite.scale = SVG_LAYOUT.hair.scale
        hair_sprite.rotation = 0.0
        
    if outfit_sprite:
        outfit_sprite.position = SVG_LAYOUT.outfit.pos
        outfit_sprite.scale = SVG_LAYOUT.outfit.scale
        outfit_sprite.rotation = 0.0
        outfit_sprite.modulate = Color.WHITE
        
    if tool_sprite:
        tool_sprite.position = SVG_LAYOUT.tool.pos
        tool_sprite.scale = SVG_LAYOUT.tool.scale
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
    var anim_player = $AnimationPlayer
    if anim_player:
        var helper = preload("res://Scripts/View/AgentAnimationHelper.gd").new()
        helper.setup_animations(anim_player)

func _swap_walk_texture(frame: int) -> void:
    # Disable texture swapping to keep base body head visible and prevent walk flickering
    return

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
        reset_layout_for_option_b()
    else:
        # 1. Base Skeleton Gender Assembly
        if agent_data.gender == 0:
            equip_part("body", preload("res://Assets/Characters/Alice_Parts/part_006.png")) # Female skeleton
        else:
            equip_part("body", preload("res://Assets/Characters/Alice_Parts/part_010.png")) # Male skeleton
            
        # 2. Eye Style - Disabled to prevent part_016.png (Alice's default head) from overlapping with custom hair
        equip_part("eyes", null)
        
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
    var locomotion = preload("res://Scripts/View/AgentLocomotion.gd").new()
    locomotion.walk_to(self, agent_data, target_room, target_pos, is_instant, walk_speed)


