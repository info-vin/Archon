extends Node
class_name TeammateDashboardController

@export var game_board_scene: PackedScene
@export var card_menu_scene: PackedScene
@export var main_menu_scene: PackedScene

var view: Control
var save_manager: Node
var env_config: Node

func _init(v: Control = null) -> void:
	if v:
		_setup_with_view(v)

func _ready() -> void:
	if get_parent() and get_parent() is Control and view == null:
		_setup_with_view(get_parent())

func _setup_with_view(v: Control) -> void:
	view = v
	save_manager = view.get_node_or_null("/root/SaveManager")
	env_config = view.get_node_or_null("/root/EnvConfig")
	
	_connect_signals()
	_initialize_view()

func _connect_signals() -> void:
	view.teammate_selected.connect(_on_teammate_selected)
	view.model_selected.connect(_on_model_selected)
	view.react_toggled.connect(_on_react_toggled)
	view.budget_changed.connect(_on_budget_changed)
	view.request_start_dive.connect(_on_start_dive)
	view.request_card_menu.connect(_on_card_menu)
	view.request_return_menu.connect(_on_return_menu)

func _initialize_view() -> void:
	if not save_manager or save_manager.teammates.is_empty():
		_init_default_teammates()
		
	if save_manager and save_manager.teammates.size() > 0:
		var teammate_data = []
		for t in save_manager.teammates:
			teammate_data.append({
				"name": t.get("name", t.get("id", "Unknown")),
				"level": t.get("level", 1)
			})
		view.populate_teammates(teammate_data)
		
		var models = []
		if env_config and env_config.models.size() > 0:
			for m in env_config.models:
				models.append(m.get("display_name", m.get("id")))
		else:
			models.append("Local/Fallback Model")
		view.populate_models(models)

func _init_default_teammates() -> void:
	if save_manager:
		var def_model = "gemini-1.5-flash"
		if env_config: def_model = env_config.default_model
		
		save_manager.teammates.append({
			"id": "alice_flash",
			"name": "Alice (Socializer)",
			"level": 1,
			"ingested_docs": 0,
			"equipped_model": def_model,
			"allow_react": false,
			"token_cap": 500
		})
		save_manager.teammates.append({
			"id": "bob_pro",
			"name": "Bob (Deductor)",
			"level": 3,
			"ingested_docs": 12,
			"equipped_model": env_config.models[1].get("id") if env_config and env_config.models.size() > 1 else def_model,
			"allow_react": true,
			"token_cap": 1500
		})
		save_manager.save_progress()

func _on_teammate_selected(idx: int) -> void:
	if not save_manager or idx >= save_manager.teammates.size():
		return
		
	var t = save_manager.teammates[idx]
	var def_model = "gemini-1.5-flash"
	if env_config: def_model = env_config.default_model
	var equipped = t.get("equipped_model", def_model)
	var model_idx = 0
	if env_config: model_idx = env_config.get_model_index_by_id(equipped)
	
	view.update_teammate_details(model_idx, t.get("allow_react", false), t.get("token_cap", 500), t.get("ingested_docs", 0))

func _on_model_selected(idx: int, model_idx: int) -> void:
	if not save_manager or idx >= save_manager.teammates.size(): return
	var model_str = "gemini-1.5-flash"
	if env_config: model_str = env_config.get_model_id_by_index(model_idx)
	save_manager.teammates[idx]["equipped_model"] = model_str
	save_manager.save_progress()

func _on_react_toggled(idx: int, button_pressed: bool) -> void:
	if not save_manager or idx >= save_manager.teammates.size(): return
	save_manager.teammates[idx]["allow_react"] = button_pressed
	save_manager.save_progress()

func _on_budget_changed(idx: int, val: float) -> void:
	if not save_manager or idx >= save_manager.teammates.size(): return
	save_manager.teammates[idx]["token_cap"] = int(val)
	save_manager.save_progress()

func _on_start_dive() -> void:
	if game_board_scene:
		view.get_tree().change_scene_to_packed(game_board_scene)

func _on_card_menu() -> void:
	if card_menu_scene:
		view.get_tree().change_scene_to_packed(card_menu_scene)

func _on_return_menu() -> void:
	if main_menu_scene:
		view.get_tree().change_scene_to_packed(main_menu_scene)
