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

@onready var dev_room: Control = $VBox/HBoxMain/GameArea/Building/OfficeGrid/DevRoom
@onready var sales_room: Control = $VBox/HBoxMain/GameArea/Building/OfficeGrid/SalesRoom
@onready var qa_room: Control = $VBox/HBoxMain/GameArea/Building/OfficeGrid/QARoom
@onready var break_room: Control = $VBox/HBoxMain/GameArea/Building/OfficeGrid/BreakRoom
@onready var lang_button: Button = $VBox/TopBar/HBox/LangButton
@onready var game_tick_timer: Timer = $GameTickTimer
@onready var task_container: HBoxContainer = $VBox/BottomBar/VBox/TaskContainer

var current_lang_index = 0
var langs = ["zh_TW", "en", "ja"]
var lang_names = ["中文", "English", "日本語"]
var tick_count: int = 0

var crisis_tweens = {}

func _ready() -> void:
	agent_manager = preload("res://Scripts/Logic/AgentManager.gd").new()
	task_manager = preload("res://Scripts/Logic/TaskManager.gd").new()
	tycoon_manager = preload("res://Scripts/Logic/TycoonManager.gd").new()
	
	task_manager.set_agent_manager(agent_manager)
	tycoon_manager.setup_connections(task_manager)
	
	tycoon_manager.crisis_spawned.connect(_on_crisis_spawned)
	tycoon_manager.crisis_resolved.connect(_on_crisis_resolved)
	tycoon_manager.crisis_spawned.connect(func(room_name): _log_event("[color=#ff003c]Crisis spawned in %s![/color]" % room_name))
	tycoon_manager.crisis_resolved.connect(func(room_name): _log_event("[color=#39ff14]Crisis resolved in %s![/color]" % room_name))
	tycoon_manager.crisis_spread.connect(func(from_r, to_r): _log_event("[color=#ff003c]Crisis spread from %s to %s![/color]" % [from_r, to_r]))
	task_manager.task_completed.connect(func(t_id, reward): _log_event("[color=#39ff14]Task completed! +$%d[/color]" % reward))
	task_manager.rush_failed.connect(func(t_id, a_id): _log_event("[color=#ff003c]Task rush failed![/color]"))
	
	# 初始化存檔介面並嘗試載入進度 (Initialize SaveAdapter and load)
	var token = ""
	if OS.has_feature("web"):
		token = str(JavaScriptBridge.eval("window.getArchonToken ? window.getArchonToken() : ''"))
		
	var save_adapter
	if not token.is_empty():
		save_adapter = preload("res://Scripts/Logic/SaveSystems/SupabaseSaveAdapter.gd").new()
	else:
		save_adapter = preload("res://Scripts/Logic/SaveSystems/LocalSaveAdapter.gd").new()
		
	tycoon_manager.set_save_adapter(save_adapter)
	await tycoon_manager.load_game()
	
	# 預設語言
	TranslationServer.set_locale(langs[current_lang_index])
	
	if lang_button:
		lang_button.pressed.connect(_on_lang_button_pressed)
		
	var recruit_btn = get_node_or_null("VBox/BottomBar/VBox/ActionHBox/RecruitBtn")
	if recruit_btn:
		recruit_btn.pressed.connect(_on_recruit_btn_pressed)
		
	var expand_btn = get_node_or_null("VBox/BottomBar/VBox/ActionHBox/ExpandRoomBtn")
	if expand_btn:
		expand_btn.pressed.connect(_on_expand_room_pressed)
		
	if game_tick_timer:
		game_tick_timer.timeout.connect(_on_tick_timer_timeout)
		
	_setup_initial_game()
	_update_ui()
	_update_static_labels()
	_setup_room_styles()
	
	await get_tree().process_frame
	await get_tree().process_frame
	_update_minimap()




func _setup_room_styles() -> void:
	var rooms = [
		{"node": dev_room, "label": dev_room_label, "color": Color("#39ff14")},
		{"node": sales_room, "label": sales_room_label, "color": Color("#fde910")},
		{"node": qa_room, "label": qa_room_label, "color": Color("#ff003c")},
		{"node": break_room, "label": break_room_label, "color": Color("#b026ff")}
	]
	
	for data in rooms:
		if data["node"] == null: continue
		var panel: PanelContainer = data["node"]
		var label: Label = data["label"]
		var c: Color = data["color"]
		
		# Colorize the label font
		label.add_theme_color_override("font_color", c)
		
		# Colorize the panel border
		var style = StyleBoxFlat.new()
		style.bg_color = Color(0.0, 0.0, 0.0, 0.5)
		style.border_width_left = 2
		style.border_width_top = 2
		style.border_width_right = 2
		style.border_width_bottom = 2
		style.border_color = c * 1.5 # Overbright for neon glow
		style.corner_radius_top_left = 4
		style.corner_radius_top_right = 4
		style.corner_radius_bottom_right = 4
		style.corner_radius_bottom_left = 4
		
		panel.add_theme_stylebox_override("panel", style)
		panel.set_meta("neon_color", c)

func _on_lang_button_pressed() -> void:
	current_lang_index = (current_lang_index + 1) % langs.size()
	TranslationServer.set_locale(langs[current_lang_index])
	
	_update_static_labels()
	_setup_room_styles()
	_update_ui()
	
	# 更新現有卡片的語言
	for child in task_container.get_children():
		if child is TaskCard:
			child._update_text()

func _update_static_labels() -> void:
	dev_room_label.text = tr("ROOM_DEV")
	sales_room_label.text = tr("ROOM_SALES")
	qa_room_label.text = tr("ROOM_QA")
	break_room_label.text = tr("ROOM_BREAK")
	
	var right_panel_event_log = get_node_or_null("VBox/HBoxMain/RightPanel/VBox/EventLogLabel")
	if right_panel_event_log: right_panel_event_log.text = tr("UI_EVENT_LOG")
	
	var right_panel_agent_status = get_node_or_null("VBox/HBoxMain/RightPanel/VBox/AgentStatusLabel")
	if right_panel_agent_status: right_panel_agent_status.text = tr("UI_AGENT_STATUS")

	var right_panel_minimap = get_node_or_null("VBox/HBoxMain/RightPanel/VBox/MinimapLabel")
	if right_panel_minimap: right_panel_minimap.text = tr("UI_MINIMAP")
	
	var tasks_btn = get_node_or_null("VBox/BottomBar/VBox/ActionHBox/TasksBtn")
	if tasks_btn: tasks_btn.text = tr("UI_BACKLOG")
	
	var recruit_btn = get_node_or_null("VBox/BottomBar/VBox/ActionHBox/RecruitBtn")
	if recruit_btn: recruit_btn.text = tr("UI_CHARACTER_CREATOR")
	
	var expand_btn = get_node_or_null("VBox/BottomBar/VBox/ActionHBox/ExpandRoomBtn")
	if expand_btn: expand_btn.text = tr("UI_EXPAND_ROOM")

func _setup_initial_game() -> void:
	# 招募三位核心員工
	var alice = preload("res://Scripts/Resources/AgentResource.gd").new("Alice", 1) # DEV
	var bob = preload("res://Scripts/Resources/AgentResource.gd").new("Bob", 0)	 # SALES
	var charlie = preload("res://Scripts/Resources/AgentResource.gd").new("Charlie", 2) # QA
	
	agent_manager.add_agent(alice)
	agent_manager.add_agent(bob)
	agent_manager.add_agent(charlie)
	
	# 紙娃娃實體化 Helper
	_spawn_agent_view(0, dev_room)
	_spawn_agent_view(1, sales_room)
	_spawn_agent_view(2, qa_room)
		
	# 掛載 Drop Zone
	var drop_script = preload("res://Scripts/UI/DevRoomDropZone.gd")
	if drop_script:
		dev_room.set_script(drop_script)
		sales_room.set_script(drop_script)

	# 產生幾個初始任務
	_spawn_task_in_backlog("Fix Login Bug", 3, 300, 1) # DEV
	_spawn_task_in_backlog("Update DB Schema", 2, 200, 1) # DEV
	_spawn_task_in_backlog("Start Outreach", 999, 0, 0) # SALES

func _spawn_agent_view(agent_id: int, room: Control) -> void:
	var agent_view_scene = preload("res://Scenes/Main/ModularAgent.tscn")
	if agent_view_scene:
		var agent_view = agent_view_scene.instantiate()
		agent_view.position = Vector2(150, 130) # 置中
		agent_view.scale = Vector2(0.2, 0.2) # 大幅縮小以符合框格
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

func _get_active_task_for_agent(agent_id: int) -> int:
	for i in range(task_manager.tasks.size()):
		var t = task_manager.tasks[i]
		if not t.is_completed and t.assigned_agent_id == agent_id:
			return i
	return -1

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

	if ticker:
		var f_color = "#39ff14" if tycoon_manager.funds > 0 else "#ff003c"
		var r_color = "#39ff14" if tycoon_manager.reputation > 50 else "#ff003c"
		ticker.text = "[color=#888888]ARCHON CORP | TICK:[/color] [color=#ffffff]%d[/color] [color=#888888]| %s:[/color] [color=%s]$%d[/color] [color=#888888]| %s:[/color] [color=%s]%d[/color]" % [
			tick_count, 
			tr("UI_FUNDS"), f_color, tycoon_manager.funds,
			tr("UI_REP"), r_color, tycoon_manager.reputation
		]
	
	# Update character positions and animations based on their state
	for agent_id in agent_views.keys():
		var agent = agent_manager.get_agent(agent_id)
		var view = agent_views[agent_id]
		if not agent or not view:
			continue
			
		var target_room = null
		var target_pos = Vector2(150, 130) # Default Center
		
		match agent.state:
			1: # WORKING
				if agent.role == 1: # DEV
					target_room = dev_room
					target_pos = Vector2(30 + 32, 80 + 32)
				elif agent.role == 0: # SALES
					target_room = sales_room
					target_pos = Vector2(200 + 32, 80 + 32)
				elif agent.role == 2: # QA
					target_room = qa_room
					target_pos = Vector2(140 + 32, 40 + 32)
			2: # RESTING
				target_room = break_room
				target_pos = Vector2(120 + 32, 80 + 32)
			_: # IDLE / EXHAUSTED
				if agent.role == 1: target_room = dev_room
				elif agent.role == 0: target_room = sales_room
				elif agent.role == 2: target_room = qa_room
				
		if target_room and view.get_parent() != target_room:
			view.get_parent().remove_child(view)
			target_room.add_child(view)
			
		view.position = target_pos
		view.apply_agent_data(agent)
	_update_minimap()

func _get_room_by_name(room_name: String) -> Control:
	match room_name:
		"DevRoom": return dev_room
		"SalesRoom": return sales_room
		"QARoom": return qa_room
		"BreakRoom": return break_room
	return null

func _on_crisis_spawned(room_name: String) -> void:
	var room = _get_room_by_name(room_name)
	if room and not crisis_tweens.has(room_name):
		var tween = create_tween().set_loops()
		tween.tween_property(room, "modulate", Color(1, 0.4, 0.4), 0.5)
		tween.tween_property(room, "modulate", Color.WHITE, 0.5)
		crisis_tweens[room_name] = tween

func _on_crisis_resolved(room_name: String) -> void:
	if crisis_tweens.has(room_name):
		var tween = crisis_tweens[room_name]
		if tween and tween.is_valid():
			tween.kill()
		crisis_tweens.erase(room_name)
		
	var room = _get_room_by_name(room_name)
	if room:
		room.modulate = Color.WHITE

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
			
			# Translate it dynamically
			help_menu_instance.get_node("VBox/Title").text = tr("UI_HELP_TITLE")
			help_menu_instance.get_node("VBox/Scroll/Content/GoalLabel").text = tr("HELP_GOAL")
			help_menu_instance.get_node("VBox/Scroll/Content/ControlsLabel").text = tr("HELP_CONTROLS")
			help_menu_instance.get_node("VBox/Scroll/Content/TipsLabel").text = tr("HELP_TIPS")
			help_menu_instance.get_node("VBox/CloseButton").text = tr("UI_CLOSE")

func _on_recruit_btn_pressed() -> void:
	var recruit_cost = 500
	if tycoon_manager.funds < recruit_cost:
		print("Insufficient funds to recruit! Need $500.")
		return
		
	# 1. Create Modal Overlay
	var overlay = ColorRect.new()
	overlay.color = Color(0, 0, 0, 0.7) # Dim background
	overlay.set_anchors_preset(Control.PRESET_FULL_RECT)
	add_child(overlay)
	
	# 2. Instantiate Character Creator
	var creator_scene = load("res://Scenes/UI/CharacterCreator.tscn")
	if creator_scene:
		var creator = creator_scene.instantiate()
		
		# Popup animation
		creator.scale = Vector2.ZERO
		creator.pivot_offset = Vector2(380, 250) # Approximate center
		var tween = create_tween()
		tween.tween_property(creator, "scale", Vector2.ONE, 0.3).set_trans(Tween.TRANS_BACK).set_ease(Tween.EASE_OUT)
		
		add_child(creator)
		
		# 3. Handle Successful Recruitment
		creator.character_created.connect(func(agent_data):
			tycoon_manager.funds -= recruit_cost # Deduct funds
			var new_id = agent_manager.add_agent(agent_data)
			
			# Spawn in correct room based on role
			var target_room = dev_room
			if agent_data.role == 0:
				target_room = sales_room
			elif agent_data.role == 2:
				target_room = qa_room
			
			_spawn_agent_view(new_id, target_room)
			_update_ui()
			overlay.queue_free() # Remove overlay
		)
		
		# 4. Handle Cancellation
		creator.closed.connect(func():
			overlay.queue_free() # Remove overlay without deducting funds
		)

func _on_expand_room_pressed() -> void:
	# Cost 500 to expand/duplicate QA room as a dynamic building proof
	if tycoon_manager.funds >= 500:
		tycoon_manager.funds -= 500
		var office_grid = get_node_or_null("VBox/GameArea/Building/OfficeGrid")
		if office_grid:
			# Instantiate a duplicate QA Room
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
			
			office_grid.add_child(new_room)
		_update_ui()
	else:
		print("不夠資金擴建房間！")



func _log_event(msg: String) -> void:
	var event_log = get_node_or_null("VBox/HBoxMain/RightPanel/VBox/EventLog")
	if event_log and event_log is RichTextLabel:
		var time_str = "[color=#888888][%d][/color] " % tick_count
		event_log.append_text("[font_size=12]" + time_str + msg + "[/font_size]\n")

func _update_minimap() -> void:
	if not minimap_container or not office_grid: return
	
	var minimap_size = minimap_container.size
	if minimap_size.x == 0 or minimap_size.y == 0: return
	
	# Clear old dots
	for child in minimap_container.get_children():
		if child.name != "BG":
			child.queue_free()
			
	var content_x = max(office_grid.size.x, 800.0)
	var content_y = max(office_grid.size.y, 600.0)
	var scale_x = minimap_size.x / content_x
	var scale_y = minimap_size.y / content_y
	var uniform_scale = min(scale_x, scale_y)
	var offset_x = (minimap_size.x - content_x * uniform_scale) / 2.0
	var offset_y = (minimap_size.y - content_y * uniform_scale) / 2.0
	var offset = Vector2(offset_x, offset_y)
	
	# Draw all rooms and hallways
	for room in office_grid.get_children():
		var final_node: Control
		
		# Find if this room has a background texture
		var tex = null
		for c in room.get_children():
			if c is TextureRect:
				tex = c.texture
				break
				
		if tex != null:
			var tex_rect = TextureRect.new()
			tex_rect.texture = tex
			tex_rect.expand_mode = TextureRect.EXPAND_IGNORE_SIZE
			tex_rect.stretch_mode = TextureRect.STRETCH_KEEP_ASPECT_CENTERED
			# Dim the texture a bit to make agents pop
			tex_rect.modulate = Color(0.6, 0.6, 0.6, 1.0)
			final_node = tex_rect
		else:
			var rect = ColorRect.new()
			rect.color = Color(0.15, 0.15, 0.15, 1.0) # Dark gray for hallways
			final_node = rect
			
		final_node.position = offset + room.position * uniform_scale
		final_node.size = room.size * uniform_scale
		minimap_container.add_child(final_node)
		
		# Draw neon border if it's a room
		if room.has_meta("neon_color"):
			var border = ReferenceRect.new()
			border.editor_only = false
			border.border_color = room.get_meta("neon_color")
			border.border_width = 1.0
			border.position = final_node.position
			border.size = final_node.size
			minimap_container.add_child(border)

	# Draw agents
	for agent_id in agent_views.keys():
		var agent = agent_manager.get_agent(agent_id)
		var view = agent_views[agent_id]
		if not agent or not view or not view.get_parent(): continue
		
		var dot = ColorRect.new()
		var color = Color.WHITE
		if agent.role == 1: color = Color("#39ff14")
		elif agent.role == 0: color = Color("#fde910")
		elif agent.role == 2: color = Color("#ff003c")
		
		dot.color = color
		dot.size = Vector2(4, 4)
		
		var room_pos = view.get_parent().position
		var global_pos = room_pos + view.position
		dot.position = offset + global_pos * uniform_scale
		
		minimap_container.add_child(dot)
