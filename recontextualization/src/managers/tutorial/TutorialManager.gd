extends Node

@onready var overlay_scene = preload("res://src/views/tutorial/TutorialOverlay.tscn")
var overlay_instance: Node

var states: Dictionary = {}
var current_state: Node

func _ready() -> void:
    # Add to group for easy access
    add_to_group("tutorial_manager")
    
    # Instantiate the overlay
    overlay_instance = overlay_scene.instantiate()
    add_child(overlay_instance)
    
    # Load and setup states
    _register_state("Welcome", "res://src/managers/tutorial/states/State_01_Welcome.gd")
    _register_state("Search", "res://src/managers/tutorial/states/State_02_Search.gd")
    _register_state("DragData", "res://src/managers/tutorial/states/State_03_DragData.gd")
    _register_state("Deliver", "res://src/managers/tutorial/states/State_04_Deliver.gd")
    
    # Wait a frame to let UI settle, then start
    call_deferred("_start_tutorial")

func _register_state(state_name: String, script_path: String) -> void:
    var state = load(script_path).new()
    state.name = state_name
    add_child(state)
    state.setup(self)
    state.transitioned.connect(_on_state_transitioned)
    states[state_name] = state

func _start_tutorial() -> void:
    _on_state_transitioned("Welcome")

func _process(delta: float) -> void:
    if current_state:
        current_state.update(delta)

func _on_state_transitioned(new_state_name: String) -> void:
    if current_state:
        current_state.exit()
        
    if new_state_name == "End":
        _end_tutorial()
        return
        
    if states.has(new_state_name):
        current_state = states[new_state_name]
        current_state.enter()
    else:
        push_error("TutorialManager: State not found: " + new_state_name)

func show_dialog(text: String, wait_for_click: bool = true) -> void:
    overlay_instance.show_dialog(text, wait_for_click)
    if wait_for_click:
        await overlay_instance.dialog_advanced

func focus_node(target: Control) -> void:
    unfocus() # Remove any existing focus
    if not target: return
    
    var focus_scene = preload("res://src/managers/tutorial/FocusFrame.tscn")
    var focus_inst = focus_scene.instantiate()
    target.add_child(focus_inst)
    focus_inst.set_anchors_preset(Control.PRESET_FULL_RECT)
    focus_inst.add_to_group("tutorial_focus_frames")

func unfocus() -> void:
    for f in get_tree().get_nodes_in_group("tutorial_focus_frames"):
        if is_instance_valid(f):
            f.queue_free()

func set_mask_transparent() -> void:
    overlay_instance.set_mask_transparent()

func set_mask_dark() -> void:
    overlay_instance.set_mask_dark()

func _end_tutorial() -> void:
    print("Tutorial Completed!")
    var game_state = get_node_or_null("/root/GameState")
    if game_state != null:
        game_state.is_tutorial_active = false
        
    var sm = get_node_or_null("/root/SaveManager")
    if sm != null:
        sm.has_completed_tutorial = true
        sm.save_progress()
    
    if is_instance_valid(overlay_instance):
        overlay_instance.queue_free()
        
    queue_free()

func is_blocking_noise_drag() -> bool:
    if current_state and current_state.name == "DragData":
        return true
    return false
