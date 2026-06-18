extends Control
class_name VectorIcon

enum IconType { TOKEN, BLOCK, DECK, DISCARD }

@export var type: IconType = IconType.TOKEN:
	set(val):
		type = val
		queue_redraw()

@export var color: Color = Color(0.3, 0.8, 1.0, 1.0): # Cyan neon by default
	set(val):
		color = val
		queue_redraw()

func _draw() -> void:
	var w = size.x
	var h = size.y
	var cx = w / 2.0
	var cy = h / 2.0
	
	# Glow effect (outer soft lines)
	var glow_color = Color(color.r, color.g, color.b, 0.2)
	for offset in range(1, 4):
		_draw_shape(cx, cy, w - offset * 2, h - offset * 2, glow_color, 4.0)
		
	# Sharp inner core line
	_draw_shape(cx, cy, w - 8, h - 8, color, 2.0)

func _draw_shape(cx: float, cy: float, w: float, h: float, col: Color, line_width: float) -> void:
	match type:
		IconType.TOKEN:
			# Crystal / Diamond Shape
			var points = PackedVector2Array([
				Vector2(cx, cy - h/2.0),
				Vector2(cx + w/2.2, cy),
				Vector2(cx, cy + h/2.0),
				Vector2(cx - w/2.2, cy),
				Vector2(cx, cy - h/2.0)
			])
			draw_polyline(points, col, line_width, true)
			
		IconType.BLOCK:
			# Shield Shape
			var points = PackedVector2Array([
				Vector2(cx - w/2.0, cy - h/2.5),
				Vector2(cx + w/2.0, cy - h/2.5),
				Vector2(cx + w/2.0, cy + h/8.0),
				Vector2(cx, cy + h/2.0),
				Vector2(cx - w/2.0, cy + h/8.0),
				Vector2(cx - w/2.0, cy - h/2.5)
			])
			draw_polyline(points, col, line_width, true)
			# Midline divider
			draw_line(Vector2(cx, cy - h/2.5), Vector2(cx, cy + h/2.2), col, line_width)
			
		IconType.DECK:
			# Stacked cards (two overlapping rectangles)
			# Back card
			var r1 = Rect2(cx - w/2.8, cy - h/2.8, w/1.8, h/1.5)
			draw_rect(r1, col, false, line_width)
			# Front card offset
			var r2 = Rect2(cx - w/3.8, cy - h/3.8, w/1.8, h/1.5)
			draw_rect(r2, col, false, line_width)
			
		IconType.DISCARD:
			# Trash Can / Recycle box: Rectangular bucket with top handle lid line and cross
			var r = Rect2(cx - w/2.2, cy - h/3.0, w/1.1, h/1.5)
			draw_rect(r, col, false, line_width)
			# Lid line
			draw_line(Vector2(cx - w/1.8, cy - h/3.0), Vector2(cx + w/1.8, cy - h/3.0), col, line_width)
			# Lid handle
			var handle = PackedVector2Array([
				Vector2(cx - w/4.0, cy - h/3.0),
				Vector2(cx - w/4.0, cy - h/2.0),
				Vector2(cx + w/4.0, cy - h/2.0),
				Vector2(cx + w/4.0, cy - h/3.0)
			])
			draw_polyline(handle, col, line_width, true)
			# Inner diagonals (X)
			draw_line(Vector2(cx - w/3.5, cy - h/5.0), Vector2(cx + w/3.5, cy + h/4.0), col, line_width)
			draw_line(Vector2(cx + w/3.5, cy - h/5.0), Vector2(cx - w/3.5, cy + h/4.0), col, line_width)
