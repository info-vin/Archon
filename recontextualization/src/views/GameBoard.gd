extends Control

signal request_dashboard
signal request_workshop
signal request_start
signal request_restart
signal request_deliver
signal request_save_progress
signal request_load_progress
signal request_main_menu
signal request_quit_game
signal request_card_management
signal request_teammate_dashboard

@onready var hand_container: Container = $HandContainer
@onready var event_queue: Node = $EventQueue

@export_file("*.tscn") var main_menu_scene: String
@export_file("*.tscn") var dashboard_scene: String
@export_file("*.tscn") var workshop_scene: String
@export_file("*.tscn") var card_menu_scene: String
@export_file("*.tscn") var teammate_dashboard_scene: String
@export var video_victory: VideoStream
@export var video_defeat_glitch: VideoStream
@export var video_defeat_shutdown: VideoStream

var card_chip_scene = preload("res://src/views/CardChip.tscn")


@onready var game_hud: HBoxContainer = $MarginContainer/RootHBox/MainColumn/GameHUD
@onready var btn_character: TextureButton = $MarginContainer/RootHBox/HubNavigation/CharacterButton
@onready var btn_cards: TextureButton = $MarginContainer/RootHBox/HubNavigation/CardManagementButton
@onready var btn_workshop: TextureButton = $MarginContainer/RootHBox/HubNavigation/WorkshopButton
@onready var btn_teammate: TextureButton = $MarginContainer/RootHBox/HubNavigation/TeammateButton
@onready var agent_companion: Control = $AgentCompanion
@onready var query_input: LineEdit = $QueryBar/QueryInput
@onready var deliver_button: Button = $QueryBar/DeliverButton
@onready var tutorial_panel: ColorRect = $TutorialPanel
@onready var game_over_panel: ColorRect = $GameOverPanel
@onready var end_game_video: VideoStreamPlayer = $EndGameVideoPlayer
@onready var pause_menu: ColorRect = $PauseMenu

func _ready() -> void:
	tutorial_panel.request_start.connect(func(): request_start.emit())
	game_over_panel.request_dashboard.connect(func(): request_dashboard.emit())

	btn_character.pressed.connect(func(): request_dashboard.emit())
	btn_cards.pressed.connect(func(): request_card_management.emit())
	btn_workshop.pressed.connect(func(): request_workshop.emit())
	btn_teammate.pressed.connect(func(): request_teammate_dashboard.emit())
	
	deliver_button.pressed.connect(func(): request_deliver.emit())
	
	if pause_menu:
		pause_menu.resume_game.connect(func(): pause_menu.hide())
		pause_menu.save_progress.connect(func(): request_save_progress.emit())
		pause_menu.load_progress.connect(func(): 
			request_load_progress.emit()
			pause_menu.hide()
		)
		pause_menu.quit_to_menu.connect(func():
			pause_menu.hide()
			request_main_menu.emit()
		)
		pause_menu.quit_game.connect(func(): 
			var dlg = ConfirmationDialog.new()
			dlg.title = "確認離開 (Confirm Quit)"
			dlg.dialog_text = "您確定要離開戰場嗎？進度將會自動保存。\n(Are you sure you want to quit? Progress will be saved automatically.)"
			dlg.confirmed.connect(func(): request_quit_game.emit())
			add_child(dlg)
			dlg.popup_centered()
		)

	if query_input:
		var style = StyleBoxFlat.new()
		style.bg_color = Color(0, 0, 0, 0.8)
		style.set_corner_radius_all(4)
		style.content_margin_left = 10
		style.content_margin_right = 10
		query_input.add_theme_stylebox_override("normal", style)
		query_input.add_theme_stylebox_override("focus", style)
		query_input.focus_entered.connect(func():
			$QueryBar.z_index = 100
		)
		query_input.focus_exited.connect(func():
			$QueryBar.z_index = 0
		)

	var hint_label = $MarginContainer/RootHBox/MainColumn/PlayArea/HintLabel
	if hint_label:
		hint_label.modulate = Color(1, 1, 1, 0.85) # Increase from 0.3 to 0.85
		var hint_style = StyleBoxFlat.new()
		hint_style.bg_color = Color(0, 0, 0, 0.6)
		hint_style.set_corner_radius_all(8)
		hint_label.add_theme_stylebox_override("normal", hint_style)

	var ev_bus = get_node_or_null("/root/EventBus")
	if ev_bus and ev_bus.has_signal("system_message"):
		ev_bus.system_message.connect(show_toast_message)

func show_toast_message(msg: String) -> void:
	var lbl = Label.new()
	lbl.text = msg
	lbl.add_theme_color_override("font_color", Color.RED)
	lbl.add_theme_font_size_override("font_size", 32)
	add_child(lbl)
	lbl.position = size / 2.0 - Vector2(100, 0)
	var tween = create_tween()
	tween.tween_property(lbl, "position", lbl.position + Vector2(0, -100), 1.5).set_trans(Tween.TRANS_QUART).set_ease(Tween.EASE_OUT)
	tween.parallel().tween_property(lbl, "modulate:a", 0.0, 1.5)
	tween.tween_callback(lbl.queue_free)

func _input(event: InputEvent) -> void:
	if event is InputEventKey and event.pressed and event.keycode == KEY_ESCAPE:
		if not tutorial_panel.visible and not game_over_panel.visible:
			if pause_menu:
				pause_menu.visible = not pause_menu.visible

# ================================
# View API for Controller
# ================================

func initialize_career(level: int, max_player_hp: float) -> void:
	game_hud.initialize_career(level, max_player_hp)
	btn_character.visible = true
	btn_cards.visible = true
	btn_workshop.visible = true
	btn_teammate.visible = true

func setup_tutorial(has_completed: bool) -> void:
	if has_completed:
		tutorial_panel.show()
	else:
		tutorial_panel.hide()

func hide_tutorial() -> void:
	tutorial_panel.hide()

func update_ap(new_ap: int) -> void:
	game_hud.update_ap(new_ap)

func update_purity(purity: float) -> void:
	game_hud.update_purity(purity)

func update_player_hp(new_hp: float) -> void:
	game_hud.update_player_hp(new_hp)

func update_crisis_hp(new_hp: float) -> void:
	game_hud.update_crisis_hp(new_hp, event_queue)

func update_sla(new_sla: float) -> void:
	game_hud.update_sla(new_sla)

func update_poisoning(ratio: float) -> void:
	game_hud.update_poisoning(ratio)

func update_rate_limit(compression: float) -> void:
	game_hud.update_rate_limit(compression, event_queue)

func trigger_chaos_event(event_id: String) -> void:
	if agent_companion and agent_companion.has_method("trigger_chaos_event"):
		agent_companion.trigger_chaos_event(event_id)

func play_deliver_blast() -> void:
	CombatJuice.deliver_blast(deliver_button)

func purify_context(remaining_cards: Array) -> void:
	var play_area = $MarginContainer/RootHBox/MainColumn/PlayArea
	if not play_area: return
	for child in play_area.get_children():
		if child.name == "HintLabel":
			continue
		if child.get("card_data") != null:
			var c_data = child.card_data
			if not remaining_cards.has(c_data):
				event_queue.add_animation(func():
					var tween = CombatJuice.card_dissolve(child)
					await tween.finished
				)

func anim_draw_card(card: Resource) -> void:
	event_queue.add_animation(func():
		var chip = card_chip_scene.instantiate()
		hand_container.add_child(chip)
		chip.set_card_data(card)
		
		chip.modulate.a = 0.0
		chip.scale = Vector2(0.1, 0.1)
		
		var tween = create_tween().set_parallel(true)
		tween.tween_property(chip, "modulate:a", 1.0, 0.3).set_ease(Tween.EASE_OUT)
		tween.tween_property(chip, "scale", Vector2(1.0, 1.0), 0.3).set_trans(Tween.TRANS_SPRING)
		
		await get_tree().create_timer(0.3).timeout
	)

func anim_play_card(card: Resource) -> void:
	var target_child = null
	for child in hand_container.get_children():
		if child.has_method("get_card_data") and child.get_card_data() == card:
			target_child = child
			break
			
	if target_child != null:
		event_queue.add_animation(func():
			var play_area = $MarginContainer/RootHBox/MainColumn/PlayArea
			
			# Hide hint text when a card is played
			if play_area.has_node("HintLabel"):
				play_area.get_node("HintLabel").hide()
				
			target_child.get_parent().remove_child(target_child)
			play_area.add_child(target_child)
			
			# Dynamic Z-Swap stack: stack cards with an offset
			var played_cards = []
			for c in play_area.get_children():
				if c.has_method("get_card_data"):
					played_cards.append(c)
					
			for i in range(played_cards.size()):
				var c = played_cards[i]
				var base_x = (play_area.size.x / 2.0) - (c.size.x / 2.0)
				var base_y = (play_area.size.y / 2.0) - (c.size.y / 2.0)
				
				# Offset each card slightly to create a 3D stack effect
				var offset = Vector2(i * 30.0, i * 20.0)
				var target_pos = Vector2(base_x, base_y) + offset
				
				# Set default Z-index to stack order (0, 1, 2, 3)
				c.z_index = i
				c.set_meta("base_z_index", i)
				
				# Hook up dynamic Z-Swap on hover
				if not c.has_meta("play_area_hover"):
					c.mouse_entered.connect(func():
						c.z_index = 100
					)
					c.mouse_exited.connect(func():
						c.z_index = c.get_meta("base_z_index", 0)
					)
					c.set_meta("play_area_hover", true)
				
				var tween = create_tween()
				tween.tween_property(c, "position", target_pos, 0.4).set_trans(Tween.TRANS_SPRING)
				tween.parallel().tween_property(c, "scale", Vector2(0.8, 0.8), 0.3)
				
			await get_tree().create_timer(0.3).timeout
		)

func show_game_over(is_victory: bool, rank: String = "") -> void:
	if is_victory:
		game_over_panel.get_node("VBox/Title").text = "危機解除！"
		if rank != "":
			game_over_panel.get_node("VBox/Title").text += " (Rank: " + rank + ")"
		game_over_panel.get_node("VBox/Title").add_theme_color_override("font_color", Color.GREEN)
		if video_victory:
			end_game_video.stream = video_victory
		end_game_video.show()
		end_game_video.play()
		await end_game_video.finished
	else:
		game_over_panel.get_node("VBox/Title").text = "系統崩潰！(SLA 超時或幻覺反噬)"
		game_over_panel.get_node("VBox/Title").add_theme_color_override("font_color", Color.RED)
		if video_defeat_glitch:
			end_game_video.stream = video_defeat_glitch
		end_game_video.show()
		end_game_video.play()
		await end_game_video.finished
		
		if video_defeat_shutdown:
			end_game_video.stream = video_defeat_shutdown
		end_game_video.play()
		await end_game_video.finished
		
	end_game_video.hide()
	game_over_panel.show()
