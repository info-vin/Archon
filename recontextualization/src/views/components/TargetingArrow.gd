extends Line2D
class_name TargetingArrow

@export var control_point_height: float = -200.0
@export var segments: int = 30

func update_curve(start_pos: Vector2, end_pos: Vector2) -> void:
	clear_points()
	var control_pos: Vector2 = (start_pos + end_pos) / 2.0
	control_pos.y += control_point_height
	
	for i in range(segments + 1):
		var t: float = float(i) / float(segments)
		var p: Vector2 = _bezier_interpolate(start_pos, control_pos, end_pos, t)
		add_point(p)

func _bezier_interpolate(p0: Vector2, p1: Vector2, p2: Vector2, t: float) -> Vector2:
	var q0: Vector2 = p0.lerp(p1, t)
	var q1: Vector2 = p1.lerp(p2, t)
	return q0.lerp(q1, t)

func show_arrow() -> void:
	show()

func hide_arrow() -> void:
	hide()
