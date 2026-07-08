extends Control

signal request_return_menu
signal request_card_menu
signal request_start_dive

# These signals are required by the controller
signal teammate_selected(idx: int)
signal model_selected(teammate_idx: int, model_idx: int)
signal react_toggled(teammate_idx: int, pressed: bool)
signal budget_changed(teammate_idx: int, val: float)
signal request_save_squad

@export var teammate_list: Control
@export var budget_slider: HBoxContainer
@export var budget_label: Label
@export var intel_label: RichTextLabel
@export var level_up_btn: TextureButton
@export var toggle_deploy_btn: TextureButton
@export var warning_label: Label

var icon_alice = preload("res://assets/images/avatar_alice.png")
var icon_bob = preload("res://assets/images/avatar_bob.png")
var icon_charlie = preload("res://assets/images/avatar_charlie.png")
var frame_img = preload("res://assets/images/card_frame_blank.png")

var _teammate_panels: Array[PanelContainer] = []
var _teammate_btns: Array[TextureButton] = []
var _teammate_data: Array = []

var _deployed_indices: Array[int] = []
var _current_intel_idx: int = -1

var _max_token_budget: int = 10

func _ready() -> void:
    _init_energy_bar()
                
    var return_btn = $MarginContainer/VBoxContainer/BottomNav/ReturnBtn
    if return_btn: return_btn.pressed.connect(func(): request_return_menu.emit())
    
    var save_btn = $MarginContainer/VBoxContainer/BottomNav/SaveBtn
    if save_btn: save_btn.pressed.connect(_on_save_btn_clicked)
    
    if level_up_btn:
        level_up_btn.pressed.connect(_on_level_up_clicked)
        level_up_btn.disabled = true
        
    if toggle_deploy_btn:
        toggle_deploy_btn.pressed.connect(_on_toggle_deploy_clicked)
        toggle_deploy_btn.disabled = true

func _init_energy_bar() -> void:
    if not budget_slider: return
    for c in budget_slider.get_children(): c.queue_free()
    for i in range(_max_token_budget):
        var segment = ColorRect.new()
        segment.custom_minimum_size = Vector2(25, 20)
        segment.size_flags_horizontal = Control.SIZE_EXPAND_FILL
        segment.color = Color(0.2, 0.2, 0.2, 1.0)
        budget_slider.add_child(segment)

func set_max_token_budget(budget: int) -> void:
    _max_token_budget = budget
    _init_energy_bar()
    _update_selection_visuals()

func _get_teammate_cost(t: Dictionary) -> int:
    return int(t.get("level", 1)) * 2

func populate_teammates(data: Array) -> void:
    if not teammate_list: return
    _teammate_data = data
    _teammate_panels.clear()
    _teammate_btns.clear()
    for c in teammate_list.get_children(): c.queue_free()
    _deployed_indices.clear()
    
    for i in range(data.size()):
        var t = data[i]
        var btn = TextureButton.new()
        var tname = str(t.get("name", "Unknown"))
        if "Alice" in tname: btn.texture_normal = icon_alice
        elif "Bob" in tname: btn.texture_normal = icon_bob
        elif "Charlie" in tname: btn.texture_normal = icon_charlie
        else: btn.texture_normal = icon_alice
        
        btn.custom_minimum_size = Vector2(90, 120)
        btn.ignore_texture_size = true
        btn.stretch_mode = TextureButton.STRETCH_KEEP_ASPECT_COVERED
        btn.pressed.connect(_on_teammate_item_selected.bind(i))
        
        var panel = PanelContainer.new()
        var style = StyleBoxFlat.new()
        style.bg_color = Color(0.1, 0.15, 0.2, 0.8)
        style.border_width_left = 2
        style.border_width_top = 2
        style.border_width_right = 2
        style.border_width_bottom = 2
        style.border_color = Color(0.2, 0.4, 0.6, 0.8)
        style.corner_radius_top_left = 4
        style.corner_radius_top_right = 4
        style.corner_radius_bottom_left = 4
        style.corner_radius_bottom_right = 4
        panel.add_theme_stylebox_override("panel", style)
        
        panel.add_child(btn)
        
        var mask = ColorRect.new()
        mask.color = Color(0, 0, 0, 0.6)
        mask.mouse_filter = Control.MOUSE_FILTER_IGNORE
        mask.visible = false
        mask.name = "InSquadMask"
        
        var mask_lbl = Label.new()
        mask_lbl.text = "IN SQUAD"
        mask_lbl.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
        mask_lbl.vertical_alignment = VERTICAL_ALIGNMENT_CENTER
        mask_lbl.set_anchors_preset(PRESET_FULL_RECT)
        mask_lbl.add_theme_color_override("font_color", Color(0, 1, 0.5, 1))
        mask.add_child(mask_lbl)
        
        panel.add_child(mask)
        
        teammate_list.add_child(panel)
        _teammate_panels.append(panel)
        _teammate_btns.append(btn)
        
    _update_selection_visuals()

func _on_teammate_item_selected(idx: int) -> void:
    _update_intel_panel(idx)
    teammate_selected.emit(idx)
    if level_up_btn: level_up_btn.disabled = false
    if toggle_deploy_btn: toggle_deploy_btn.disabled = false
    _update_selection_visuals()

func _on_toggle_deploy_clicked() -> void:
    if _current_intel_idx < 0: return
    
    if _deployed_indices.has(_current_intel_idx):
        _deployed_indices.erase(_current_intel_idx)
        _update_selection_visuals()
        return
        
    var cost = _get_teammate_cost(_teammate_data[_current_intel_idx])
    var current_cost = _get_current_budget()
    if current_cost + cost > _max_token_budget:
        _flash_error("指揮官算力等級不足，拒絕編制！")
        return
        
    _deployed_indices.append(_current_intel_idx)
    _update_selection_visuals()

func _get_current_budget() -> int:
    var cost = 0
    for idx in _deployed_indices:
        cost += _get_teammate_cost(_teammate_data[idx])
    return cost

func _flash_error(msg: String) -> void:
    if warning_label:
        var tween = create_tween()
        warning_label.text = msg
        warning_label.visible = true
        warning_label.modulate = Color(1, 1, 1, 1)
        tween.tween_property(warning_label, "modulate", Color(1, 0, 0, 1), 0.1)
        tween.tween_property(warning_label, "modulate", Color(1, 1, 1, 1), 0.1)
        tween.tween_property(warning_label, "modulate", Color(1, 0, 0, 1), 0.1)
        tween.tween_property(warning_label, "modulate", Color(1, 1, 1, 1), 0.1)
        tween.tween_callback(func(): 
            warning_label.visible = false
            _update_selection_visuals()
        )

func _update_selection_visuals() -> void:
    var total_cost = _get_current_budget()
            
    for i in range(_teammate_panels.size()):
        var panel = _teammate_panels[i]
        var style = panel.get_theme_stylebox("panel") as StyleBoxFlat
        var mask = panel.get_node("InSquadMask") as ColorRect
        if _deployed_indices.has(i):
            style.border_color = Color(0.0, 1.0, 0.5, 1.0)
            if mask: mask.visible = true
        else:
            style.border_color = Color(0.2, 0.4, 0.6, 0.8)
            if mask: mask.visible = false
            
    if budget_label:
        budget_label.text = "戰術預算: %d / %d" % [total_cost, _max_token_budget]
        
    if budget_slider:
        for i in range(budget_slider.get_child_count()):
            var seg = budget_slider.get_child(i)
            if i < total_cost:
                seg.color = Color(0.0, 1.0, 0.8, 1.0)
            else:
                seg.color = Color(0.2, 0.2, 0.2, 1.0)
                
    if toggle_deploy_btn and _current_intel_idx >= 0:
        var lbl = toggle_deploy_btn.get_node("Label") as Label
        if lbl:
            if _deployed_indices.has(_current_intel_idx):
                lbl.text = "✘ 解除編制"
                lbl.add_theme_color_override("font_color", Color(1, 0.4, 0.4, 1))
            else:
                lbl.text = "✔ 編制出戰"
                lbl.add_theme_color_override("font_color", Color(0, 1, 0.8, 1))

func _update_intel_panel(idx: int) -> void:
    _current_intel_idx = idx
    if not intel_label or idx < 0 or idx >= _teammate_data.size(): return
    var t = _teammate_data[idx]
    var tname = t.get("name", "Unknown")
    var level = t.get("level", 1)
    var cost = _get_teammate_cost(t)
    var rank = "C"
    if level >= 4: rank = "S"
    elif level == 3: rank = "A"
    elif level == 2: rank = "B"
    
    var color = "cyan"
    if rank == "S": color = "yellow"
    elif rank == "A": color = "purple"
    
    intel_label.text = """[b]代號:[/b] [color=%s]%s[/color]
[b]階級:[/b] %s
[b]算力消耗:[/b] %d Token
[b]引擎特性:[/b] %s
[b]基礎體力:[/b] %d
""" % [color, tname, rank, cost, t.get("description", "高級戰術特務，擅長特殊作戰與滲透任務。"), level * 100]

func _on_level_up_clicked() -> void:
    if _current_intel_idx >= 0 and _current_intel_idx < _teammate_data.size():
        var t = _teammate_data[_current_intel_idx]
        t["level"] = int(t.get("level", 1)) + 1
        _update_intel_panel(_current_intel_idx)
        _update_selection_visuals() # In case budget cost changes

func _on_save_btn_clicked() -> void:
    request_save_squad.emit()

# Old controller methods needed to avoid crash
func populate_models(models: Array) -> void: pass
func update_teammate_details(model_idx: int, allow_react: bool, token_cap: float, ingested_docs: Variant) -> void: pass
