extends Node2D
class_name ModularAgentView

# References to the Sprite2D layers
@onready var body_sprite: Sprite2D = $BaseBody
@onready var eyes_sprite: Sprite2D = $Eyes
@onready var hair_sprite: Sprite2D = $Hair
@onready var outfit_sprite: Sprite2D = $Outfit
@onready var tool_sprite: Sprite2D = $Tool

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
    # This is where we would load specific textures based on the agent's role
    # For example, if agent_data.role == AgentResource.AgentRole.DEV:
    #     equip_part("outfit", preload("res://Assets/Outfits/magical_robe.png"))
    #     equip_part("tool", preload("res://Assets/Tools/magic_cards.png"))
    pass

# Animation hook (called by AnimationPlayer or Tween)
func play_work_animation() -> void:
    # E.g., bob the tool sprite up and down
    var tween = create_tween().set_loops(0) # Infinite loop
    tween.tween_property(tool_sprite, "position:y", -5.0, 0.5).as_relative()
    tween.tween_property(tool_sprite, "position:y", 5.0, 0.5).as_relative()

func stop_animation() -> void:
    # Logic to return to idle pose
    pass
