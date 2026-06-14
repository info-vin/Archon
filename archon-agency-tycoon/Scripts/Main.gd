extends Control

var agent_manager
var task_manager
var tycoon_manager

@onready var funds_label: Label = $VBox/TopBar/HBox/FundsValue
@onready var dev_room: Control = $VBox/GameArea/Building/Floor1/DevRoom
@onready var tick_button: Button = $VBox/TopBar/HBox/TickButton
@onready var task_container: HBoxContainer = $VBox/BottomBar/VBox/TaskContainer

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
    # 招募一位工程師 Alice
    var agent = preload("res://Scripts/Resources/AgentResource.gd").new("Alice (DEV)", 1)
    var agent_id = agent_manager.add_agent(agent)
    
    # 產生幾個任務放在 Backlog
    _spawn_task_in_backlog("Fix Login Bug", 3, 300)
    _spawn_task_in_backlog("Update DB Schema", 2, 200)
    _spawn_task_in_backlog("Write Unit Tests", 4, 400)
    
    # 紙娃娃實體化
    var agent_view_scene = preload("res://Scenes/Main/ModularAgent.tscn")
    if agent_view_scene:
        var agent_view = agent_view_scene.instantiate()
        agent_view.position = Vector2(150, 100)
        agent_view.scale = Vector2(0.5, 0.5) 
        dev_room.add_child(agent_view)
        
    # 掛載 Drop Zone 到 DevRoom
    var drop_script = preload("res://Scripts/UI/DevRoomDropZone.gd")
    if drop_script:
        dev_room.set_script(drop_script)

func _spawn_task_in_backlog(t_name: String, ticks: int, reward: int) -> void:
    var task = preload("res://Scripts/Resources/TaskResource.gd").new(t_name, 1, ticks, reward)
    var task_id = task_manager.add_task(task)
    
    var card_scene = preload("res://Scenes/UI/TaskCard.tscn")
    if card_scene and task_container:
        var card = card_scene.instantiate()
        task_container.add_child(card)
        card.setup(task_id, t_name, ticks, reward)

func _on_task_dropped_on_agent(task_id: int, agent_id: int) -> void:
    var success = task_manager.assign_task(task_id, agent_id)
    if success:
        # 移除 UI 上的卡片
        for child in task_container.get_children():
            if child is TaskCard and child.task_id == task_id:
                child.queue_free()
                break
        _update_ui()
    else:
        print("無法指派！(可能體力不足或非閒置狀態)")

func _get_active_task_for_agent(agent_id: int) -> int:
    for i in range(task_manager.tasks.size()):
        var t = task_manager.tasks[i]
        if not t.is_completed and t.assigned_agent_id == agent_id:
            return i
    return -1

func _on_tick_button_pressed() -> void:
    # 讓時間單純流逝，玩家自己決定要不要派任務，或者讓員工休息
    task_manager.process_tick()
    agent_manager.process_tick()
    
    # 隨機產生新任務 (簡易版 SALES 邏輯)
    if randf() < 0.2:
        _spawn_task_in_backlog("Random Client Req", randi()%3 + 2, (randi()%3 + 1)*100)
        
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
        text += "任務: [無]"
        
    status_label.text = text
