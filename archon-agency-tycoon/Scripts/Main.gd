extends Control

var agent_manager
var task_manager
var tycoon_manager

@onready var funds_label: Label = $VBox/TopBar/HBox/FundsValue
@onready var dev_room: Control = $VBox/GameArea/Building/Floor1/DevRoom
@onready var tick_button: Button = $VBox/TopBar/HBox/TickButton

func _ready() -> void:
    agent_manager = preload("res://Scripts/Logic/AgentManager.gd").new()
    task_manager = preload("res://Scripts/Logic/TaskManager.gd").new()
    tycoon_manager = preload("res://Scripts/Logic/TycoonManager.gd").new()
    
    task_manager.set_agent_manager(agent_manager)
    tycoon_manager.setup_connections(task_manager)
    
    if tick_button:
        tick_button.pressed.connect(_on_tick_button_pressed)
        
    _setup_initial_game()
    _update_ui()

func _setup_initial_game() -> void:
    var agent = preload("res://Scripts/Resources/AgentResource.gd").new("Alice (DEV)", 1)
    var agent_id = agent_manager.add_agent(agent)
    
    var task = preload("res://Scripts/Resources/TaskResource.gd").new("Fix Login Bug", 1, 3, 300)
    var task_id = task_manager.add_task(task)
    task_manager.assign_task(task_id, agent_id)
    
    var agent_view_scene = preload("res://Scenes/Main/ModularAgent.tscn")
    if agent_view_scene:
        var agent_view = agent_view_scene.instantiate()
        agent_view.position = Vector2(150, 100)
        agent_view.scale = Vector2(0.5, 0.5) 
        dev_room.add_child(agent_view)

func _get_active_task_for_agent(agent_id: int) -> int:
    for i in range(task_manager.tasks.size()):
        var t = task_manager.tasks[i]
        if not t.is_completed and t.assigned_agent_id == agent_id:
            return i
    return -1

func _on_tick_button_pressed() -> void:
    # --- Auto-Boss Logic (MVP Loop) ---
    var alice = agent_manager.get_agent(0)
    var active_task_idx = _get_active_task_for_agent(0)
    
    if active_task_idx == -1: # Alice has no active task
        if alice.state == 3 or alice.energy < 30: # EXHAUSTED or tired
            alice.state = 2 # RESTING
        elif alice.state == 2 and alice.energy == 100: # RESTING and full
            alice.state = 0 # IDLE
        elif alice.state == 0: # IDLE and ready
            var ticks = randi() % 4 + 2 # 2 to 5 ticks
            var reward = (randi() % 4 + 1) * 100 # $100 to $400
            var new_task = preload("res://Scripts/Resources/TaskResource.gd").new("Auto Contract", 1, ticks, reward)
            var new_task_id = task_manager.add_task(new_task)
            task_manager.assign_task(new_task_id, 0)
            
    # --- Time Flows ---
    task_manager.process_tick()
    agent_manager.process_tick()
    _update_ui()

func _update_ui() -> void:
    funds_label.text = "$%d" % tycoon_manager.funds
    
    var status_label = dev_room.get_node_or_null("AgentStatus")
    if not status_label:
        status_label = Label.new()
        status_label.name = "AgentStatus"
        status_label.position = Vector2(10, 10)
        status_label.add_theme_color_override("font_color", Color(1, 1, 1))
        dev_room.add_child(status_label)
        
    var alice = agent_manager.get_agent(0)
    var active_task_idx = _get_active_task_for_agent(0)
    
    var state_str = "IDLE"
    if alice.state == 1: state_str = "WORKING 💦"
    elif alice.state == 2: state_str = "RESTING ☕"
    elif alice.state == 3: state_str = "EXHAUSTED 💀"
    
    var text = "Alice: %s\n體力: %d/100\n" % [state_str, alice.energy]
    
    if active_task_idx != -1:
        var task = task_manager.tasks[active_task_idx]
        text += "任務 [%s]: %d / %d" % [task.task_name, task.current_progress, task.required_ticks]
    else:
        text += "任務: [無] (等待指派或休息中...)"
        
    status_label.text = text
