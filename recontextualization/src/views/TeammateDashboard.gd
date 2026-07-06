extends Control

signal request_return_menu
signal request_card_menu
signal request_start_dive

signal teammate_selected(idx: int)
signal model_selected(teammate_idx: int, model_idx: int)
signal react_toggled(teammate_idx: int, pressed: bool)
signal budget_changed(teammate_idx: int, val: float)

@export var teammate_list: ItemList
@export var model_option: OptionButton
@export var react_check: CheckButton
@export var budget_slider: HSlider
@export var budget_label: Label
@export var ingested_docs_label: Label
@export var back_btn: Button
@export var card_menu_btn: Button
@export var dive_btn: Button

var _controller: Node
var _current_teammate_idx: int = 0

func _ready() -> void:
    if teammate_list:
        teammate_list.item_selected.connect(_on_teammate_item_selected)
    if model_option:
        model_option.item_selected.connect(_on_model_item_selected)
    if react_check:
        react_check.toggled.connect(_on_react_toggled)
    if budget_slider:
        budget_slider.value_changed.connect(_on_budget_slider_changed)
        
    if back_btn:
        back_btn.pressed.connect(func(): request_return_menu.emit())
    if card_menu_btn:
        card_menu_btn.pressed.connect(func(): request_card_menu.emit())
    if dive_btn:
        dive_btn.pressed.connect(func(): request_start_dive.emit())

func _on_teammate_item_selected(idx: int) -> void:
    _current_teammate_idx = idx
    teammate_selected.emit(idx)

func _on_model_item_selected(idx: int) -> void:
    model_selected.emit(_current_teammate_idx, idx)

func _on_react_toggled(pressed: bool) -> void:
    react_toggled.emit(_current_teammate_idx, pressed)

func _on_budget_slider_changed(val: float) -> void:
    if budget_label:
        budget_label.text = "label_token_cap_" + str(int(val))
    budget_changed.emit(_current_teammate_idx, val)

func populate_teammates(data: Array) -> void:
    if not teammate_list: return
    teammate_list.clear()
    for t in data:
        teammate_list.add_item(t["name"] + " - Lv." + str(t["level"]))
    if teammate_list.item_count > 0:
        teammate_list.select(0)
        _current_teammate_idx = 0
        teammate_selected.emit(0)

func populate_models(models: Array) -> void:
    if not model_option: return
    model_option.clear()
    for m in models:
        model_option.add_item(m)

func update_teammate_details(model_idx: int, allow_react: bool, token_cap: float, ingested_docs: int) -> void:
    if model_option: model_option.select(model_idx)
    if react_check: react_check.button_pressed = allow_react
    if budget_slider: budget_slider.value = token_cap
    if ingested_docs_label:
        # Note: In a real i18n setup, string formatting is handled via tr() with format,
        # but for now we dynamically update the label text
        ingested_docs_label.text = "label_ingested_docs_" + str(ingested_docs)
