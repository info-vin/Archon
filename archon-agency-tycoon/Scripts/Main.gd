extends Control

var agent_manager
var task_manager
var tycoon_manager
var agent_views = {}
const AgentRouterClass = preload("res://Scripts/Logic/AgentRouter.gd")
var agent_router = AgentRouterClass.new()

@onready var minimap_container: Control = $VBox/HBoxMain/RightPanel/VBox/MinimapContainer
@onready var office_grid: GridContainer = $VBox/HBoxMain/GameArea/Building/OfficeGrid
@onready var ticker: RichTextLabel = $VBox/TopBar/HBox/TickerLabel
@onready var dev_room_label: Label = $VBox/HBoxMain/GameArea/Building/OfficeGrid/DevRoom/Label
@onready var sales_room_label: Label = $VBox/HBoxMain/GameArea/Building/OfficeGrid/SalesRoom/Label
@onready var qa_room_label: Label = $VBox/HBoxMain/GameArea/Building/OfficeGrid/QARoom/Label
@onready var break_room_label: Label = $VBox/HBoxMain/GameArea/Building/OfficeGrid/BreakRoom/Label

@onready var dev_room: PanelContainer = $VBox/HBoxMain/GameArea/Building/OfficeGrid/DevRoom
@onready var sales_room: PanelContainer = $VBox/HBoxMain/GameArea/Building/OfficeGrid/SalesRoom
@onready var qa_room: PanelContainer = $VBox/HBoxMain/GameArea/Building/OfficeGrid/QARoom
@onready var break_room: PanelContainer = $VBox/HBoxMain/GameArea/Building/OfficeGrid/BreakRoom
@onready var lang_button: Button = $VBox/TopBar/HBox/LangButton
@onready var game_tick_timer: Timer = $GameTickTimer
@onready var task_container: HBoxContainer = $VBox/BottomBar/VBox/TaskContainer

# L2 Controller Modules
var hud_controller: Node
var lifecycle: Node
var config: Resource

var current_lang_index = 0
var langs = ["zh_TW", "en", "ja"]
var lang_names = ["中文", "English", "日本語"]
var tick_count: int = 0
var room_agent_counts = {"dev": 0, "sales": 0, "qa": 0, "break": 0}

var instant_positioning: bool = false
var help_menu_instance = null

func _ready() -> void:
	# Load centralized config
	config = load("res://GameConfig.tres")
	
	# Initialize L2 modules
	hud_controller = HUDController.new()
	hud_controller.initialize(self)
	lifecycle = preload("res://Scripts/Logic/GameLifecycle.gd").new()
	lifecycle.initialize(self)
	
	# Instantiate Managers
	agent_manager = preload("res://Scripts/Logic/AgentManager.gd").new()
	task_manager = preload("res://Scripts/Logic/TaskManager.gd").new()
	tycoon_manager = preload("res://Scripts/Logic/TycoonManager.gd").new()
	
	# Setup UI scripts
	minimap_container.set_script(preload("res://Scripts/UI/Minimap.gd"))
	dev_room.set_script(preload("res://Scripts/UI/OfficeRoom.gd"))
	sales_room.set_script(preload("res://Scripts/UI/OfficeRoom.gd"))
	qa_room.set_script(preload("res://Scripts/UI/OfficeRoom.gd"))
	break_room.set_script(preload("res://Scripts/UI/OfficeRoom.gd"))
	dev_room.setup_room("DevRoom", Color("#39ff14"), tycoon_manager)
	sales_room.setup_room("SalesRoom", Color("#fde910"), tycoon_manager)
	qa_room.setup_room("QARoom", Color("#ff003c"), tycoon_manager)
	break_room.setup_room("BreakRoom", Color("#b026ff"), tycoon_manager)
	
	# Setup initial game if no save
	if not FileAccess.file_exists("user://savegame.save"):
		_setup_initial_game()
	else:
		_load_game()

	game_tick_timer.timeout.connect(_on_tick_timer_timeout)

func _load_game() -> void:
	var loaded = await tycoon_manager.load_game(agent_manager, task_manager)
	if loaded:
		lifecycle.setup_loaded_game(agent_manager, task_manager)
	else:
		_setup_initial_game()
func _setup_initial_game() -> void:
	# Recruit initial staff (Alice DEV, Bob SALES, Charlie QA)
	var AgentResource = preload("res://Scripts/Resources/AgentResource.gd")
	# Init params: name, role, code, charisma, debug, luck, hair, outfit, tool
	var alice = AgentResource.new("Alice", AgentResource.AgentRole.DEV, 10, 5, 5, 5)
	var bob = AgentResource.new("Bob", AgentResource.AgentRole.SALES, 5, 10, 5, 5)
	var charlie = AgentResource.new("Charlie", AgentResource.AgentRole.QA, 5, 5, 10, 5)

	for agent in [alice, bob, charlie]:
		var id = agent_manager.add_agent(agent)
		var target_room = dev_room
		if agent.role == AgentResource.AgentRole.SALES: target_room = sales_room
		elif agent.role == AgentResource.AgentRole.QA: target_room = qa_room
		_spawn_agent_view(id, target_room)
	_update_ui()

func _update_ui() -> void:
	room_agent_counts = {"dev": 0, "sales": 0, "qa": 0, "break": 0}
	
	# Update HUD Labels
	hud_controller.update_static_labels()
	hud_controller.update_ticker(tick_count, tycoon_manager.funds, tycoon_manager.reputation)
	
	# Update Agent Positions
	var walk_speed = 180.0
	var rooms_dict = {"dev": dev_room, "sales": sales_room, "qa": qa_room, "break": break_room}
	
	for agent_id in agent_views.keys():
		var agent = agent_manager.get_agent(agent_id)
		var view = agent_views[agent_id]
		if not agent or not view: continue
			
		var target_info = agent_router.calculate_route(agent, rooms_dict)
		if target_info.room:
			view.walk_to(agent, target_info.room, target_info.pos, instant_positioning, walk_speed)

	_update_minimap()

func _update_minimap() -> void:
	if minimap_container and minimap_container.has_method("update_minimap"):
		minimap_container.update_minimap(office_grid, agent_manager, agent_views)

func _spawn_agent_view(agent_id: int, room: Control) -> void:
	var agent_view_scene = preload("res://Scenes/Main/ModularAgent.tscn")
	if agent_view_scene:
		var agent_view = agent_view_scene.instantiate()
		agent_view.position = Vector2(150, 130) # Center
		agent_view.scale = Vector2(1.0, 1.0) # Reset scale to 1.0 for true pixel size
		room.add_child(agent_view)
		agent_views[agent_id] = agent_view

func _spawn_task_in_backlog(t_name: String, ticks: int, reward: int, req_role: int = 1) -> void:
	var task = preload("res://Scripts/Resources/TaskResource.gd").new(t_name, req_role, ticks, reward)
	task_container.add_child(task.to_node())

func _on_task_dropped_on_agent(task_id: int, dropped_agent_id: int) -> void:
	task_manager.assign_task(task_id, dropped_agent_id)

func _on_tick_timer_timeout() -> void:
	tick_count += 1
	tycoon_manager.process_tick(agent_manager, task_manager)
	_update_ui()

func _on_lang_button_pressed() -> void:
	current_lang_index = (current_lang_index + 1) % langs.size()
	TranslationServer.set_locale(langs[current_lang_index])
	lang_button.text = lang_names[current_lang_index]
	_update_ui()

func _on_save_btn_pressed() -> void:
	tycoon_manager.save_game(agent_manager, task_manager)
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
	var event_log = get_node_or_null("VBox/HBoxMain/RightPanel/VBox/EventLog")
	if event_log and event_log is RichTextLabel:
		var time_str = "[color=#888888][%d][/color] " % tick_count
		event_log.append_text("[font_size=12]" + time_str + msg + "[/font_size]\n")
