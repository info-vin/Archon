@tool
extends MarginContainer

@onready var chip_icon: TextureRect = $ChipSlot/ChipIcon
@onready var title_label: Label = $ChipSlot/TitleContainer/TitleLabel
@onready var desc_label: RichTextLabel = $ChipSlot/DescriptionContainer/DescriptionLabel
@onready var background: TextureRect = $BackgroundFrame

@export var chip_texture: Texture2D:
    set(val):
        chip_texture = val
        if is_inside_tree() and chip_icon != null:
            chip_icon.texture = val

@export var card_name: String = "Card Name":
    set(val):
        card_name = val
        if is_inside_tree() and title_label != null:
            title_label.text = val

@export var stats_text: String = "":
    set(val):
        stats_text = val
        if is_inside_tree() and desc_label != null:
            desc_label.text = val

var card_data: Resource = null

func set_card_data(p_card: Resource) -> void:
    card_data = p_card
    if p_card:
        setup(p_card.icon, p_card.title, "Cost: " + str(p_card.ap_cost))

func get_card_data() -> Resource:
    return card_data

func _ready():
    if chip_texture != null and chip_icon != null:
        chip_icon.texture = chip_texture
    if title_label != null:
        title_label.text = card_name
    if desc_label != null and stats_text != "":
        desc_label.text = stats_text

func setup(p_texture: Texture2D, p_card_name: String, p_stats: String = ""):
    chip_texture = p_texture
    card_name = p_card_name
    stats_text = p_stats

func _get_drag_data(_at_position: Vector2):
    var preview = duplicate()
    preview.modulate.a = 0.7
    var control = Control.new()
    control.add_child(preview)
    preview.position = -size / 2.0
    set_drag_preview(control)
    return self
