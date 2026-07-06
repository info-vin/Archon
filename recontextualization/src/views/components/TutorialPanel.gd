extends ColorRect

signal request_start

@onready var start_button: Button = $VBox/StartButton

func _ready() -> void:
	start_button.pressed.connect(func():
		request_start.emit()
	)
