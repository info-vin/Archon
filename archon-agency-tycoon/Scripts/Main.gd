extends Control

var agent_manager
var task_manager
var tycoon_manager

@onready var funds_label: Label = $VBox/TopBar/HBox/FundsValue
@onready var dev_room: Control = $VBox/GameArea/Building/Floor1/DevRoom
@onready var tick_button: Button = $VBox/TopBar/HBox/TickButton

func _ready() -> void:
    # 1. 實例化大腦 (Managers)
    agent_manager = preload("res://Scripts/Logic/AgentManager.gd").new()
    task_manager = preload("res://Scripts/Logic/TaskManager.gd").new()
    tycoon_manager = preload("res://Scripts/Logic/TycoonManager.gd").new()
    
    # 2. 接通神經網路
    task_manager.set_agent_manager(agent_manager)
    tycoon_manager.setup_connections(task_manager)
    
    # 3. 綁定「下一回合」按鈕
    if tick_button:
        tick_button.pressed.connect(_on_tick_button_pressed)
        
    # 4. 準備測試資料
    _setup_initial_game()
    _update_ui()

func _setup_initial_game() -> void:
    # 招募一位工程師 Alice
    var agent = preload("res://Scripts/Resources/AgentResource.gd").new("Alice (DEV)", 1)
    var agent_id = agent_manager.add_agent(agent)
    
    # 接到一個需要 3 回合，價值 $300 的修復 Bug 任務
    var task = preload("res://Scripts/Resources/TaskResource.gd").new("Fix Login Bug", 1, 3, 300)
    var task_id = task_manager.add_task(task)
    
    # 老闆強制指派 Alice 去解 Bug
    task_manager.assign_task(task_id, agent_id)
    
    # 把我們辛苦弄好的「紙娃娃」實體化到畫面的 Dev 房間裡！
    var agent_view_scene = preload("res://Scenes/Main/ModularAgent.tscn")
    if agent_view_scene:
        var agent_view = agent_view_scene.instantiate()
        agent_view.position = Vector2(150, 100) # 把她放在房間中間
        # 稍微縮小整個紙娃娃，避免太大隻
        agent_view.scale = Vector2(0.5, 0.5) 
        dev_room.add_child(agent_view)

func _on_tick_button_pressed() -> void:
    # 時間流動！
    task_manager.process_tick()
    agent_manager.process_tick()
    _update_ui()

func _update_ui() -> void:
    # 更新老闆的錢包
    funds_label.text = "$%d" % tycoon_manager.funds
    
    # 顯示 Alice 和任務的狀態文字
    var status_label = dev_room.get_node_or_null("AgentStatus")
    if not status_label:
        status_label = Label.new()
        status_label.name = "AgentStatus"
        status_label.position = Vector2(10, 10)
        status_label.add_theme_color_override("font_color", Color(1, 1, 1))
        dev_room.add_child(status_label)
        
    var alice = agent_manager.get_agent(0)
    var task = task_manager.tasks[0]
    
    var state_str = "IDLE"
    if alice.state == 1: state_str = "WORKING 💦"
    elif alice.state == 2: state_str = "RESTING ☕"
    elif alice.state == 3: state_str = "EXHAUSTED 💀"
    
    var text = "Alice: %s\n體力: %d/100\n" % [state_str, alice.energy]
    if task.is_completed:
        text += "任務: [已完成] 賺入 $%d!" % task.reward_funds
    else:
        text += "任務進度: %d / %d" % [task.current_progress, task.required_ticks]
        
    status_label.text = text
