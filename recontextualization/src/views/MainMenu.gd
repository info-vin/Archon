extends Control

signal request_new_career
signal request_continue
signal request_card_management
signal request_quit
signal request_language_change(new_lang: String)
signal request_volume_change(new_volume: float)

@onready var lang_button: OptionButton = $VBoxContainer/SettingsBox/LangBox/LangButton
@onready var vol_slider: HSlider = $VBoxContainer/SettingsBox/VolBox/VolSlider

func _ready() -> void:
	_connect_ui_signals()

func _connect_ui_signals() -> void:
	$VBoxContainer/NewCareerButton.pressed.connect(func(): request_new_career.emit())
	$VBoxContainer/ContinueButton.pressed.connect(func(): request_continue.emit())
	$VBoxContainer/CardManagementButton.pressed.connect(func(): request_card_management.emit())
	$VBoxContainer/QuitButton.pressed.connect(func(): request_quit.emit())
	
	lang_button.item_selected.connect(_on_lang_selected)
	vol_slider.value_changed.connect(func(v): request_volume_change.emit(v))

func set_initial_settings(language: String, volume: float) -> void:
	lang_button.selected = 0 if language == "en" else 1
	vol_slider.value = volume

func _on_lang_selected(index: int) -> void:
	var lang_code = "en" if index == 0 else "zh_TW"
	request_language_change.emit(lang_code)

