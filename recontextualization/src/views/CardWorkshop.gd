extends Control
class_name CardWorkshop

signal request_add_to_furnace(card_data: Dictionary)
signal request_synthesize
signal request_return_battle
signal request_buy_catalyst

@export var inventory_container: Control
@export var slot_1: TextureRect
@export var slot_2: TextureRect
@export var slot_3: TextureRect
@export var catalyst_slot: TextureRect
@export var synthesize_btn: TextureButton
@export var status_label: Label
@export var return_btn: TextureButton
@export var buy_catalyst_btn: TextureButton
@export var output_slot: TextureRect
@onready var empty_state_label: Label = $EmptyStateLabel

var _controller: Node
var card_slot_scene = preload("res://src/views/components/CardSlot.tscn")
var tex_btn_bg = preload("res://assets/images/card_frame_blank.png")

func _update_synthesis_button() -> void:
    if not synthesize_btn: return
    
    var can_synthesize = _controller.can_synthesize() if _controller else false
    synthesize_btn.disabled = not can_synthesize
    
    var label = synthesize_btn.get_node_or_null("Label")
    if can_synthesize:
        synthesize_btn.mouse_default_cursor_shape = Control.CURSOR_POINTING_HAND
        if label:
            label.add_theme_color_override("font_color", Color(0.2, 0.9, 0.2, 1.0)) # Green
    else:
        synthesize_btn.mouse_default_cursor_shape = Control.CURSOR_FORBIDDEN
        if label:
            label.add_theme_color_override("font_color", Color(0.4, 0.4, 0.4, 1.0)) # Gray

func _ready() -> void:
    _controller = get_node_or_null("CardWorkshopController")
    if synthesize_btn:
        synthesize_btn.texture_normal = tex_btn_bg
        synthesize_btn.pressed.connect(func(): request_synthesize.emit())
    if return_btn:
        return_btn.texture_normal = tex_btn_bg
        return_btn.pressed.connect(func(): request_return_battle.emit())
    if buy_catalyst_btn:
        buy_catalyst_btn.pressed.connect(func(): request_buy_catalyst.emit())
        
    if output_slot:
        # Simple drag simulation: click to collect
        output_slot.gui_input.connect(_on_output_slot_gui_input)

func _on_output_slot_gui_input(event: InputEvent) -> void:
    if event is InputEventMouseButton and event.pressed and event.button_index == MOUSE_BUTTON_LEFT:
        # Simulate dropping into inventory with shrink animation
        var tween = create_tween()
        tween.tween_property(output_slot, "scale", Vector2(0.2, 0.2), 0.4).set_trans(Tween.TRANS_CUBIC)
        if inventory_container:
            tween.parallel().tween_property(output_slot, "global_position", inventory_container.global_position + Vector2(50, 100), 0.4)
            
        tween.tween_callback(func():
            output_slot.visible = false
            # Reset position for next time
            output_slot.set_anchors_and_offsets_preset(Control.PRESET_CENTER, Control.PRESET_MODE_KEEP_SIZE)
            show_status("已儲存至庫存！")
            request_synthesize.emit() # fake signal to controller to reset
        )

func populate_inventory(cards: Array) -> void:
    if not inventory_container: return
    for c in inventory_container.get_children(): c.queue_free()
    
    var group_by_id_level = {}
    for c in cards:
        var key = str(c["base_id"]) + "_" + str(c.get("level", 1))
        group_by_id_level[key] = group_by_id_level.get(key, 0) + 1
        
    var has_synthesizable = false
    for k in group_by_id_level:
        if group_by_id_level[k] >= 3:
            has_synthesizable = true
            break
            
    if empty_state_label:
        empty_state_label.visible = not has_synthesizable
    
    for c in cards:
        var slot = card_slot_scene.instantiate()
        slot.custom_minimum_size = Vector2(160, 220)
        inventory_container.add_child(slot)
        slot.setup(c["base_id"], false)
        if slot.has_signal("card_clicked"):
            slot.card_clicked.connect(_on_inventory_card_clicked.bind(c))
        else:
            slot.gui_input.connect(func(event: InputEvent):
                if event is InputEventMouseButton and event.pressed and event.button_index == MOUSE_BUTTON_LEFT:
                    if event.double_click:
                        _on_inventory_card_clicked("", c)
            )

func _on_inventory_card_clicked(card_id: String, card_data: Dictionary) -> void:
    request_add_to_furnace.emit(card_data)

func show_status(text: String) -> void:
    if status_label:
        status_label.text = text

func update_furnace_count(count: int) -> void:
    pass

func update_furnace_slots(cards: Array) -> void:
    var slots = [slot_1, slot_2, slot_3]
    for i in range(3):
        if not slots[i]: continue
        # Clear existing CardSlot instances
        for c in slots[i].get_children():
            c.queue_free()
        
        if i < cards.size():
            var slot = card_slot_scene.instantiate()
            slots[i].add_child(slot)
            slot.setup(cards[i]["base_id"], false)
            var p_size = slots[i].custom_minimum_size
            if p_size.x == 0: p_size = slots[i].size
            var scale_factor = min(p_size.x / 120.0, p_size.y / 160.0)
            slot.scale = Vector2(scale_factor, scale_factor)
            slot.position = (p_size - (Vector2(120.0, 160.0) * scale_factor)) / 2.0
            slots[i].self_modulate.a = 0.0 # Hide parent frame to prevent overlap
        else:
            slots[i].self_modulate.a = 1.0 # Restore frame
            
    if output_slot:
        output_slot.visible = false
        
    _update_synthesis_button()

func play_success_anim() -> void:
    if not output_slot: return
    output_slot.scale = Vector2(0.5, 0.5)
    output_slot.visible = true
    
    # Show the real output card graphic inside the slot
    for c in output_slot.get_children():
        c.queue_free()
    var result_slot = card_slot_scene.instantiate()
    output_slot.add_child(result_slot)
    var base_id = "action_keyword"
    if _controller and _controller.get("current_cards_in_furnace") and _controller.current_cards_in_furnace.size() > 0:
        base_id = _controller.current_cards_in_furnace[0]["base_id"]
    result_slot.setup(base_id, false)
    var p_size = output_slot.custom_minimum_size
    if p_size.x == 0: p_size = output_slot.size
    var scale_factor = min(p_size.x / 120.0, p_size.y / 160.0)
    result_slot.scale = Vector2(scale_factor, scale_factor)
    result_slot.position = (p_size - (Vector2(120.0, 160.0) * scale_factor)) / 2.0

    var tween = create_tween()
    tween.tween_property(output_slot, "scale", Vector2(1.1875, 1.1875), 0.5).set_trans(Tween.TRANS_CUBIC).set_ease(Tween.EASE_OUT)
    tween.parallel().tween_property(output_slot, "modulate", Color(2.0, 2.0, 2.0, 1.0), 0.2)
    tween.tween_property(output_slot, "modulate", Color.WHITE, 0.4)
    
    tween.tween_callback(func():
        # Setup simulated drag interaction after pop-in
        output_slot.mouse_filter = Control.MOUSE_FILTER_STOP
    )
    
    show_status("請將產物拖曳(點擊)回庫存區")

func play_failure_anim() -> void:
    var tween = create_tween()
    tween.tween_property(self, "position", Vector2(10, 0), 0.05)
    tween.tween_property(self, "position", Vector2(-10, 0), 0.05)
    tween.tween_property(self, "position", Vector2(10, 0), 0.05)
    tween.tween_property(self, "position", Vector2(0, 0), 0.05)
    tween.parallel().tween_property(self, "modulate", Color(1.0, 0.2, 0.2, 1.0), 0.1)
    tween.tween_property(self, "modulate", Color.WHITE, 0.2)
