extends Control
class_name CardWorkshop

signal request_add_to_furnace(card_data: Dictionary)
signal request_synthesize()
signal request_return_battle()

@export var inventory_container: VBoxContainer
@export var slot_1: ColorRect
@export var slot_2: ColorRect
@export var slot_3: ColorRect
@export var catalyst_slot: ColorRect
@export var synthesize_btn: Button
@export var status_label: Label
@export var return_btn: Button

var _controller: Node

func _ready() -> void:
    if synthesize_btn:
        synthesize_btn.pressed.connect(func(): request_synthesize.emit())
    if return_btn:
        return_btn.pressed.connect(func(): request_return_battle.emit())

var list_item_scene = preload("res://src/views/components/ListItemButton.tscn")

func populate_inventory(inventory: Array) -> void:
    for child in inventory_container.get_children():
        child.queue_free()
        
    for card_data in inventory:
        var btn = list_item_scene.instantiate()
        btn.text = "%s Lv.%d" % [card_data.get("base_id", "Unknown"), card_data.get("level", 1)]
        btn.pressed.connect(func(): request_add_to_furnace.emit(card_data))
        inventory_container.add_child(btn)

func update_furnace_count(count: int) -> void:
    # Update visuals (placeholder for now)
    pass

func show_status(text: String) -> void:
    status_label.text = text

func play_success_anim() -> void:
    # Trigger big particle explosion
    pass

func play_failure_anim() -> void:
    # Trigger screen shake and glass shatter
    pass
