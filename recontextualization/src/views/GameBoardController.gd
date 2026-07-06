extends Node

@onready var view = get_parent()

var save_manager: Node:
	get:
		if Engine.has_singleton("SaveManager"):
			return Engine.get_singleton("SaveManager")
		return get_node_or_null("/root/SaveManager")

var game_state: Node:
	get:
		if Engine.has_singleton("GameState"):
			return Engine.get_singleton("GameState")
		return get_node_or_null("/root/GameState")

var event_bus: Node:
	get:
		if Engine.has_singleton("EventBus"):
			return Engine.get_singleton("EventBus")
		return get_node_or_null("/root/EventBus")

func _ready() -> void:
	if not view.is_node_ready():
		await view.ready

	# 1. Connect View signals to Controller actions
	view.request_dashboard.connect(_on_dashboard_requested)
	view.request_workshop.connect(_on_workshop_requested)
	view.request_start.connect(_on_request_start)
	view.request_restart.connect(_on_request_restart)
	view.request_deliver.connect(_on_request_deliver)
	view.request_query.connect(_on_request_query)
	view.request_save_progress.connect(_on_request_save_progress)
	view.request_load_progress.connect(_on_request_load_progress)
	view.request_main_menu.connect(_on_request_main_menu)
	view.request_quit_game.connect(_on_request_quit_game)

	# 2. Connect Model/State signals to View updates
	if game_state != null:
		game_state.ap_changed.connect(view.update_ap)
		game_state.chaos_event_triggered.connect(view.trigger_chaos_event)
		game_state.context_updated.connect(view.update_purity)
		game_state.hp_changed.connect(view.update_crisis_hp)
		game_state.player_hp_changed.connect(view.update_player_hp)
		game_state.sla_changed.connect(view.update_sla)
		game_state.game_over.connect(view.show_game_over)
		game_state.poisoning_updated.connect(view.update_poisoning)
		game_state.rate_limit_updated.connect(view.update_rate_limit)
		game_state.context_purified.connect(view.purify_context)
		
		# 3. Initialize View from Model data
		if save_manager != null:
			view.initialize_career(save_manager.career_level, save_manager.max_player_hp)
			
			if not save_manager.has_completed_tutorial:
				view.hide_tutorial()
				game_state.is_tutorial_active = true
				game_state.start_game()
			else:
				game_state.is_tutorial_active = false
				view.setup_tutorial(true)
		else:
			view.setup_tutorial(true)

		# Initial values
		view.update_ap(game_state.current_ap)
		view.update_crisis_hp(game_state.crisis_hp)
		view.update_player_hp(game_state.player_hp)
		view.update_sla(game_state.sla_timer)
		view.update_poisoning(game_state.data_poisoning_ratio)
		view.update_rate_limit(game_state.rate_limit_compression)

	if event_bus != null:
		if event_bus.has_signal("card_drawn"):
			event_bus.card_drawn.connect(view.anim_draw_card)
		if event_bus.has_signal("card_played"):
			event_bus.card_played.connect(view.anim_play_card)

# ================================
# Actions triggered by View
# ================================

func _on_request_start() -> void:
	view.hide_tutorial()
	if game_state != null:
		game_state.start_game()

func _on_request_restart() -> void:
	if view.main_menu_scene:
		get_tree().change_scene_to_file(view.main_menu_scene)

func _on_request_deliver() -> void:
	view.play_deliver_blast()
	if game_state != null:
		game_state.deliver_context()

func _on_request_query(text: String) -> void:
	if game_state != null:
		game_state.trigger_search(1) # 1 = KEYWORD

func _on_request_save_progress() -> void:
	if save_manager != null:
		save_manager.save_progress()

func _on_dashboard_requested() -> void:
	if view.dashboard_scene:
		get_tree().change_scene_to_file(view.dashboard_scene)

func _on_workshop_requested() -> void:
	if view.workshop_scene:
		get_tree().change_scene_to_file(view.workshop_scene)

func _on_request_load_progress() -> void:
	if save_manager != null:
		save_manager.load_progress()
	get_tree().reload_current_scene()

func _on_request_main_menu() -> void:
	if view.main_menu_scene:
		get_tree().change_scene_to_file(view.main_menu_scene)

func _on_request_quit_game() -> void:
	get_tree().quit()
