extends Label
class_name TimerUI

var turn_timer: float
var config: Resource

func setup(p_config: Resource, initial_timer: float) -> void:
	config = p_config
	turn_timer = initial_timer
	horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	add_theme_font_size_override("font_size", config.timer_font_size_normal)
	position = Vector2(576 - 120, 10)
	size = Vector2(240, 40)
	update_display()

func update_display() -> void:
	var display_time = ceil(turn_timer)
	text = str(display_time) + "s"
	if display_time <= 5:
		add_theme_font_size_override("font_size", config.timer_font_size_alert)
		add_theme_color_override("font_color", Color(1.0, 0.2, 0.2))
	else:
		add_theme_font_size_override("font_size", config.timer_font_size_normal)
		add_theme_color_override("font_color", Color(1.0, 1.0, 1.0))

func tick(delta: float) -> bool:
	turn_timer -= delta
	update_display()
	return turn_timer <= 0.0

func reset(new_time: float) -> void:
	turn_timer = new_time
	update_display()
