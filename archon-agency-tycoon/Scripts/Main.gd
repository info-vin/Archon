extends Node

var agent_views = {}
const AgentRouterClass = preload("res://Scripts/Logic/AgentRouter.gd")
var agent_router = AgentRouterClass.new()

@onready var minimap_container: Control = $UILayer/UI/RightPanel/VBox/MinimapContainer
@onready var office_grid: Node2D = $World/Rooms
@onready var ticker: RichTextLabel = $UILayer/UI/TopBar/HBox/TickerLabel
@onready var dev_room_label: Label = $World/Rooms/DevRoom/Label
@onready var sales_room_label: Label = $World/Rooms/SalesRoom/Label
@onready var qa_room_label: Label = $World/Rooms/QARoom/Label
@onready var break_room_label: Label = $World/Rooms/BreakRoom/Label

@onready var dev_room: Node2D = $World/Rooms/DevRoom
@onready var sales_room: Node2D = $World/Rooms/SalesRoom
@onready var qa_room: Node2D = $World/Rooms/QARoom
@onready var break_room: Node2D = $World/Rooms/BreakRoom
@onready var lang_button: Button = $UILayer/UI/TopBar/HBox/LangButton
@onready var jukebox_button: Button = $UILayer/UI/TopBar/HBox/JukeboxButton
@onready var task_container: HBoxContainer = $UILayer/UI/BottomBar/VBox/TaskContainer

var hud_controller: Node
var config: Resource
var current_lang_index = 0
var langs = ["zh_TW", "en", "ja"]
var lang_names = ["中文", "English", "日本語"]

var instant_positioning: bool = false
var help_menu_instance = null

func _ready() -> void:
	config = load("res://GameConfig.tres")
	
	hud_controller = preload("res://Scripts/UI/HUDController.gd").new()
	hud_controller.initialize(self)
	
	minimap_container.set_script(preload("res://Scripts/UI/Minimap.gd"))
	var drop_script = preload("res://Scripts/UI/DevRoomDropZone.gd")
	if drop_script:
		dev_room.set_script(drop_script)
		sales_room.set_script(drop_script)
		qa_room.set_script(drop_script)
		break_room.set_script(drop_script)
	
	var t_mgr = get_node("/root/SimulationEngine").tycoon_manager
	dev_room.setup_room("DevRoom", Color("#39ff14"), t_mgr)
	sales_room.setup_room("SalesRoom", Color("#fde910"), t_mgr)
	qa_room.setup_room("QARoom", Color("#ff003c"), t_mgr)
	break_room.setup_room("BreakRoom", Color("#b026ff"), t_mgr)
	
	get_node("/root/EventBus").tick_updated.connect(_on_tick_updated)
	get_node("/root/EventBus").agent_spawned.connect(_on_agent_spawned)
	get_node("/root/EventBus").task_generated.connect(_on_task_generated)
	
	# Sync existing agents for tests and initial startup
	var sim_engine = get_node_or_null("/root/SimulationEngine")
	if sim_engine and sim_engine.agent_manager:
		for agent_id in range(sim_engine.agent_manager.agents.size()):
			var agent = sim_engine.agent_manager.get_agent(agent_id)
			var target_room = dev_room
			if agent.role == 0: target_room = sales_room
			elif agent.role == 2: target_room = qa_room
			_spawn_agent_view(agent_id, target_room)
			
	if sim_engine and sim_engine.task_manager:
		for task_id in range(sim_engine.task_manager.tasks.size()):
			var task = sim_engine.task_manager.tasks[task_id]
			if not task.is_completed and task.assigned_agent_id == -1:
				var task_card = preload("res://Scenes/UI/TaskCard.tscn").instantiate()
				task_container.add_child(task_card)
				task_card.setup(task_id, task.task_name, task.required_ticks, task.reward_funds)
				
	if sim_engine:
		_update_ui()
	
	if jukebox_button:
		jukebox_button.pressed.connect(_on_jukebox_pressed)
	var recruit_btn = $UILayer/UI/BottomBar/VBox/ActionHBox/RecruitBtn
	if recruit_btn:
		recruit_btn.pressed.connect(_on_recruit_btn_pressed)
	var expand_btn = $UILayer/UI/BottomBar/VBox/ActionHBox/ExpandRoomBtn
	if expand_btn:
		expand_btn.pressed.connect(_on_expand_room_pressed)
	var save_btn = $UILayer/UI/BottomBar/VBox/ActionHBox/SaveBtn
	if save_btn:
		save_btn.pressed.connect(_on_save_btn_pressed)
	if lang_button:
		lang_button.pressed.connect(_on_lang_button_pressed)
		
	# Let layout cycles complete
	await get_tree().process_frame
	_update_ui()
	_update_minimap()

func _on_tick_updated(tick_count: int, funds: int, rep: int) -> void:
	hud_controller.update_ticker(tick_count, funds, rep)
	_update_ui()

func _on_agent_spawned(agent_id: int, room_name: String) -> void:
	var target_room = dev_room
	if room_name == "sales": target_room = sales_room
	elif room_name == "qa": target_room = qa_room
	_spawn_agent_view(agent_id, target_room)

func _update_ui() -> void:
	if agent_router:
		agent_router.reset_counts()
	
	hud_controller.update_static_labels()
	
	var walk_speed = 180.0
	var rooms_dict = {"dev": dev_room, "sales": sales_room, "qa": qa_room, "break": break_room}
	
	for agent_id in agent_views.keys():
		var agent = get_node("/root/SimulationEngine").agent_manager.get_agent(agent_id)
		var view = agent_views[agent_id]
		if not agent or not view: continue
			
		var target_info = agent_router.calculate_route(agent, rooms_dict)
		if target_info.room:
			view.walk_to(agent, target_info.room, target_info.pos, instant_positioning, walk_speed)

	_update_minimap()

func _update_minimap() -> void:
	if minimap_container and minimap_container.has_method("update_minimap"):
		minimap_container.update_minimap(office_grid, get_node("/root/SimulationEngine").agent_manager, agent_views)

func _spawn_agent_view(agent_id: int, room: Node2D) -> void:
	var agent_view_scene = preload("res://Scenes/Main/ModularAgent.tscn")
	var agent = get_node("/root/SimulationEngine").agent_manager.get_agent(agent_id)
	if agent_view_scene and agent:
		var agent_view = agent_view_scene.instantiate()
		agent_view.position = Vector2(150, 130)
		agent_view.scale = Vector2(1.0, 1.0)
		agent_view.agent_id = agent_id
		room.add_child(agent_view)
		agent_view.apply_agent_data(agent)
		if not agent_view.is_connected("agent_clicked", _on_agent_clicked):
			agent_view.agent_clicked.connect(_on_agent_clicked)
		agent_views[agent_id] = agent_view

func _on_task_generated(task_id: int, task_name: String, ticks: int, reward: int) -> void:
	var task_card = preload("res://Scenes/UI/TaskCard.tscn").instantiate()
	task_container.add_child(task_card)
	task_card.setup(task_id, task_name, ticks, reward)

func _on_task_dropped_on_agent(task_id: int, dropped_agent_id: int) -> void:
	get_node("/root/SimulationEngine").task_manager.assign_task(task_id, dropped_agent_id)

func _on_agent_clicked(agent_id: int) -> void:
	var agent = get_node("/root/SimulationEngine").agent_manager.get_agent(agent_id)
	if agent:
		_log_event("Clicked on Agent: [color=#39ff14]" + agent.agent_name + "[/color] (" + str(agent.energy) + " Energy, " + str(int(agent.happiness)) + " Happiness)")

func _on_lang_button_pressed() -> void:
	current_lang_index = (current_lang_index + 1) % langs.size()
	TranslationServer.set_locale(langs[current_lang_index])
	lang_button.text = lang_names[current_lang_index]
	_update_ui()

func _on_jukebox_pressed() -> void:
	if has_node("/root/AudioManager"):
		var audio_mgr = get_node("/root/AudioManager")
		var next_track = audio_mgr.cycle_bgm()
		_log_event("Jukebox BGM track changed to: [color=#39ff14]%s[/color]" % next_track.to_upper())

func _on_save_btn_pressed() -> void:
	get_node("/root/SimulationEngine").save_game()
	_log_event("Game Saved Successfully!")

func _unhandled_input(event: InputEvent) -> void:
	if event is InputEventKey and event.pressed:
		if event.keycode == KEY_H:
			hud_controller.toggle_help_menu()

func _on_recruit_btn_pressed() -> void:
	hud_controller.show_recruit_overlay()

func _on_expand_room_pressed() -> void:
	hud_controller.show_expand_room()

func _log_event(msg: String) -> void:
	var event_log = get_node_or_null("UILayer/UI/RightPanel/VBox/EventLog")
	if event_log and event_log is RichTextLabel:
		var time_str = "[color=#888888][%d][/color] " % get_node("/root/SimulationEngine").tick_count
		event_log.append_text("[font_size=12]" + time_str + msg + "[/font_size]\n")
