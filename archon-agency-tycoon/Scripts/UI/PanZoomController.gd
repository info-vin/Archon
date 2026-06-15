extends ScrollContainer
class_name PanZoomController

# Zoom configuration
@export var min_zoom: float = 0.5
@export var max_zoom: float = 2.0
@export var zoom_speed: float = 0.05

var current_zoom: float = 1.0
var touch_points: Dictionary = {}
var last_pinch_distance: float = 0.0

@onready var building: Control = $Building

func _ready() -> void:
	# Ensure the building has its pivot point at the center of the viewport or top-center
	if building:
		building.pivot_offset = Vector2.ZERO

func _gui_input(event: InputEvent) -> void:
	# Handle mouse wheel zoom for desktop
	if event is InputEventMouseButton:
		if event.button_index == MOUSE_BUTTON_WHEEL_UP and event.pressed:
			_adjust_zoom(zoom_speed, event.position)
			accept_event()
		elif event.button_index == MOUSE_BUTTON_WHEEL_DOWN and event.pressed:
			_adjust_zoom(-zoom_speed, event.position)
			accept_event()
			
	# Handle touch gestures (Mobile / iPad)
	if event is InputEventScreenTouch:
		if event.pressed:
			touch_points[event.index] = event.position
		else:
			touch_points.erase(event.index)
			if touch_points.size() < 2:
				last_pinch_distance = 0.0
				
	if event is InputEventScreenDrag:
		touch_points[event.index] = event.position
		
		# Double touch drag -> Pinch to Zoom
		if touch_points.size() == 2:
			var keys = touch_points.keys()
			var p1 = touch_points[keys[0]]
			var p2 = touch_points[keys[1]]
			var current_distance = p1.distance_to(p2)
			
			if last_pinch_distance > 0.0:
				var zoom_delta = (current_distance - last_pinch_distance) * 0.005
				var midpoint = (p1 + p2) / 2.0
				_adjust_zoom(zoom_delta, midpoint)
				
			last_pinch_distance = current_distance
			accept_event()
		
		# Single touch drag -> Pan view
		elif touch_points.size() == 1:
			scroll_horizontal -= event.relative.x
			scroll_vertical -= event.relative.y
			accept_event()

func _adjust_zoom(delta: float, zoom_center: Vector2) -> void:
	if not building:
		return
		
	var old_zoom = current_zoom
	current_zoom = clamp(current_zoom + delta, min_zoom, max_zoom)
	
	if old_zoom == current_zoom:
		return
		
	# Scale the inner building
	building.scale = Vector2(current_zoom, current_zoom)
	
	# Adjust ScrollContainer offsets to zoom towards the mouse/touch center
	var scroll_pos = Vector2(scroll_horizontal, scroll_vertical)
	var local_center = zoom_center + scroll_pos
	var new_local_center = local_center * (current_zoom / old_zoom)
	
	scroll_horizontal = int(new_local_center.x - zoom_center.x)
	scroll_vertical = int(new_local_center.y - zoom_center.y)
