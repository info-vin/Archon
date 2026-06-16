extends Control

var agent_manager
var task_manager
var tycoon_manager
var agent_views = {}

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

var dev_desks = [
	Vector2(65, 230),
	Vector2(180, 120),
	Vector2(280, 130),
	Vector2(280, 240)
]
var sales_desks = [
	Vector2(110, 130),
	Vector2(250, 120),
	Vector2(180, 230),
	Vector2(290, 220)
]
var qa_desks = [
	Vector2(140 + 32, 40 + 32),
	Vector2(200, 150)
]
var break_desks = [
	Vector2(120 + 32, 80 + 32),
	Vector2(80, 150),
	Vector2(220, 150)
]

var instant_positioning: bool = false

func _ready() -> void:
	# Load centralized config
	config = load("res://GameConfig.tres")
	
	# Instantiate Managers
	agent_manager = preload("res://Scripts/Logic/AgentManager.gd").new()
	task_manager = preload("res://Scripts/Logic/TaskManager.gd").new()
	tycoon_manager = preload("res://Scripts/Logic/TycoonManager.gd").new()
	
	agent_manager.set_config(config)
	task_manager.set_config(config)
	tycoon_manager.set_config(config)
	
	task_manager.set_agent_manager(agent_manager)
	tycoon_manager.setup_connections(task_manager)
	
	# Connect submodules
	hud_controller = preload("res://Scripts/UI/HUDController.gd").new()
	hud_controller.initialize(self)
	add_child(hud_controller)
	
	lifecycle = preload("res://Scripts/Logic/GameLifecycle.gd").new()
	lifecycle.initialize(self)
	add_child(lifecycle)
	
	# Setup scripts for Minimap
	minimap_container.set_script(preload("res://Scripts/UI/Minimap.gd"))
	
	# Attach OfficeRoom script to rooms that don't have custom drop scripts attached yet
	# (Note: DevRoom and SalesRoom drop zones inherit from OfficeRoom and are set up in lifecycle)
	qa_room.set_script(preload("res://Scripts/UI/OfficeRoom.gd"))
	break_room.set_script(preload("res://Scripts/UI/OfficeRoom.gd"))
	
	qa_room.setup_room("QARoom", Color("#ff003c"), tycoon_manager)
	break_room.setup_room("BreakRoom", Color("#b026ff"), tycoon_manager)
	
	# Logger mappings
	tycoon_manager.crisis_spawned.connect(func(room_name): _log_event("[color=#ff003c]Crisis spawned in %s![/color]" % room_name))
	tycoon_manager.crisis_resolved.connect(func(room_name): _log_event("[color=#39ff14]Crisis resolved in %s![/color]" % room_name))
	tycoon_manager.crisis_spread.connect(func(from_r, to_r): _log_event("[color=#ff003c]Crisis spread from %s to %s![/color]" % [from_r, to_r]))
	task_manager.task_completed.connect(func(t_id, reward): _log_event("[color=#39ff14]Task completed! +$%d[/color]" % reward))
	task_manager.rush_failed.connect(func(t_id, a_id): _log_event("[color=#ff003c]Task rush failed![/color]"))
	
	# Initialize SaveSystem progress
	var token = ""
	if OS.has_feature("web"):
		token = str(JavaScriptBridge.eval("window.getArchonToken ? window.getArchonToken() : ''"))
		
	var save_adapter
	if not token.is_empty():
		save_adapter = preload("res://Scripts/Logic/SaveSystems/SupabaseSaveAdapter.gd").new()
	else:
		save_adapter = preload("res://Scripts/Logic/SaveSystems/LocalSaveAdapter.gd").new()
		
	tycoon_manager.set_save_adapter(save_adapter)
	var loaded = await tycoon_manager.load_game(agent_manager, task_manager)
	
	# Default locale
	TranslationServer.set_locale(langs[current_lang_index])
	
	if lang_button: lang_button.pressed.connect(_on_lang_button_pressed)
	
	var recruit_btn = get_node_or_null("VBox/BottomBar/VBox/ActionHBox/RecruitBtn")
	if recruit_btn: recruit_btn.pressed.connect(_on_recruit_btn_pressed)
	
	var save_btn = get_node_or_null("VBox/BottomBar/VBox/ActionHBox/SaveBtn")
	if save_btn: save_btn.pressed.connect(_on_save_btn_pressed)
		
	var expand_btn = get_node_or_null("VBox/BottomBar/VBox/ActionHBox/ExpandRoomBtn")
	if expand_btn: expand_btn.pressed.connect(_on_expand_room_pressed)
		
	if game_tick_timer: game_tick_timer.timeout.connect(_on_tick_timer_timeout)
		
	if not loaded:
		lifecycle.setup_initial_game(agent_manager)
	else:
		lifecycle.setup_loaded_game(agent_manager, task_manager)
		
	_update_ui()
	hud_controller.update_static_labels()
	
	await get_tree().process_frame
	await get_tree().process_frame
	_update_minimap()

func _on_lang_button_pressed() -> void:
	current_lang_index = (current_lang_index + 1) % langs.size()
	TranslationServer.set_locale(langs[current_lang_index])
	
	hud_controller.update_static_labels()
	
	# Re-setup styles for rooms dynamically
	dev_room.setup_room("DevRoom", Color("#39ff14"), tycoon_manager)
	sales_room.setup_room("SalesRoom", Color("#fde910"), tycoon_manager)
	qa_room.setup_room("QARoom", Color("#ff003c"), tycoon_manager)
	break_room.setup_room("BreakRoom", Color("#b026ff"), tycoon_manager)
	
	_update_ui()
	
	for child in task_container.get_children():
		if child is TaskCard:
			child._update_text()

func _on_save_btn_pressed() -> void:
	_log_event("[color=#00ffff]Saving game...[/color]")
	var result = await tycoon_manager.save_game(agent_manager, task_manager)
	if result:
		_log_event("[color=#39ff14]Game Saved Successfully![/color]")
	else:
		_log_event("[color=#ff003c]Save Failed![/color]")

func _spawn_agent_view(agent_id: int, room: Control) -> void:
	var agent_view_scene = preload("res://Scenes/Main/ModularAgent.tscn")
	if agent_view_scene:
		var agent_view = agent_view_scene.instantiate()
		agent_view.position = Vector2(150, 130) # Center
		agent_view.scale = Vector2(0.2, 0.2) # Scale down to fit rooms
		room.add_child(agent_view)
		agent_views[agent_id] = agent_view

func _spawn_task_in_backlog(t_name: String, ticks: int, reward: int, req_role: int = 1) -> void:
	var task = preload("res://Scripts/Resources/TaskResource.gd").new(t_name, req_role, ticks, reward)
	var task_id = task_manager.add_task(task)

	var card_scene = preload("res://Scenes/UI/TaskCard.tscn")
	if card_scene and task_container:
		var card = card_scene.instantiate()
		task_container.add_child(card)
		card.setup(task_id, t_name, ticks, reward)

func _on_task_dropped_on_agent(task_id: int, dropped_agent_id: int) -> void:
	var task = task_manager.tasks[task_id]
	var target_agent = -1

	if task.required_role == 1: target_agent = 0 # DEV -> Alice
	elif task.required_role == 0: target_agent = 1 # SALES -> Bob
	elif task.required_role == 2: target_agent = 2 # QA -> Charlie

	if target_agent != -1:
		var success = task_manager.assign_task(task_id, target_agent)
		if success:
			if task.required_role != 0:
				for child in task_container.get_children():
					if child is TaskCard and child.task_id == task_id:
						child.queue_free()
						break
			_update_ui()
		else:
			print("無法指派！(可能體力不足或非閒置狀態)")
	else:
		print("未知的任務角色需求")

func _on_tick_timer_timeout() -> void:
	tick_count += 1
	task_manager.process_tick()
	agent_manager.process_tick()
	_update_ui()

func _update_ui() -> void:
	# Update Agent Status List
	var status_list = get_node_or_null("VBox/HBoxMain/RightPanel/VBox/AgentStatusList")
	if status_list:
		for child in status_list.get_children():
			child.queue_free()
		for i in range(agent_manager.agents.size()):
			var agent = agent_manager.agents[i]
			var state_str = "IDLE"
			var state_color = "#888888"
			match agent.state:
				1:
					state_str = "WORKING"
					state_color = "#39ff14"
				2:
					state_str = "RESTING"
					state_color = "#b026ff"
				3:
					state_str = "EXHAUSTED"
					state_color = "#ff003c"
			var lbl = RichTextLabel.new()
			lbl.bbcode_enabled = true
			lbl.text = "[font_size=12][color=#ffffff]%s[/color] - [color=%s]%s[/color] (E:%d)[/font_size]" % [agent.agent_name, state_color, state_str, agent.energy]
			lbl.fit_content = true
			status_list.add_child(lbl)

	if hud_controller:
		hud_controller.update_ticker(tick_count, tycoon_manager.funds, tycoon_manager.reputation)
	
	# Update character positions and animations based on their state
	var room_agent_counts = {
		"dev": 0,
		"sales": 0,
		"qa": 0,
		"break": 0
	}
	
	var walk_speed = 180.0
	var door_pos = Vector2(180, 300)
	
	for agent_id in agent_views.keys():
		var agent = agent_manager.get_agent(agent_id)
		var view = agent_views[agent_id]
		if not agent or not view: continue
			
		var target_room = null
		var target_pos = Vector2(150, 130) # Default Center
		
		match agent.state:
			1: # WORKING
				if agent.role == 1: # DEV
					target_room = dev_room
					var slot = room_agent_counts["dev"]
					target_pos = dev_desks[slot % dev_desks.size()]
					room_agent_counts["dev"] = slot + 1
				elif agent.role == 0: # SALES
					target_room = sales_room
					var slot = room_agent_counts["sales"]
					target_pos = sales_desks[slot % sales_desks.size()]
					room_agent_counts["sales"] = slot + 1
				elif agent.role == 2: # QA
					target_room = qa_room
					var slot = room_agent_counts["qa"]
					target_pos = qa_desks[slot % qa_desks.size()]
					room_agent_counts["qa"] = slot + 1
			2: # RESTING
				target_room = break_room
				var slot = room_agent_counts["break"]
				target_pos = break_desks[slot % break_desks.size()]
				room_agent_counts["break"] = slot + 1
			_: # IDLE / EXHAUSTED
				if agent.role == 1:
					target_room = dev_room
					target_pos = Vector2(180, 280)
				elif agent.role == 0:
					target_room = sales_room
					target_pos = Vector2(180, 280)
				elif agent.role == 2:
					target_room = qa_room
					target_pos = Vector2(180, 280)
				
		if target_room:
			var old_parent = view.get_parent()
			
			if instant_positioning:
				if old_parent != target_room:
					if is_instance_valid(view) and is_instance_valid(old_parent) and is_instance_valid(target_room):
						old_parent.remove_child(view)
						target_room.add_child(view)
				view.position = target_pos
				view.apply_agent_data(agent)
			else:
				# Kill any running walk tween for this view to avoid conflicts
				if view.has_meta("walk_tween"):
					var old_tween = view.get_meta("walk_tween")
					if old_tween and old_tween.is_valid():
						old_tween.kill()
				
				if old_parent != target_room:
					# Walk to current room's door, then switch room, then walk to desk
					view.play_walk_animation(agent)
					
					var dist1 = view.position.distance_to(door_pos)
					var time1 = dist1 / walk_speed if dist1 > 0 else 0.05
					
					var walk_tween = create_tween()
					view.set_meta("walk_tween", walk_tween)
					
					walk_tween.tween_property(view, "position", door_pos, time1)
					walk_tween.tween_callback(func():
						if is_instance_valid(view) and is_instance_valid(old_parent) and is_instance_valid(target_room):
							if view.get_parent() == old_parent:
								old_parent.remove_child(view)
								target_room.add_child(view)
							view.position = door_pos
					)
					var dist2 = door_pos.distance_to(target_pos)
					var time2 = dist2 / walk_speed if dist2 > 0 else 0.05
					walk_tween.tween_property(view, "position", target_pos, time2)
					walk_tween.tween_callback(func():
						if is_instance_valid(view):
							view.apply_agent_data(agent)
					)
				else:
					# Within same room, walk if distance is far, otherwise snap
					var dist = view.position.distance_to(target_pos)
					if dist > 10:
						view.play_walk_animation(agent)
						var time = dist / walk_speed
						var walk_tween = create_tween()
						view.set_meta("walk_tween", walk_tween)
						walk_tween.tween_property(view, "position", target_pos, time)
						walk_tween.tween_callback(func():
							if is_instance_valid(view):
								view.apply_agent_data(agent)
						)
					else:
						view.position = target_pos
						view.apply_agent_data(agent)
	_update_minimap()

func _update_minimap() -> void:
	if minimap_container and minimap_container.has_method("update_minimap"):
		minimap_container.update_minimap(office_grid, agent_manager, agent_views)

var help_menu_instance = null

func _unhandled_input(event: InputEvent) -> void:
	if event is InputEventKey and event.pressed:
		if event.keycode == KEY_H:
			_toggle_help_menu()

func _toggle_help_menu() -> void:
	if help_menu_instance and is_instance_valid(help_menu_instance):
		help_menu_instance.close()
	else:
		var scene = load("res://Scenes/UI/HelpMenu.tscn")
		if scene:
			help_menu_instance = scene.instantiate()
			add_child(help_menu_instance)
			help_menu_instance.closed.connect(func(): help_menu_instance = null)
			help_menu_instance.get_node("VBox/Title").text = tr("UI_HELP_TITLE")
			help_menu_instance.get_node("VBox/Scroll/Content/GoalLabel").text = tr("HELP_GOAL")
			help_menu_instance.get_node("VBox/Scroll/Content/ControlsLabel").text = tr("HELP_CONTROLS")
			help_menu_instance.get_node("VBox/Scroll/Content/TipsLabel").text = tr("HELP_TIPS")
			help_menu_instance.get_node("VBox/CloseButton").text = tr("UI_CLOSE")

func _on_recruit_btn_pressed() -> void:
	var recruit_cost = config.recruit_cost if config else 500
	if tycoon_manager.funds < recruit_cost:
		print("Insufficient funds to recruit!")
		return
		
	var overlay = ColorRect.new()
	overlay.color = Color(0, 0, 0, 0.7)
	overlay.set_anchors_preset(Control.PRESET_FULL_RECT)
	add_child(overlay)
	
	var creator_scene = load("res://Scenes/UI/CharacterCreator.tscn")
	if creator_scene:
		var creator = creator_scene.instantiate()
		creator.scale = Vector2.ZERO
		creator.pivot_offset = Vector2(380, 250)
		var tween = create_tween()
		tween.tween_property(creator, "scale", Vector2.ONE, 0.3).set_trans(Tween.TRANS_BACK).set_ease(Tween.EASE_OUT)
		
		add_child(creator)
		creator.set_config(config)
		
		creator.character_created.connect(func(agent_data):
			tycoon_manager.funds -= recruit_cost
			var new_id = agent_manager.add_agent(agent_data)
			var target_room = dev_room
			if agent_data.role == 0: target_room = sales_room
			elif agent_data.role == 2: target_room = qa_room
			
			_spawn_agent_view(new_id, target_room)
			_update_ui()
			overlay.queue_free()
		)
		
		creator.closed.connect(func():
			overlay.queue_free()
		)

func _on_expand_room_pressed() -> void:
	var expand_cost = config.expand_cost if config else 500
	if tycoon_manager.funds >= expand_cost:
		tycoon_manager.funds -= expand_cost
		var office_grid = get_node_or_null("VBox/GameArea/Building/OfficeGrid")
		if office_grid:
			var new_room = PanelContainer.new()
			new_room.custom_minimum_size = Vector2(360, 390)
			
			var bg_tex = TextureRect.new()
			bg_tex.texture = preload("res://Assets/Rooms/qa_room_bg.png")
			bg_tex.expand_mode = TextureRect.EXPAND_IGNORE_SIZE
			bg_tex.stretch_mode = TextureRect.STRETCH_KEEP_ASPECT_CENTERED
			bg_tex.set_anchors_preset(Control.PRESET_FULL_RECT)
			new_room.add_child(bg_tex)
			
			var lbl = Label.new()
			lbl.text = tr("ROOM_QA") + " (Expansion)"
			new_room.add_child(lbl)
			
			new_room.set_script(preload("res://Scripts/UI/OfficeRoom.gd"))
			office_grid.add_child(new_room)
			new_room.setup_room("QARoom", Color("#ff003c"), tycoon_manager)
		_update_ui()
	else:
		print("不夠資金擴建房間！")

func _log_event(msg: String) -> void:
	var event_log = get_node_or_null("VBox/HBoxMain/RightPanel/VBox/EventLog")
	if event_log and event_log is RichTextLabel:
		var time_str = "[color=#888888][%d][/color] " % tick_count
		event_log.append_text("[font_size=12]" + time_str + msg + "[/font_size]\n")
