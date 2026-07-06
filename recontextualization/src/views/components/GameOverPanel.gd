extends ColorRect

signal request_dashboard

@onready var restart_button: Button = $VBox/RestartButton

func _ready() -> void:
	restart_button.pressed.connect(func():
		request_dashboard.emit()
	)
