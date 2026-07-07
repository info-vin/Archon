extends Control

signal request_return_menu
signal request_card_menu
signal request_start_dive

signal teammate_selected(idx: int)
signal model_selected(teammate_idx: int, model_idx: int)
signal react_toggled(teammate_idx: int, pressed: bool)
signal budget_changed(teammate_idx: int, val: float)

@export var teammate_list: GridContainer
@export var model_option: TextureButton
@export var react_check: TextureButton
@export var budget_slider: HBoxContainer
@export var budget_label: Label
@export var ingested_docs_label: Label

var _controller: Node
var _current_teammate_idx: int = 0
var _current_model_idx: int = 0
var _available_models: Array = []

var icon_alice = preload("res://assets/images/avatar_alice.png")
var icon_bob = preload("res://assets/images/avatar_bob.png")
var icon_charlie = preload("res://assets/images/avatar_charlie.png")

var tex_engine = preload("res://assets/images/icon_equipment_slot.png")
var tex_toggle_off = preload("res://assets/images/icon_equipment_slot.png")
var tex_toggle_on = preload("res://assets/images/chip_green_target.png")

var _teammate_panels: Array[PanelContainer] = []
var _teammate_data: Array = []
var _selected_squad: Array[int] = []
const MAX_TOKEN_BUDGET: int = 10

func _ready() -> void:
    if model_option:
        model_option.texture_normal = tex_engine
        model_option.pressed.connect(_on_model_slot_clicked)
    if react_check:
        react_check.toggle_mode = true
        react_check.texture_normal = tex_toggle_off
        react_check.texture_pressed = tex_toggle_on
        react_check.toggled.connect(_on_react_toggled)
        
    _init_energy_bar()

func _init_energy_bar() -> void:
    if not budget_slider: return
    for i in range(MAX_TOKEN_BUDGET):
        var segment = ColorRect.new()
        segment.custom_minimum_size = Vector2(30, 20)
        segment.color = Color(0.2, 0.2, 0.2, 1.0)
        budget_slider.add_child(segment)

func _get_teammate_cost(t: Dictionary) -> int:
    return int(t.get("level", 1)) * 2

func _on_teammate_item_selected(idx: int) -> void:
    _current_teammate_idx = idx
    teammate_selected.emit(idx)
    
    if idx in _selected_squad:
        _selected_squad.erase(idx)
    else:
        if _selected_squad.size() >= 3:
            _flash_error()
            return
            
        var cost = _get_teammate_cost(_teammate_data[idx])
        var current_cost = 0
        for s_idx in _selected_squad:
            current_cost += _get_teammate_cost(_teammate_data[s_idx])
            
        if current_cost + cost > MAX_TOKEN_BUDGET:
            _flash_error()
            return
            
        _selected_squad.append(idx)
        
    _update_selection_visuals()

func _flash_error() -> void:
    if budget_label:
        var tween = create_tween()
        tween.tween_property(budget_label, "modulate", Color(1, 0, 0, 1), 0.1)
        tween.tween_property(budget_label, "modulate", Color(1, 1, 1, 1), 0.1)
        tween.tween_property(budget_label, "modulate", Color(1, 0, 0, 1), 0.1)
        tween.tween_property(budget_label, "modulate", Color(1, 1, 1, 1), 0.1)

func _update_selection_visuals() -> void:
    var total_cost = 0
    for i in range(_teammate_panels.size()):
        var panel = _teammate_panels[i]
        var style = panel.get_theme_stylebox("panel") as StyleBoxFlat
        if i in _selected_squad:
            style.border_color = Color(0.0, 1.0, 0.0, 1.0) # Green for selected
            style.border_width_left = 4
            style.border_width_top = 4
            style.border_width_right = 4
            style.border_width_bottom = 4
            total_cost += _get_teammate_cost(_teammate_data[i])
        else:
            style.border_color = Color(0.2, 0.4, 0.6, 0.8) # Default
            style.border_width_left = 2
            style.border_width_top = 2
            style.border_width_right = 2
            style.border_width_bottom = 2
            
    if budget_label:
        budget_label.text = "預算上限: %d / %d Token" % [total_cost, MAX_TOKEN_BUDGET]
        
    if budget_slider:
        for i in range(budget_slider.get_child_count()):
            var seg = budget_slider.get_child(i)
            if i < total_cost:
                seg.color = Color(0.0, 0.8, 1.0, 1.0) # Neon blue
            else:
                seg.color = Color(0.2, 0.2, 0.2, 1.0)

func populate_teammates(data: Array) -> void:
    if not teammate_list: return
    _teammate_data = data
    _teammate_panels.clear()
    for c in teammate_list.get_children(): c.queue_free()
    
    for i in range(data.size()):
        var t = data[i]
        var btn = TextureButton.new()
        var tname = str(t["name"])
        if "Alice" in tname: btn.texture_normal = icon_alice
        elif "Bob" in tname: btn.texture_normal = icon_bob
        elif "Charlie" in tname: btn.texture_normal = icon_charlie
        else: btn.texture_normal = icon_alice
        
        btn.custom_minimum_size = Vector2(100, 100)
        btn.ignore_texture_size = true
        btn.stretch_mode = TextureButton.STRETCH_KEEP_ASPECT_CENTERED
        btn.tooltip_text = tname + " - Lv." + str(t["level"])
        btn.pressed.connect(_on_teammate_item_selected.bind(i))
        
        var panel = PanelContainer.new()
        var style = StyleBoxFlat.new()
        style.bg_color = Color(0.1, 0.15, 0.2, 0.8)
        style.border_width_left = 2
        style.border_width_top = 2
        style.border_width_right = 2
        style.border_width_bottom = 2
        style.border_color = Color(0.2, 0.4, 0.6, 0.8)
        style.corner_radius_top_left = 8
        style.corner_radius_top_right = 8
        style.corner_radius_bottom_left = 8
        style.corner_radius_bottom_right = 8
        panel.add_theme_stylebox_override("panel", style)
        
        panel.add_child(btn)
        teammate_list.add_child(panel)
        _teammate_panels.append(panel)
        
    if data.size() > 0:
        _current_teammate_idx = 0
        teammate_selected.emit(0)
        _update_selection_visuals()

func populate_models(models: Array) -> void:
    _available_models = models

func update_teammate_details(model_idx: int, allow_react: bool, token_cap: float, ingested_docs: Variant) -> void:
    _current_model_idx = model_idx
    if react_check: react_check.button_pressed = allow_react
    
    if ingested_docs_label and _teammate_data.size() > _current_teammate_idx:
        var t = _teammate_data[_current_teammate_idx]
        var model_name = "未知"
        if _available_models.size() > _current_model_idx:
            model_name = _available_models[_current_model_idx]
            
        var cost = _get_teammate_cost(t)
        ingested_docs_label.text = "[ 特務情報 ]\n代號: %s\n引擎: %s\n戰術消耗: %d Token\n等級: Lv.%s" % [
            t.get("name", "Unknown"),
            model_name,
            cost,
            t.get("level", 1)
        ]

func _on_model_slot_clicked() -> void:
    pass

func _on_react_toggled(pressed: bool) -> void:
    pass

