extends Control

signal request_dashboard
signal request_workshop
signal request_start
signal request_restart
signal request_deliver
signal request_query(text: String)
signal request_save_progress
signal request_load_progress
signal request_main_menu
signal request_quit_game

@onready var hand_container: Container = $MarginContainer/VBoxContainer/HandContainer
@onready var event_queue: Node = $EventQueue

@export_file("*.tscn") var main_menu_scene: String
@export_file("*.tscn") var dashboard_scene: String
@export_file("*.tscn") var workshop_scene: String
@export var video_victory: VideoStream
@export var video_defeat_glitch: VideoStream
@export var video_defeat_shutdown: VideoStream

var card_chip_scene = preload("res://src/views/CardChip.tscn")


@onready var game_hud: HBoxContainer = $MarginContainer/VBoxContainer/GameHUD
@onready var agent_companion: Control = $AgentCompanion
@onready var query_input: LineEdit = $MarginContainer/VBoxContainer/QueryBar/QueryInput
@onready var deliver_button: Button = $MarginContainer/VBoxContainer/QueryBar/DeliverButton
@onready var tutorial_panel: ColorRect = $TutorialPanel
@onready var game_over_panel: ColorRect = $GameOverPanel
@onready var end_game_video: VideoStreamPlayer = $EndGameVideoPlayer
@onready var pause_menu: ColorRect = $PauseMenu

func _ready() -> void:
	tutorial_panel.request_start.connect(func(): request_start.emit())
	game_over_panel.request_dashboard.connect(func(): request_dashboard.emit())

	$MarginContainer/VBoxContainer/QueryBar/WorkshopButton.pressed.connect(func(): request_workshop.emit())
	deliver_button.pressed.connect(func(): request_deliver.emit())
	query_input.text_submitted.connect(func(text): request_query.emit(text))
	
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
		pause_menu.quit_game.connect(func(): request_quit_game.emit())

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
	var play_area = $MarginContainer/VBoxContainer/PlayArea
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
			var play_area = $MarginContainer/VBoxContainer/PlayArea
			target_child.get_parent().remove_child(target_child)
			play_area.add_child(target_child)
			
			var tween = create_tween()
			var target_pos = (play_area.size / 2.0) - (target_child.size / 2.0)
			tween.tween_property(target_child, "position", target_pos, 0.4).set_trans(Tween.TRANS_SPRING)
			tween.parallel().tween_property(target_child, "scale", Vector2(0.8, 0.8), 0.3)
			await get_tree().create_timer(0.4).timeout
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
