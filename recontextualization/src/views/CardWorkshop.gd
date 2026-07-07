extends Control
class_name CardWorkshop

signal request_add_to_furnace(card_data: Dictionary)
signal request_synthesize
signal request_return_battle
signal request_toggle_mode(is_dismantle: bool)
signal request_buy_catalyst

@export var inventory_container: Control
@export var slot_1: TextureRect
@export var slot_2: TextureRect
@export var slot_3: TextureRect
@export var catalyst_slot: TextureRect
@export var synthesize_btn: TextureButton
@export var status_label: Label
@export var return_btn: TextureButton
@export var mode_toggle_btn: TextureButton
@export var buy_catalyst_btn: TextureButton
@export var lines_container: Node2D

var _controller: Node
var is_dismantle_mode: bool = false
var card_slot_scene = preload("res://src/views/components/CardSlot.tscn")
var tex_btn_bg = preload("res://assets/images/card_frame_blank.png")

func _ready() -> void:
    if synthesize_btn:
        synthesize_btn.texture_normal = tex_btn_bg
        synthesize_btn.pressed.connect(func(): request_synthesize.emit())
    if return_btn:
        return_btn.texture_normal = tex_btn_bg
        return_btn.pressed.connect(func(): request_return_battle.emit())
    if mode_toggle_btn:
        mode_toggle_btn.texture_normal = tex_btn_bg
        mode_toggle_btn.pressed.connect(_on_toggle_mode)
    if buy_catalyst_btn:
        buy_catalyst_btn.pressed.connect(func(): request_buy_catalyst.emit())
        
    _setup_lines()

func _on_toggle_mode() -> void:
    is_dismantle_mode = not is_dismantle_mode
    if mode_toggle_btn and mode_toggle_btn.has_node("Label"):
        var txt = "當前模式: 分解 (1進2)" if is_dismantle_mode else "當前模式: 融合 (3進1)"
        mode_toggle_btn.get_node("Label").text = txt
        
    request_toggle_mode.emit(is_dismantle_mode)
    _setup_lines()

func _setup_lines() -> void:
    if not lines_container: return
    for c in lines_container.get_children():
        c.queue_free()
        
    var center = catalyst_slot.position + catalyst_slot.size / 2.0
    var p1 = slot_1.position + slot_1.size / 2.0
    var p2 = slot_2.position + slot_2.size / 2.0
    var p3 = slot_3.position + slot_3.size / 2.0
    
    if is_dismantle_mode:
        slot_1.visible = true
        slot_2.visible = true
        slot_3.visible = true
        
        slot_1.position = Vector2(-250, 0)
        slot_2.position = Vector2(150, -120)
        slot_3.position = Vector2(150, 120)
        p1 = slot_1.position + slot_1.size / 2.0
        p2 = slot_2.position + slot_2.size / 2.0
        p3 = slot_3.position + slot_3.size / 2.0
        
        _draw_line(p1, center, Color(0.8, 0.4, 0.2))
        _draw_line(center, p2, Color(0.2, 0.8, 0.4))
        _draw_line(center, p3, Color(0.2, 0.8, 0.4))
    else:
        slot_1.visible = true
        slot_2.visible = true
        slot_3.visible = true
        
        slot_1.position = Vector2(-250, -150)
        slot_2.position = Vector2(-250, 150)
        
        var p4 = Vector2(-300, 0) + slot_1.size / 2.0
        
        slot_3.position = Vector2(150, 0)
        p1 = slot_1.position + slot_1.size / 2.0
        p2 = slot_2.position + slot_2.size / 2.0
        p3 = slot_3.position + slot_3.size / 2.0
        
        _draw_line(p1, center, Color(0.2, 0.6, 0.8))
        _draw_line(p2, center, Color(0.2, 0.6, 0.8))
        _draw_line(p4, center, Color(0.2, 0.6, 0.8))
        _draw_line(center, p3, Color(0.8, 0.6, 0.2))

func _draw_line(from: Vector2, to: Vector2, color: Color) -> void:
    var line = Line2D.new()
    line.add_point(from)
    line.add_point(to)
    line.width = 4
    line.default_color = color
    var mat = CanvasItemMaterial.new()
    mat.blend_mode = CanvasItemMaterial.BLEND_MODE_ADD
    line.material = mat
    lines_container.add_child(line)

func populate_inventory(cards: Array) -> void:
    if not inventory_container: return
    for c in inventory_container.get_children(): c.queue_free()
    
    for c in cards:
        var slot = card_slot_scene.instantiate()
        inventory_container.add_child(slot)
        slot.setup(c["base_id"], false)
        slot.card_clicked.connect(_on_inventory_card_clicked.bind(c))

func _on_inventory_card_clicked(card_id: String, card_data: Dictionary) -> void:
    request_add_to_furnace.emit(card_data)

func show_status(text: String) -> void:
    if status_label:
        status_label.text = text

func update_furnace_count(count: int) -> void:
    pass

func play_success_anim() -> void:
    var tween = create_tween()
    tween.tween_property(self, "modulate", Color(2.0, 2.0, 2.0, 1.0), 0.1)
    tween.tween_property(self, "modulate", Color.WHITE, 0.3)

func play_failure_anim() -> void:
    var tween = create_tween()
    tween.tween_property(self, "position", Vector2(10, 0), 0.05)
    tween.tween_property(self, "position", Vector2(-10, 0), 0.05)
    tween.tween_property(self, "position", Vector2(10, 0), 0.05)
    tween.tween_property(self, "position", Vector2(0, 0), 0.05)
    tween.parallel().tween_property(self, "modulate", Color(1.0, 0.2, 0.2, 1.0), 0.1)
    tween.tween_property(self, "modulate", Color.WHITE, 0.2)
