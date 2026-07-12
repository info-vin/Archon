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

@onready var carousel = $UIPanel/CarouselContainer
@onready var sfx_click = $SFXClick

var _is_animating = false

func _ready() -> void:
	_connect_ui_signals()

func _unhandled_input(event: InputEvent) -> void:
	if _is_animating: return
	
	if event.is_action_pressed("ui_left"):
		if carousel: carousel.scroll(-1)
	elif event.is_action_pressed("ui_right"):
		if carousel: carousel.scroll(1)
	elif event.is_action_pressed("ui_accept"):
		if carousel: _trigger_action(carousel.target_index)

func _connect_ui_signals() -> void:
	if btn_new_career: btn_new_career.pressed.connect(func(): _trigger_action(0))
	if btn_continue: btn_continue.pressed.connect(func(): _trigger_action(1))
	if btn_teammate_dashboard: btn_teammate_dashboard.pressed.connect(func(): _trigger_action(2))
	if btn_card_management: btn_card_management.pressed.connect(func(): _trigger_action(3))
	if btn_quit: btn_quit.pressed.connect(func(): _trigger_action(4))
	
	if lang_button: lang_button.item_selected.connect(_on_lang_selected)
	if vol_slider: vol_slider.value_changed.connect(func(v): request_volume_change.emit(v))

func _trigger_action(index: int) -> void:
	if _is_animating: return
	_is_animating = true
	
	if sfx_click: sfx_click.play()
	
	var target_node: Control = null
	var target_signal: Callable = Callable()
	
	match index:
		0: 
			target_node = btn_new_career
			target_signal = func(): request_new_career.emit()
		1: 
			target_node = btn_continue
			target_signal = func(): request_continue.emit()
		2: 
			target_node = btn_teammate_dashboard
			target_signal = func(): request_teammate_dashboard.emit()
		3: 
			target_node = btn_card_management
			target_signal = func(): request_card_management.emit()
		4: 
			target_node = btn_quit
			target_signal = func(): request_quit.emit()
			
	if target_node:
		var original_x = target_node.position.x
		var tween = create_tween()
		tween.set_trans(Tween.TRANS_ELASTIC).set_ease(Tween.EASE_OUT)
		tween.tween_property(target_node, "position:x", original_x + 30.0, 0.1)
		tween.tween_property(target_node, "position:x", original_x - 30.0, 0.1)
		tween.tween_property(target_node, "position:x", original_x, 0.1)
		tween.finished.connect(func():
			_is_animating = false
			target_signal.call()
		)
	else:
		_is_animating = false
		target_signal.call()

func set_initial_settings(language: String, volume: float) -> void:
	if lang_button: lang_button.selected = 0 if language == "en" else 1
	if vol_slider: vol_slider.value = volume

func _on_lang_selected(index: int) -> void:
	var lang_code = "en" if index == 0 else "zh_TW"
	request_language_change.emit(lang_code)
