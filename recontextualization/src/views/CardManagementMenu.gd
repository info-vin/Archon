extends Control

signal request_equip_card(card_id: String)
signal request_unequip_card(card_id: String)
signal request_return_menu()
signal request_teammate_dash()
signal request_start_dive()

@export var unlocked_list: Control
@export var equipped_list: Control
@export var limit_label: Label

var _controller: Node

func _ready() -> void:
    if has_node("NavBox/BackButton"):
        $NavBox/BackButton.pressed.connect(func(): request_return_menu.emit())
    if has_node("NavBox/TeammateDashboardButton"):
        $NavBox/TeammateDashboardButton.pressed.connect(func(): request_teammate_dash.emit())
    if has_node("NavBox/StartDiveButton"):
        $NavBox/StartDiveButton.pressed.connect(func(): request_start_dive.emit())

func update_limit_label(current_cards: int, max_cards: int) -> void:
    limit_label.text = "掛載插槽 (Equipped) (%d / %d)" % [current_cards, max_cards]

var list_item_scene = preload("res://src/views/components/ListItemButton.tscn")

func _style_card_btn(btn: Button) -> void:
    var style = StyleBoxFlat.new()
    style.bg_color = Color(0.1, 0.15, 0.25, 0.8)
    style.border_width_left = 2
    style.border_width_top = 2
    style.border_width_right = 2
    style.border_width_bottom = 2
    style.border_color = Color(0.3, 0.8, 1.0, 0.5)
    style.corner_radius_top_left = 4
    style.corner_radius_top_right = 4
    style.corner_radius_bottom_left = 4
    style.corner_radius_bottom_right = 4
    btn.add_theme_stylebox_override("normal", style)
    
    var hover_style = style.duplicate()
    hover_style.bg_color = Color(0.2, 0.3, 0.5, 0.9)
    hover_style.border_color = Color(0.6, 1.0, 1.0, 0.8)
    btn.add_theme_stylebox_override("hover", hover_style)
    
    btn.custom_minimum_size = Vector2(0, 80)
    btn.alignment = HORIZONTAL_ALIGNMENT_LEFT

func populate_lists(equipable_cards: Array, equipped_cards: Array) -> void:
    for child in unlocked_list.get_children():
        child.queue_free()
    for child in equipped_list.get_children():
        child.queue_free()
        
    for card_id in equipable_cards:
        var btn = list_item_scene.instantiate()
        btn.text = " [+] 【%s】\n     Type: Action | Cost: 1 AP" % [card_id.to_upper()]
        _style_card_btn(btn)
        btn.pressed.connect(func(): request_equip_card.emit(card_id))
        unlocked_list.add_child(btn)
        
    for card_id in equipped_cards:
        var btn = list_item_scene.instantiate()
        btn.text = " [-] 【%s】\n     [ EQUIPPED ]" % [card_id.to_upper()]
        _style_card_btn(btn)
        var eq_style = btn.get_theme_stylebox("normal").duplicate()
        eq_style.border_color = Color(1.0, 0.8, 0.2, 0.8)
        btn.add_theme_stylebox_override("normal", eq_style)
        btn.pressed.connect(func(): request_unequip_card.emit(card_id))
        equipped_list.add_child(btn)
