extends Control

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

@export var main_menu_scene: PackedScene
@export var video_victory: VideoStream
@export var video_defeat_glitch: VideoStream
@export var video_defeat_shutdown: VideoStream

var card_chip_scene = preload("res://src/views/CardChip.tscn")
var CombatJuice = preload("res://src/views/components/CombatJuice.gd")

@onready var poison_bar: ProgressBar = $MarginContainer/VBoxContainer/TopBar/PoisonBar
@onready var rate_limit_label: Label = $MarginContainer/VBoxContainer/TopBar/RateLimitLabel
@onready var ap_label: Label = $MarginContainer/VBoxContainer/TopBar/APLabel
@onready var purity_bar: ProgressBar = $MarginContainer/VBoxContainer/TopBar/PurityBar
@onready var crisis_hp_bar: ProgressBar = $MarginContainer/VBoxContainer/TopBar/CrisisHPBar
@onready var career_label: Label = $MarginContainer/VBoxContainer/TopBar/CareerLabel
@onready var player_hp_bar: ProgressBar = $MarginContainer/VBoxContainer/TopBar/PlayerHPBar
@onready var sla_progress: ProgressBar = $MarginContainer/VBoxContainer/TopBar/SLAPorgressBar
@onready var sla_text: Label = $MarginContainer/VBoxContainer/TopBar/SLAPorgressBar/SLAText

@onready var query_input: LineEdit = $MarginContainer/VBoxContainer/QueryBar/QueryInput
@onready var deliver_button: Button = $MarginContainer/VBoxContainer/QueryBar/DeliverButton

@onready var tutorial_panel: ColorRect = $TutorialPanel
@onready var start_button: Button = $TutorialPanel/VBox/StartButton

@onready var game_over_panel: ColorRect = $GameOverPanel
@onready var game_over_title: Label = $GameOverPanel/VBox/Title
@onready var restart_button: Button = $GameOverPanel/VBox/RestartButton
@onready var end_game_video: VideoStreamPlayer = $EndGameVideoPlayer

@onready var pause_menu: ColorRect = $PauseMenu

func _ready() -> void:
	var style_green = StyleBoxFlat.new()
	style_green.bg_color = Color(0.2, 0.8, 0.2, 1.0)
	purity_bar.add_theme_stylebox_override("fill", style_green)

	var style_red = StyleBoxFlat.new()
	style_red.bg_color = Color(1.0, 0.2, 0.2, 1.0)
	poison_bar.add_theme_stylebox_override("fill", style_red)

	var style_dark_red = StyleBoxFlat.new()
	style_dark_red.bg_color = Color(0.6, 0.0, 0.0, 1.0)
	crisis_hp_bar.add_theme_stylebox_override("fill", style_dark_red)

	start_button.pressed.connect(func(): request_start.emit())
	restart_button.pressed.connect(func(): request_restart.emit())
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
		
	game_over_panel.hide()

func _input(event: InputEvent) -> void:
	if event is InputEventKey and event.pressed and event.keycode == KEY_ESCAPE:
		if not tutorial_panel.visible and not game_over_panel.visible:
			if pause_menu:
				pause_menu.visible = not pause_menu.visible

# ================================
# View API for Controller
# ================================

func initialize_career(level: int, max_player_hp: float) -> void:
	career_label.text = "L" + str(level)
	player_hp_bar.max_value = max_player_hp

func setup_tutorial(has_completed: bool) -> void:
	if has_completed:
		tutorial_panel.show()
	else:
		tutorial_panel.hide()

func hide_tutorial() -> void:
	tutorial_panel.hide()

func update_ap(new_ap: int) -> void:
	ap_label.text = tr("hud_ap") + ": %d" % new_ap

func update_purity(purity: float) -> void:
	purity_bar.value = purity * 100.0

func update_player_hp(new_hp: float) -> void:
	player_hp_bar.value = new_hp

func update_crisis_hp(new_hp: float) -> void:
	var old_val = crisis_hp_bar.value
	crisis_hp_bar.value = new_hp
	
	if old_val > new_hp:
		event_queue.add_animation(func():
			var tween = CombatJuice.damage_flash_and_shake(crisis_hp_bar)
			await tween.finished
		)

func update_sla(new_sla: float) -> void:
	sla_progress.value = new_sla
	var mins = int(new_sla) / 60
	var secs = int(new_sla) % 60
	sla_text.text = "SLA: %02d:%02d" % [mins, secs]
	
	if new_sla < 30.0:
		CombatJuice.warning_pulse(sla_progress, Time.get_ticks_msec())
	elif new_sla < 60.0:
		sla_progress.modulate = Color.RED
	else:
		sla_progress.modulate = Color.WHITE

func update_poisoning(ratio: float) -> void:
	poison_bar.value = ratio * 100.0

func update_rate_limit(compression: float) -> void:
	if compression < 0.8:
		rate_limit_label.show()
		event_queue.add_animation(func():
			var tween = CombatJuice.flash_alpha(rate_limit_label)
			await tween.finished
		)
	else:
		rate_limit_label.hide()

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
		game_over_title.text = "危機解除！"
		if rank != "":
			game_over_title.text += " (Rank: " + rank + ")"
		game_over_title.add_theme_color_override("font_color", Color.GREEN)
		if video_victory:
			end_game_video.stream = video_victory
		end_game_video.show()
		end_game_video.play()
		await end_game_video.finished
	else:
		game_over_title.text = "系統崩潰！(SLA 超時或幻覺反噬)"
		game_over_title.add_theme_color_override("font_color", Color.RED)
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
