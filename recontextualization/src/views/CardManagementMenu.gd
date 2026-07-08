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

func update_limit_label(current_cards: int, max_cards: int, current_cost: int, max_tokens: int) -> void:
	limit_label.text = "核心武裝 (%d / %d)   |   算力負載: %d / %d Token" % [current_cards, max_cards, current_cost, max_tokens]
	if current_cost > max_tokens:
		limit_label.modulate = Color.RED
	else:
		limit_label.modulate = Color.WHITE

var card_chip_scene = preload("res://src/views/CardChip.tscn")

func populate_lists(equipable_cards: Array, equipped_cards: Array) -> void:
	for child in unlocked_list.get_children():
		child.queue_free()
	for child in equipped_list.get_children():
		child.queue_free()
		
	for card_dict in equipable_cards:
		var slot = card_chip_scene.instantiate()
		unlocked_list.add_child(slot)
		var tex = load(card_dict["texture"]) if card_dict.has("texture") else null
		slot.setup(tex, card_dict["name"], card_dict["stats"])
		slot.gui_input.connect(_on_chip_gui_input.bind(card_dict["id"], slot, false))
		
	for card_dict in equipped_cards:
		var slot = card_chip_scene.instantiate()
		equipped_list.add_child(slot)
		var tex = load(card_dict["texture"]) if card_dict.has("texture") else null
		slot.setup(tex, card_dict["name"], card_dict["stats"])
		slot.gui_input.connect(_on_chip_gui_input.bind(card_dict["id"], slot, true))

func _on_chip_gui_input(event: InputEvent, card_id: String, slot: Node, is_equipped: bool):
	if event is InputEventMouseButton and event.button_index == MOUSE_BUTTON_LEFT and event.pressed:
		if is_equipped:
			_on_unequip_clicked(card_id, slot)
		else:
			_on_equip_clicked(card_id, slot)

func _on_equip_clicked(card_id: String, slot: Node) -> void:
	# Add a simple pop animation
	var tween = create_tween()
	tween.tween_property(slot, "scale", Vector2(1.1, 1.1), 0.1)
	tween.tween_property(slot, "scale", Vector2(0.1, 0.1), 0.1)
	await tween.finished
	request_equip_card.emit(card_id)

func _on_unequip_clicked(card_id: String, slot: Node) -> void:
	var tween = create_tween()
	tween.tween_property(slot, "scale", Vector2(1.1, 1.1), 0.1)
	tween.tween_property(slot, "scale", Vector2(0.1, 0.1), 0.1)
	await tween.finished
	request_unequip_card.emit(card_id)
