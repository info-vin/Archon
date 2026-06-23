extends Node
class_name HUDController

var main_node: Node

func initialize(p_main_node: Node) -> void:
	main_node = p_main_node

func update_static_labels() -> void:
	if not main_node: return
	
	if main_node.dev_room_label: main_node.dev_room_label.text = tr("ROOM_DEV")
	if main_node.sales_room_label: main_node.sales_room_label.text = tr("ROOM_SALES")
	if main_node.qa_room_label: main_node.qa_room_label.text = tr("ROOM_QA")
	if main_node.break_room_label: main_node.break_room_label.text = tr("ROOM_BREAK")
	
	var event_log_lbl = main_node.get_node_or_null("VBox/HBoxMain/RightPanel/VBox/EventLogLabel")
	if event_log_lbl: event_log_lbl.text = tr("UI_EVENT_LOG")
	
	var agent_status_lbl = main_node.get_node_or_null("VBox/HBoxMain/RightPanel/VBox/AgentStatusLabel")
	if agent_status_lbl: agent_status_lbl.text = tr("UI_AGENT_STATUS")
	
	var minimap_lbl = main_node.get_node_or_null("VBox/HBoxMain/RightPanel/VBox/MinimapLabel")
	if minimap_lbl: minimap_lbl.text = tr("UI_MINIMAP")
	
	var tasks_btn = main_node.get_node_or_null("VBox/BottomBar/VBox/ActionHBox/TasksBtn")
	if tasks_btn: tasks_btn.text = tr("UI_BACKLOG")
	
	var save_btn = main_node.get_node_or_null("VBox/BottomBar/VBox/ActionHBox/SaveBtn")
	if save_btn: save_btn.text = tr("UI_SAVE")
	
	var recruit_btn = main_node.get_node_or_null("VBox/BottomBar/VBox/ActionHBox/RecruitBtn")
	if recruit_btn: recruit_btn.text = tr("UI_CHARACTER_CREATOR")
	
	var expand_btn = main_node.get_node_or_null("VBox/BottomBar/VBox/ActionHBox/ExpandRoomBtn")
	if expand_btn: expand_btn.text = tr("UI_EXPAND_ROOM")

func show_recruit_overlay() -> void:
	var recruit_cost = main_node.config.recruit_cost if main_node.config else 500
	if main_node.get_node("/root/SimulationEngine").tycoon_manager.funds < recruit_cost:
		print("Insufficient funds to recruit!")
		return
		
	var overlay = ColorRect.new()
	overlay.color = Color(0, 0, 0, 0.7)
	overlay.set_anchors_preset(Control.PRESET_FULL_RECT)
	main_node.add_child(overlay)
	
	var creator_scene = load("res://Scenes/UI/CharacterCreator.tscn")
	if creator_scene:
		var creator = creator_scene.instantiate()
		creator.scale = Vector2.ZERO
		creator.pivot_offset = Vector2(380, 250)
		var tween = main_node.create_tween()
		tween.tween_property(creator, "scale", Vector2.ONE, 0.3).set_trans(Tween.TRANS_BACK).set_ease(Tween.EASE_OUT)
		
		main_node.add_child(creator)
		creator.set_config(main_node.config)
		
		creator.character_created.connect(func(agent_data):
			main_node.get_node("/root/SimulationEngine").recruit_agent(agent_data)
			overlay.queue_free()
		)
		
		creator.closed.connect(func():
			overlay.queue_free()
		)

func show_expand_room() -> void:
	if main_node.get_node("/root/SimulationEngine").expand_room():
		var office_grid = main_node.office_grid
		if office_grid:
			var new_room = Node2D.new()
			# Manually set position to a new grid cell (e.g., column 1, row 2)
			new_room.position = Vector2(0, 900)
			
			var bg_tex = Sprite2D.new()
			bg_tex.texture = preload("res://Assets/Rooms/qa_room_bg.png")
			bg_tex.centered = false
			new_room.add_child(bg_tex)
			
			var lbl = Label.new()
			lbl.name = "Label"
			lbl.text = tr("ROOM_QA") + " (Expansion)"
			new_room.add_child(lbl)
			
			var desk1 = Marker2D.new(); desk1.name = "DeskPoint_1"; desk1.position = Vector2(172, 72); new_room.add_child(desk1)
			var stand1 = Marker2D.new(); stand1.name = "StandPoint_1"; stand1.position = Vector2(100, 250); new_room.add_child(stand1)
			
			new_room.set_script(preload("res://Scripts/UI/OfficeRoom.gd"))
			office_grid.add_child(new_room)
			new_room.setup_room("QARoom", Color("#ff003c"), main_node.get_node("/root/SimulationEngine").tycoon_manager)
		main_node._update_ui()
	else:
		print("不夠資金擴建房間！")

func toggle_help_menu() -> void:
	if main_node.help_menu_instance and is_instance_valid(main_node.help_menu_instance):
		main_node.help_menu_instance.close()
	else:
		var scene = load("res://Scenes/UI/HelpMenu.tscn")
		if scene:
			main_node.help_menu_instance = scene.instantiate()
			main_node.add_child(main_node.help_menu_instance)
			main_node.help_menu_instance.closed.connect(func(): main_node.help_menu_instance = null)
			main_node.help_menu_instance.get_node("VBox/Title").text = tr("UI_HELP_TITLE")
			main_node.help_menu_instance.get_node("VBox/Scroll/Content/GoalLabel").text = tr("HELP_GOAL")
			main_node.help_menu_instance.get_node("VBox/Scroll/Content/ControlsLabel").text = tr("HELP_CONTROLS")
			main_node.help_menu_instance.get_node("VBox/Scroll/Content/TipsLabel").text = tr("HELP_TIPS")
			main_node.help_menu_instance.get_node("VBox/CloseButton").text = tr("UI_CLOSE")

func update_ticker(tick_count: int, funds: int, reputation: int) -> void:
	if not main_node or not main_node.ticker: return
	
	var f_color = "#39ff14" if funds > 0 else "#ff003c"
	var r_color = "#39ff14" if reputation > 50 else "#ff003c"
	main_node.ticker.text = "[color=#888888]ARCHON CORP | TICK:[/color] [color=#ffffff]%d[/color] [color=#888888]| %s:[/color] [color=%s]$%d[/color] [color=#888888]| %s:[/color] [color=%s]%d[/color]" % [
		tick_count, 
		tr("UI_FUNDS"), f_color, funds,
		tr("UI_REP"), r_color, reputation
	]
