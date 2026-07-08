@tool
extends Control
class_name CarouselContainer

@export var is_vertical: bool = false
@export var ellipse_radius: Vector2 = Vector2(250, 60)
@export var min_scale: float = 0.85
@export var max_scale: float = 1.05
@export var animation_speed: float = 10.0

var current_index: float = 0.0
var target_index: int = 0

func _ready():
    # Allow input processing for scroll wheel
    focus_mode = Control.FOCUS_ALL
    mouse_filter = Control.MOUSE_FILTER_STOP

func _gui_input(event: InputEvent) -> void:
    if event is InputEventMouseButton and event.pressed:
        if event.button_index == MOUSE_BUTTON_WHEEL_UP:
            scroll(-1)
            accept_event()
        elif event.button_index == MOUSE_BUTTON_WHEEL_DOWN:
            scroll(1)
            accept_event()

func scroll(dir: int):
    var count = get_valid_children().size()
    if count == 0: return
    target_index = (target_index + dir) % count
    if target_index < 0:
        target_index += count

func get_valid_children() -> Array:
    var valid = []
    for c in get_children():
        if c is Control and c.visible:
            valid.append(c)
    return valid

func _process(delta: float) -> void:
    var children = get_valid_children()
    var count = children.size()
    if count == 0: return
    
    # Ensure target_index is within bounds
    target_index = target_index % count
    
    var diff = target_index - current_index
    if diff > count / 2.0: diff -= count
    elif diff < -count / 2.0: diff += count
    
    if abs(diff) > 0.01:
        current_index += diff * animation_speed * delta
        if current_index >= count: current_index -= count
        if current_index < 0: current_index += count
    else:
        current_index = float(target_index)
        
    _arrange_children(children)

func _arrange_children(children: Array):
    var count = children.size()
    var center = size / 2.0
    var angle_step = PI * 2.0 / count
    
    for i in range(count):
        var child = children[i]
        
        # Calculate angle offset relative to current_index
        # We want target_index = 0 to be at the front (angle = 0)
        var offset_idx = float(i) - current_index
        
        # Wrap offset_idx to [-count/2, count/2] for shortest path math
        if offset_idx > count / 2.0: offset_idx -= count
        elif offset_idx < -count / 2.0: offset_idx += count
        
        var angle = offset_idx * angle_step
        
        var x = 0.0
        var y = 0.0
        var z = 0.0 # -1 to 1, where 1 is front
        
        if is_vertical:
            # Vertical carousel: Y is up/down, X is depth (tilt)
            y = sin(angle) * ellipse_radius.y
            x = cos(angle) * ellipse_radius.x # Front is x = radius.x
            z = cos(angle)
        else:
            # Horizontal carousel: X is left/right, Y is depth (tilt)
            x = sin(angle) * ellipse_radius.x
            y = cos(angle) * ellipse_radius.y # Front is y = +radius (bottom)
            z = cos(angle)
            
        # Dynamic scale if there are many cards
        var dynamic_max = max_scale
        var dynamic_min = min_scale
        if count > 6:
            dynamic_min = 0.6
            
        # Z maps from [-1, 1]
        var normalized_z = (z + 1.0) / 2.0 # [0, 1] where 1 is front
        var s = lerp(dynamic_min, dynamic_max, normalized_z)
        
        # We don't use pivot_offset because we center the pos manually
        var base_size = child.get_minimum_size()
        if base_size == Vector2.ZERO: base_size = child.size
        
        var pos = center + Vector2(x, y) - (base_size * s / 2.0)
        
        child.position = pos
        child.scale = Vector2(s, s)
        child.z_index = int(normalized_z * 100)

func _can_drop_data(at_position: Vector2, data: Variant) -> bool:
    return true

signal card_dropped(data)

func _drop_data(at_position: Vector2, data: Variant) -> void:
    card_dropped.emit(data)
