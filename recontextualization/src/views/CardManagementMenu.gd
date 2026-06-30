extends Control

@onready var unlocked_list = $HBoxContainer/VBoxContainer/UnlockedList
@onready var equipped_list = $HBoxContainer/VBoxContainer2/EquippedList
@onready var limit_label = $HBoxContainer/VBoxContainer2/LimitLabel

var sm: Node

func _ready() -> void:
    if Engine.has_singleton("SaveManager"):
        sm = Engine.get_singleton("SaveManager")
    
    $BackButton.pressed.connect(_on_back_pressed)
    _refresh_lists()

func _refresh_lists() -> void:
    if not sm: return
    
    # Clear existing
    for child in unlocked_list.get_children():
        child.queue_free()
    for child in equipped_list.get_children():
        child.queue_free()
        
    var max_cards = sm.get_max_equipped_cards()
    var current_cards = sm.equipped_action_cards.size()
    limit_label.text = "Equipped (%d / %d)" % [current_cards, max_cards]
    
    for card_id in sm.unlocked_action_cards:
        if not card_id in sm.equipped_action_cards:
            var btn = Button.new()
            btn.text = card_id + " (Equip)"
            btn.custom_minimum_size = Vector2(200, 50)
            btn.pressed.connect(func(): _on_equip_card(card_id))
            unlocked_list.add_child(btn)
            
    for card_id in sm.equipped_action_cards:
        var btn = Button.new()
        btn.text = card_id + " (Unequip)"
        btn.custom_minimum_size = Vector2(200, 50)
        btn.pressed.connect(func(): _on_unequip_card(card_id))
        equipped_list.add_child(btn)

func _on_equip_card(card_id: String) -> void:
    if not sm: return
    if sm.equipped_action_cards.size() < sm.get_max_equipped_cards():
        if not card_id in sm.equipped_action_cards:
            sm.equipped_action_cards.append(card_id)
            sm.save_progress()
            _refresh_lists()

func _on_unequip_card(card_id: String) -> void:
    if not sm: return
    if card_id in sm.equipped_action_cards:
        sm.equipped_action_cards.erase(card_id)
        sm.save_progress()
        _refresh_lists()

func _on_back_pressed() -> void:
    get_tree().change_scene_to_file("res://src/views/MainMenu.tscn")
