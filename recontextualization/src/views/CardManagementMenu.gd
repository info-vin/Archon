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

var card_slot_scene = preload("res://src/views/components/CardSlot.tscn")

func populate_lists(equipable_cards: Array, equipped_cards: Array) -> void:
    for child in unlocked_list.get_children():
        child.queue_free()
    for child in equipped_list.get_children():
        child.queue_free()
        
    for card_id in equipable_cards:
        var slot = card_slot_scene.instantiate()
        unlocked_list.add_child(slot)
        slot.setup(card_id, false)
        slot.card_clicked.connect(_on_equip_clicked.bind(slot))
        
    for card_id in equipped_cards:
        var slot = card_slot_scene.instantiate()
        equipped_list.add_child(slot)
        slot.setup(card_id, true)
        slot.card_clicked.connect(_on_unequip_clicked.bind(slot))

func _on_equip_clicked(card_id: String, slot: Node) -> void:
    # Trigger visual animation first, then emit the logic signal
    var target_pos = limit_label.global_position # Fly towards the equipped section
    slot.play_fly_anim(target_pos)
    await get_tree().create_timer(0.3).timeout
    request_equip_card.emit(card_id)

func _on_unequip_clicked(card_id: String, slot: Node) -> void:
    var target_pos = unlocked_list.global_position # Fly towards available section
    slot.play_fly_anim(target_pos)
    await get_tree().create_timer(0.3).timeout
    request_unequip_card.emit(card_id)
