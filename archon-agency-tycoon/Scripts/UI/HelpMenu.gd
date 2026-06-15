extends PanelContainer

signal closed

func _ready() -> void:
    # Set default neon styling and border
    modulate = Color(1, 1, 1, 0)
    # Animate pop in
    var tween = create_tween()
    tween.tween_property(self, "modulate:a", 1.0, 0.25).set_trans(Tween.TRANS_SINE)
    
    # Connect close button
    var close_btn = get_node_or_null("VBox/CloseButton")
    if close_btn:
        close_btn.pressed.connect(close)

func _unhandled_input(event: InputEvent) -> void:
    if event.is_action_pressed("ui_cancel"): # Escape key by default in Godot
        close()
        get_viewport().set_input_as_handled()

func close() -> void:
    var tween = create_tween()
    tween.tween_property(self, "modulate:a", 0.0, 0.2).set_trans(Tween.TRANS_SINE)
    await tween.finished
    closed.emit()
    queue_free()
