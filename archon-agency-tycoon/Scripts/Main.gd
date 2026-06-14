extends Control

var agent_manager
var task_manager
var tycoon_manager

@onready var funds_label: Label = $VBox/TopBar/HBox/FundsValue
@onready var funds_title: Label = $VBox/TopBar/HBox/FundsLabel
@onready var rep_title: Label = $VBox/TopBar/HBox/RepLabel
@onready var backlog_title: Label = $VBox/BottomBar/VBox/Label
@onready var dev_room_label: Label = $VBox/GameArea/Building/Floor1/DevRoom/Label
@onready var sales_room_label: Label = $VBox/GameArea/Building/Floor1/SalesRoom/Label
@onready var qa_room_label: Label = $VBox/GameArea/Building/Floor2/QARoom/Label
@onready var break_room_label: Label = $VBox/GameArea/Building/Floor2/BreakRoom/Label

@onready var dev_room: Control = $VBox/GameArea/Building/Floor1/DevRoom
@onready var sales_room: Control = $VBox/GameArea/Building/Floor1/SalesRoom
@onready var qa_room: Control = $VBox/GameArea/Building/Floor2/QARoom
@onready var lang_button: Button = $VBox/TopBar/HBox/LangButton
@onready var game_tick_timer: Timer = $GameTickTimer
@onready var task_container: HBoxContainer = $VBox/BottomBar/VBox/TaskContainer

var current_lang_index = 0
var langs = ["zh_TW", "en", "ja"]
var lang_names = ["中文", "English", "日本語"]

func _ready() -> void:
    agent_manager = preload("res://Scripts/Logic/AgentManager.gd").new()
    task_manager = preload("res://Scripts/Logic/TaskManager.gd").new()
    tycoon_manager = preload("res://Scripts/Logic/TycoonManager.gd").new()
    
    task_manager.set_agent_manager(agent_manager)
    tycoon_manager.setup_connections(task_manager)
    
    # 預設語言
    TranslationServer.set_locale(langs[current_lang_index])
    
    if lang_button:
        lang_button.pressed.connect(_on_lang_button_pressed)
        
    if game_tick_timer:
        game_tick_timer.timeout.connect(_on_tick_timer_timeout)
        
    _setup_initial_game()
    _update_ui()
    _update_static_labels()

func _on_lang_button_pressed() -> void:
    current_lang_index = (current_lang_index + 1) % langs.size()
    TranslationServer.set_locale(langs[current_lang_index])
    lang_button.text = "Language: " + lang_names[current_lang_index]
    _update_static_labels()
    _update_ui()
    
    # 更新現有卡片的語言
    for child in task_container.get_children():
        if child is TaskCard:
            child._update_text()

func _update_static_labels() -> void:
    funds_title.text = tr("UI_FUNDS")
    rep_title.text = tr("UI_REP")
    backlog_title.text = tr("UI_BACKLOG")
    dev_room_label.text = tr("ROOM_DEV")
    sales_room_label.text = tr("ROOM_SALES")
    qa_room_label.text = tr("ROOM_QA")
    break_room_label.text = tr("ROOM_BREAK")

func _setup_initial_game() -> void:
    # 招募三位核心員工
    var alice = preload("res://Scripts/Resources/AgentResource.gd").new("Alice", 1) # DEV
    var bob = preload("res://Scripts/Resources/AgentResource.gd").new("Bob", 0)     # SALES
    var charlie = preload("res://Scripts/Resources/AgentResource.gd").new("Charlie", 2) # QA
    
    agent_manager.add_agent(alice)
    agent_manager.add_agent(bob)
    agent_manager.add_agent(charlie)
    
    # 紙娃娃實體化 Helper
    _spawn_agent_view(dev_room, "Alice (DEV)")
    _spawn_agent_view(sales_room, "Bob (SALES)")
    _spawn_agent_view(qa_room, "Charlie (QA)")
        
    # 掛載 Drop Zone
    var drop_script = preload("res://Scripts/UI/DevRoomDropZone.gd")
    if drop_script:
        dev_room.set_script(drop_script)
        # Note: We can expand this to other rooms later

func _spawn_agent_view(room: Control, label_text: String) -> void:
    var agent_view_scene = preload("res://Scenes/Main/ModularAgent.tscn")
    if agent_view_scene:
        var agent_view = agent_view_scene.instantiate()
        agent_view.position = Vector2(150, 130) # 置中
        agent_view.scale = Vector2(0.2, 0.2) # 大幅縮小以符合框格
        room.add_child(agent_view)

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
        print("無法指派！")

func _get_active_task_for_agent(agent_id: int) -> int:
    for i in range(task_manager.tasks.size()):
        var t = task_manager.tasks[i]
        if not t.is_completed and t.assigned_agent_id == agent_id:
            return i
    return -1

func _on_tick_timer_timeout() -> void:
    # 真實時間流逝 (1 Tick)
    task_manager.process_tick()
    agent_manager.process_tick()
    _update_ui()

func _update_ui() -> void:
    funds_label.text = "$%d" % tycoon_manager.funds
    
    _update_agent_status_label(dev_room, 0, "Alice")
    _update_agent_status_label(sales_room, 1, "Bob")
    _update_agent_status_label(qa_room, 2, "Charlie")

func _update_agent_status_label(room: Control, agent_id: int, agent_name: String) -> void:
    var status_label = room.get_node_or_null("AgentStatus")
    if not status_label:
        status_label = Label.new()
        status_label.name = "AgentStatus"
        status_label.position = Vector2(10, 30)
        status_label.add_theme_color_override("font_color", Color(1, 1, 1))
        room.add_child(status_label)
        
    var agent = agent_manager.get_agent(agent_id)
    var active_task_idx = _get_active_task_for_agent(agent_id)
    
    var state_str = tr("STATE_IDLE")
    if agent.state == 1: state_str = tr("STATE_WORKING")
    elif agent.state == 2: state_str = tr("STATE_RESTING")
    elif agent.state == 3: state_str = "EXHAUSTED"
    
    var text = "%s: %s\nEnergy: %d/100\n" % [agent_name, state_str, agent.energy]
    
    if active_task_idx != -1:
        var task = task_manager.tasks[active_task_idx]
        text += "[%s]: %d / %d %s" % [task.task_name, task.current_progress, task.required_ticks, tr("UI_TICK")]
    else:
        text += "[None]"
        
    status_label.text = text
