extends CanvasLayer

@onready var mask_rect = $MaskRect
@onready var dialog_box = $DialogBox
@onready var dialog_label = $DialogBox/MarginContainer/HBoxContainer/DialogLabel
@onready var continue_hint = $DialogBox/MarginContainer/HBoxContainer/ContinueHint

signal dialog_advanced

var is_typing = false
var full_text = ""
var type_timer = 0.0
const TYPE_SPEED = 0.03

func _ready():
    mask_rect.color = Color(0, 0, 0, 0.35)
    dialog_box.hide()

func _input(event):
    var is_advance_action = false
    if event is InputEventMouseButton and event.pressed and event.button_index == MOUSE_BUTTON_LEFT:
        is_advance_action = true
    elif event is InputEventKey and event.pressed and (event.keycode == KEY_SPACE or event.keycode == KEY_ENTER):
        is_advance_action = true

    if is_advance_action:
        if dialog_box.visible:
            if is_typing:
                # Skip typing
                is_typing = false
                dialog_label.text = full_text
                continue_hint.show()
                get_viewport().set_input_as_handled()
            else:
                dialog_box.hide()
                dialog_advanced.emit()
                get_viewport().set_input_as_handled()

func _process(delta):
    if is_typing:
        type_timer += delta
        if type_timer >= TYPE_SPEED:
            type_timer = 0.0
            var current_len = dialog_label.text.length()
            if current_len < full_text.length():
                dialog_label.text += full_text[current_len]
            else:
                is_typing = false
                continue_hint.show()

func show_dialog(text: String):
    dialog_box.show()
    full_text = text
    dialog_label.text = ""
    is_typing = true
    type_timer = 0.0
    continue_hint.hide()

func set_mask_transparent():
    mask_rect.color = Color(0, 0, 0, 0.0)

func set_mask_dark():
    mask_rect.color = Color(0, 0, 0, 0.35)
