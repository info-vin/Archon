extends Control

signal request_equip_card(card_id: String)
signal request_unequip_card(card_id: String)
signal request_return_menu()
signal request_teammate_dash()
signal request_start_dive()

@export var unlocked_list: Control
@export var equipped_list: Control
@export var limit_label: Label

@onready var btn_save: Button = $MainLayout/LeftPanel/LoadoutPanel/VBox/BtnSave
@onready var input_loadout: LineEdit = $MainLayout/LeftPanel/LoadoutPanel/VBox/InputLoadoutName
@onready var stat_cost: Label = $MainLayout/LeftPanel/StatsPanel/VBox/Stat1
@onready var stat_upload: Label = $MainLayout/LeftPanel/StatsPanel/VBox/Stat2
@onready var stat_cdr: Label = $MainLayout/LeftPanel/StatsPanel/VBox/Stat3
@onready var stat_stealth: Label = $MainLayout/LeftPanel/StatsPanel/VBox/Stat4

var _controller: Node

func _ready() -> void:
	if has_node("NavBox/BackButton"):
		$NavBox/BackButton.pressed.connect(func(): request_return_menu.emit())
	if has_node("NavBox/TeammateDashboardButton"):
		$NavBox/TeammateDashboardButton.pressed.connect(func(): request_teammate_dash.emit())
	if has_node("NavBox/StartDiveButton"):
		$NavBox/StartDiveButton.pressed.connect(func(): request_start_dive.emit())

func update_limit_label(current_cards: int, max_cards: int, current_cost: int, max_tokens: int) -> void:
	limit_label.text = "%s (%d / %d)\n%s: %d / %d Token" % [tr("menu_equipped_limit"), current_cards, max_cards, tr("menu_cost_limit"), current_cost, max_tokens]
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
		slot.custom_minimum_size = Vector2(160, 235)
		slot.size = Vector2(160, 235)
		var tex = load(card_dict["texture"]) if card_dict.has("texture") else null
		slot.setup(tex, card_dict["name"], card_dict["stats"])
		slot.set_meta("card_id", card_dict["id"])
		slot.gui_input.connect(_on_chip_gui_input.bind(card_dict["id"], slot, false))
		
	for card_dict in equipped_cards:
		var slot = card_chip_scene.instantiate()
		equipped_list.add_child(slot)
		slot.custom_minimum_size = Vector2(160, 235)
		slot.size = Vector2(160, 235)
		var tex = load(card_dict["texture"]) if card_dict.has("texture") else null
		slot.setup(tex, card_dict["name"], card_dict["stats"])
		slot.set_meta("card_id", card_dict["id"])
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
