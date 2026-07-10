extends Control

signal request_new_career
signal request_continue
signal request_teammate_dashboard
signal request_card_management
signal request_quit
signal request_language_change(new_lang: String)
signal request_volume_change(new_volume: float)

@export var lang_button: OptionButton
@export var vol_slider: HSlider

@export var btn_new_career: BaseButton
@export var btn_continue: BaseButton
@export var btn_teammate_dashboard: BaseButton
@export var btn_card_management: BaseButton
@export var btn_quit: BaseButton

func _ready() -> void:
	_connect_ui_signals()

func _connect_ui_signals() -> void:
	if btn_new_career: btn_new_career.pressed.connect(func(): request_new_career.emit())
	if btn_continue: btn_continue.pressed.connect(func(): request_continue.emit())
	if btn_teammate_dashboard: btn_teammate_dashboard.pressed.connect(func(): request_teammate_dashboard.emit())
	if btn_card_management: btn_card_management.pressed.connect(func(): request_card_management.emit())
	if btn_quit: btn_quit.pressed.connect(func(): request_quit.emit())
	
	if lang_button: lang_button.item_selected.connect(_on_lang_selected)
	if vol_slider: vol_slider.value_changed.connect(func(v): request_volume_change.emit(v))

func set_initial_settings(language: String, volume: float) -> void:
	lang_button.selected = 0 if language == "en" else 1
	vol_slider.value = volume

func _on_lang_selected(index: int) -> void:
	var lang_code = "en" if index == 0 else "zh_TW"
	request_language_change.emit(lang_code)
