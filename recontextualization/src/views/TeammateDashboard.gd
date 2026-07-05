extends Control

signal back_requested

var _save_manager: Node
var _env_config: Node
var _current_teammate_idx: int = 0

@onready var teammate_list: ItemList = ItemList.new()
@onready var model_option: OptionButton = OptionButton.new()
@onready var react_check: CheckButton = CheckButton.new()
@onready var budget_slider: HSlider = HSlider.new()
@onready var ingested_docs_label: Label = Label.new()

func _ready() -> void:
    _save_manager = get_node_or_null("/root/SaveManager")
    _env_config = get_node_or_null("/root/EnvConfig")
    _build_ui()
    _refresh_teammates()

func _build_ui() -> void:
    var vbox = VBoxContainer.new()
    vbox.set_anchors_preset(PRESET_FULL_RECT)
    vbox.add_theme_constant_override("separation", 20)
    # Add some margin
    var margin = MarginContainer.new()
    margin.set_anchors_preset(PRESET_FULL_RECT)
    margin.add_theme_constant_override("margin_left", 40)
    margin.add_theme_constant_override("margin_right", 40)
    margin.add_theme_constant_override("margin_top", 40)
    margin.add_theme_constant_override("margin_bottom", 40)
    margin.add_child(vbox)
    add_child(margin)
    
    var title = Label.new()
    title.text = "AI 隊友管理面板 (Agent Companion Roster)"
    title.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
    vbox.add_child(title)
    
    var hbox = HBoxContainer.new()
    hbox.size_flags_vertical = Control.SIZE_EXPAND_FILL
    hbox.add_theme_constant_override("separation", 40)
    vbox.add_child(hbox)
    
    # Left: Teammate List
    var left_vbox = VBoxContainer.new()
    left_vbox.size_flags_horizontal = Control.SIZE_EXPAND_FILL
    var list_title = Label.new()
    list_title.text = "已招募代理 (Recruited Agents)"
    left_vbox.add_child(list_title)
    
    teammate_list.size_flags_vertical = Control.SIZE_EXPAND_FILL
    teammate_list.item_selected.connect(_on_teammate_selected)
    left_vbox.add_child(teammate_list)
    hbox.add_child(left_vbox)
    
    # Right: Config Panel
    var config_vbox = VBoxContainer.new()
    config_vbox.size_flags_horizontal = Control.SIZE_EXPAND_FILL
    config_vbox.add_theme_constant_override("separation", 20)
    var config_title = Label.new()
    config_title.text = "推理策略設定 (Reasoning Strategy)"
    config_vbox.add_child(config_title)
    hbox.add_child(config_vbox)
    
    # Model Selection
    var model_hbox = HBoxContainer.new()
    var model_label = Label.new()
    model_label.text = "裝備模型 (Equipped Model):"
    
    if _env_config and _env_config.models.size() > 0:
        for m in _env_config.models:
            model_option.add_item(m.get("display_name", m.get("id")))
    else:
        model_option.add_item("Local/Fallback Model")
        
    model_option.item_selected.connect(_on_model_selected)
    model_hbox.add_child(model_label)
    model_hbox.add_child(model_option)
    config_vbox.add_child(model_hbox)
    
    # ReAct Switch
    var react_hbox = HBoxContainer.new()
    var react_label = Label.new()
    react_label.text = "專家反思與多步推論 (ReAct):"
    react_check.toggled.connect(_on_react_toggled)
    react_hbox.add_child(react_label)
    react_hbox.add_child(react_check)
    config_vbox.add_child(react_hbox)
    
    # Budget Slider
    var budget_vbox = VBoxContainer.new()
    var budget_label = Label.new()
    budget_label.text = "單次檢索 Token 預算 (Token Cap): 500"
    budget_vbox.add_child(budget_label)
    
    budget_slider.min_value = 100
    budget_slider.max_value = 2000
    budget_slider.step = 100
    budget_slider.value_changed.connect(func(val):
        budget_label.text = "單次檢索 Token 預算 (Token Cap): " + str(val)
        _on_budget_changed(val)
    )
    budget_vbox.add_child(budget_slider)
    config_vbox.add_child(budget_vbox)
    
    # Ingested Docs
    ingested_docs_label.text = "知識庫配置：已吸收文件數: 0"
    config_vbox.add_child(ingested_docs_label)
    
    # Spacer
    var spacer = Control.new()
    spacer.size_flags_vertical = Control.SIZE_EXPAND_FILL
    config_vbox.add_child(spacer)
    
    # Back Button
    var back_btn = Button.new()
    back_btn.text = "返回 (Back)"
    back_btn.custom_minimum_size = Vector2(200, 50)
    back_btn.size_flags_horizontal = Control.SIZE_SHRINK_CENTER
    back_btn.pressed.connect(func(): back_requested.emit())
    vbox.add_child(back_btn)

func _refresh_teammates() -> void:
    teammate_list.clear()
    if not _save_manager or _save_manager.teammates.is_empty():
        # Default teammates for initialization
        if _save_manager:
            var def_model = "gemini-1.5-flash"
            if _env_config: def_model = _env_config.default_model
            
            _save_manager.teammates.append({
                "id": "alice_flash",
                "name": "Alice (Socializer)",
                "level": 1,
                "ingested_docs": 0,
                "equipped_model": def_model,
                "allow_react": false,
                "token_cap": 500
            })
            _save_manager.teammates.append({
                "id": "bob_pro",
                "name": "Bob (Deductor)",
                "level": 3,
                "ingested_docs": 12,
                "equipped_model": _env_config.models[1].get("id") if _env_config and _env_config.models.size() > 1 else def_model,
                "allow_react": true,
                "token_cap": 1500
            })
            _save_manager.save_progress()
            
    if _save_manager and _save_manager.teammates.size() > 0:
        for t in _save_manager.teammates:
            var display_name = t.get("name", t.get("id", "Unknown"))
            teammate_list.add_item(display_name + " - Lv." + str(t.get("level", 1)))
        
        # Select first
        if teammate_list.item_count > 0:
            teammate_list.select(_current_teammate_idx)
            _on_teammate_selected(_current_teammate_idx)

func _on_teammate_selected(idx: int) -> void:
    _current_teammate_idx = idx
    if not _save_manager or idx >= _save_manager.teammates.size():
        return
        
    var t = _save_manager.teammates[idx]
    
    # Sync UI
    var def_model = "gemini-1.5-flash"
    if _env_config: def_model = _env_config.default_model
    var equipped = t.get("equipped_model", def_model)
    var model_idx = 0
    if _env_config: model_idx = _env_config.get_model_index_by_id(equipped)
    model_option.select(model_idx)
    
    react_check.button_pressed = t.get("allow_react", false)
    budget_slider.value = t.get("token_cap", 500)
    ingested_docs_label.text = "知識庫配置：已吸收文件數: " + str(t.get("ingested_docs", 0))

func _on_model_selected(idx: int) -> void:
    if not _save_manager or _current_teammate_idx >= _save_manager.teammates.size(): return
    var model_str = "gemini-1.5-flash"
    if _env_config: model_str = _env_config.get_model_id_by_index(idx)
    _save_manager.teammates[_current_teammate_idx]["equipped_model"] = model_str
    _save_manager.save_progress()

func _on_react_toggled(button_pressed: bool) -> void:
    if not _save_manager or _current_teammate_idx >= _save_manager.teammates.size(): return
    _save_manager.teammates[_current_teammate_idx]["allow_react"] = button_pressed
    _save_manager.save_progress()

func _on_budget_changed(val: float) -> void:
    if not _save_manager or _current_teammate_idx >= _save_manager.teammates.size(): return
    _save_manager.teammates[_current_teammate_idx]["token_cap"] = int(val)
    _save_manager.save_progress()
