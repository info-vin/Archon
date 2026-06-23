extends Camera2D
class_name PanZoomController

@export var min_zoom: float = 0.5
@export var max_zoom: float = 2.0
@export var zoom_speed: float = 0.1

var current_zoom: float = 1.0
var touch_points: Dictionary = {}
var last_pinch_distance: float = 0.0

func _ready() -> void:
	self.zoom = Vector2(current_zoom, current_zoom)

func _unhandled_input(event: InputEvent) -> void:
	# Desktop Mouse Wheel Zoom
	if event is InputEventMouseButton:
		if event.button_index == MOUSE_BUTTON_WHEEL_UP and event.pressed:
			_adjust_zoom(zoom_speed)
			get_viewport().set_input_as_handled()
		elif event.button_index == MOUSE_BUTTON_WHEEL_DOWN and event.pressed:
			_adjust_zoom(-zoom_speed)
			get_viewport().set_input_as_handled()
			
	# Desktop Right Click Drag Pan
	if event is InputEventMouseMotion and Input.is_mouse_button_pressed(MOUSE_BUTTON_RIGHT):
		self.position -= event.relative / self.zoom
		get_viewport().set_input_as_handled()
			
	# Mobile Touch
	if event is InputEventScreenTouch:
		if event.pressed:
			touch_points[event.index] = event.position
		else:
			touch_points.erase(event.index)
			if touch_points.size() < 2:
				last_pinch_distance = 0.0
				
	# Mobile Drag & Pinch
	if event is InputEventScreenDrag:
		touch_points[event.index] = event.position
		
		# Pinch to Zoom
		if touch_points.size() == 2:
			var keys = touch_points.keys()
			var p1 = touch_points[keys[0]]
			var p2 = touch_points[keys[1]]
			var current_distance = p1.distance_to(p2)
			
			if last_pinch_distance > 0.0:
				var zoom_delta = (current_distance - last_pinch_distance) * 0.005
				_adjust_zoom(zoom_delta)
				
			last_pinch_distance = current_distance
			get_viewport().set_input_as_handled()
		
		# Single touch Pan
		elif touch_points.size() == 1:
			self.position -= event.relative / self.zoom
			get_viewport().set_input_as_handled()

func _adjust_zoom(delta: float) -> void:
	var old_zoom = current_zoom
	current_zoom = clamp(current_zoom + delta, min_zoom, max_zoom)
	
	if old_zoom == current_zoom:
		return
		
	var mouse_pos_before = get_global_mouse_position()
	self.zoom = Vector2(current_zoom, current_zoom)
	var mouse_pos_after = get_global_mouse_position()
	
	# Adjust position to zoom towards the mouse
	self.position += mouse_pos_before - mouse_pos_after
