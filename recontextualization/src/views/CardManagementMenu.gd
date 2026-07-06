extends Control

signal request_equip_card(card_id: String)
signal request_unequip_card(card_id: String)
signal request_return_menu()
signal request_teammate_dash()
signal request_start_dive()

@onready var unlocked_list = $HBoxContainer/VBoxContainer/UnlockedList
@onready var equipped_list = $HBoxContainer/VBoxContainer2/EquippedList
@onready var limit_label = $HBoxContainer/VBoxContainer2/LimitLabel

var _controller: Node

func _ready() -> void:
    if has_node("NavBox/BackButton"):
        $NavBox/BackButton.pressed.connect(func(): request_return_menu.emit())
    if has_node("NavBox/TeammateDashboardButton"):
        $NavBox/TeammateDashboardButton.pressed.connect(func(): request_teammate_dash.emit())
    if has_node("NavBox/StartDiveButton"):
        $NavBox/StartDiveButton.pressed.connect(func(): request_start_dive.emit())

func update_limit_label(current_cards: int, max_cards: int) -> void:
    limit_label.text = "Equipped (%d / %d)" % [current_cards, max_cards]

func populate_lists(equipable_cards: Array, equipped_cards: Array) -> void:
    for child in unlocked_list.get_children():
        child.queue_free()
    for child in equipped_list.get_children():
        child.queue_free()
        
    for card_id in equipable_cards:
        var btn = Button.new()
        btn.text = card_id + " (Equip)"
        btn.custom_minimum_size = Vector2(200, 50)
        btn.pressed.connect(func(): request_equip_card.emit(card_id))
        unlocked_list.add_child(btn)
        
    for card_id in equipped_cards:
        var btn = Button.new()
        btn.text = card_id + " (Unequip)"
        btn.custom_minimum_size = Vector2(200, 50)
        btn.pressed.connect(func(): request_unequip_card.emit(card_id))
        equipped_list.add_child(btn)
