extends PanelContainer

signal character_created(agent_data)
signal closed

@onready var agent_view: ModularAgentView = $HBox/PreviewArea/ViewportContainer/SubViewport/ModularAgent

@onready var name_edit: LineEdit = $HBox/ControlArea/NameEdit
@onready var role_option: OptionButton = $HBox/ControlArea/RoleHBox/RoleOption
@onready var gender_btn: Button = $HBox/ControlArea/GenderHBox/GenderBtn
@onready var hair_style_btn: Button = $HBox/ControlArea/HairHBox/HairStyleBtn
@onready var outfit_btn: Button = $HBox/ControlArea/OutfitHBox/OutfitBtn
@onready var tool_btn: Button = $HBox/ControlArea/ToolHBox/ToolBtn
@onready var color_slider: HSlider = $HBox/ControlArea/ColorHBox/ColorSlider
@onready var randomize_btn: Button = $HBox/ControlArea/Actions/RandomizeBtn
@onready var recruit_btn: Button = $HBox/ControlArea/Actions/RecruitBtn
@onready var cancel_btn: Button = $HBox/ControlArea/Actions/CancelBtn

@onready var btn_idle: Button = $HBox/PreviewArea/AnimButtons/BtnIdle
@onready var btn_work: Button = $HBox/PreviewArea/AnimButtons/BtnWork
@onready var btn_rest: Button = $HBox/PreviewArea/AnimButtons/BtnRest

# Current selected states
var gender: int = 0
var hair_style: int = 1
var outfit_style: int = 1
var tool_style: int = 1
var hair_hue: float = 0.0 # 0-360 range
var character_name: String = ""

# The persistent data
var current_agent_data: AgentResource
var config: Resource

# AI Spritesheet Mode variables
var is_spritesheet_mode: bool = true
var prompt_builder
var slot_paths: Array = ["", "", "", "", "", "", ""]
var current_step_select: int = 0
var mode_btn: Button
var ai_area: VBoxContainer
var path_edits: Array = []
var lock_label: Label
var file_dialog: FileDialog

func set_config(p_config: Resource) -> void:
	config = p_config

func _ready() -> void:
	z_index = 100
	var style = StyleBoxFlat.new()
	style.bg_color = Color(0.02, 0.02, 0.05, 1.0)
	add_theme_stylebox_override("panel", style)

	current_agent_data = preload("res://Scripts/Resources/AgentResource.gd").new("New Employee", 1)
	if config == null and ResourceLoader.exists("res://GameConfig.tres"):
		config = load("res://GameConfig.tres")
	if role_option:
		role_option.add_item("DEV", 1)
		role_option.add_item("SALES", 0)
		role_option.add_item("QA", 2)
		role_option.item_selected.connect(_on_role_selected)
	_update_translations()
	
	var btns = {gender_btn: _on_gender_pressed, hair_style_btn: _on_hair_style_pressed, outfit_btn: _on_outfit_pressed, tool_btn: _on_tool_pressed, randomize_btn: _on_randomize_pressed, recruit_btn: _on_recruit_pressed, cancel_btn: _on_cancel_pressed, btn_idle: _on_anim_idle, btn_work: _on_anim_work, btn_rest: _on_anim_rest}
	for b in btns:
		if b: b.pressed.connect(btns[b])
	if color_slider: color_slider.value_changed.connect(_on_color_changed)
	
	prompt_builder = preload("res://Scripts/UI/AIPromptBuilder.gd").new()
	file_dialog = FileDialog.new()
	file_dialog.file_mode = FileDialog.FILE_MODE_OPEN_FILE
	file_dialog.access = FileDialog.ACCESS_FILESYSTEM
	file_dialog.filters = ["*.png", "*.jpg", "*.jpeg", "*.mp4", "*.webm"]
	file_dialog.file_selected.connect(_on_file_selected)
	add_child(file_dialog)
	
	mode_btn = Button.new()
	mode_btn.text = "Mode: AI Spritesheet"
	mode_btn.pressed.connect(_on_mode_toggle_pressed)
	$HBox/ControlArea.add_child(mode_btn)
	$HBox/ControlArea.move_child(mode_btn, 1)
	
	_setup_ai_prompt_manager_ui()
	
	var paperdoll_nodes = ["GenderHBox", "HairHBox", "OutfitHBox", "ToolHBox", "ColorHBox", "Actions/RandomizeBtn"]
	for n_name in paperdoll_nodes:
		var n = $HBox/ControlArea.get_node(n_name)
		if n: n.visible = false
		
	ai_area.visible = true
	recruit_btn.text = "Bake & Recruit"
	recruit_btn.disabled = true
	_update_ai_ui()

func _update_translations() -> void:
	$HBox/ControlArea/Title.text = tr("UI_CHARACTER_CREATOR")
	name_edit.placeholder_text = tr("UI_ENTER_NAME")
	$HBox/ControlArea/RoleHBox/Label.text = tr("UI_ROLE")
	$HBox/ControlArea/GenderHBox/Label.text = tr("UI_GENDER")
	$HBox/ControlArea/HairHBox/Label.text = tr("UI_HAIR_STYLE")
	$HBox/ControlArea/OutfitHBox/Label.text = tr("UI_OUTFIT")
	$HBox/ControlArea/ToolHBox/Label.text = tr("UI_TOOL")
	$HBox/ControlArea/ColorHBox/Label.text = tr("UI_HAIR_COLOR")
	if randomize_btn: randomize_btn.text = tr("UI_RANDOMIZE")
	recruit_btn.text = tr("UI_RECRUIT")
	cancel_btn.text = tr("UI_CANCEL")
	gender_btn.text = tr("UI_GENDER_FEMALE") if gender == 0 else tr("UI_GENDER_MALE")
	hair_style_btn.text = tr("UI_STYLE") + " " + str(hair_style)
	outfit_btn.text = tr("UI_OUTFIT") + " " + str(outfit_style)
	tool_btn.text = tr("UI_TOOL") + " " + str(tool_style)

func _on_gender_pressed() -> void:
	gender = 1 - gender
	gender_btn.text = tr("UI_GENDER_FEMALE") if gender == 0 else tr("UI_GENDER_MALE")
	_update_preview()

func _on_hair_style_pressed() -> void:
	var max_styles = config.max_hair_styles if config else 3
	hair_style = (hair_style % max_styles) + 1
	hair_style_btn.text = tr("UI_STYLE") + " " + str(hair_style)
	_update_preview()

func _on_outfit_pressed() -> void:
	var max_styles = config.max_outfit_styles if config else 2
	outfit_style = (outfit_style % max_styles) + 1
	outfit_btn.text = tr("UI_OUTFIT") + " " + str(outfit_style)
	_update_preview()

func _on_tool_pressed() -> void:
	var max_styles = config.max_tool_styles if config else 3
	tool_style = (tool_style % max_styles) + 1
	tool_btn.text = tr("UI_TOOL") + " " + str(tool_style)
	_update_preview()

func _on_color_changed(value: float) -> void:
	hair_hue = value
	_update_preview()

func _on_randomize_pressed() -> void:
	var max_hair = config.max_hair_styles if config else 3
	var max_outfit = config.max_outfit_styles if config else 2
	var max_tool = config.max_tool_styles if config else 3
	gender = randi() % 2
	hair_style = (randi() % max_hair) + 1
	outfit_style = (randi() % max_outfit) + 1
	tool_style = (randi() % max_tool) + 1
	hair_hue = randf() * 360.0
	gender_btn.text = tr("UI_GENDER_FEMALE") if gender == 0 else tr("UI_GENDER_MALE")
	hair_style_btn.text = tr("UI_STYLE") + " " + str(hair_style)
	outfit_btn.text = tr("UI_OUTFIT") + " " + str(outfit_style)
	tool_btn.text = tr("UI_TOOL") + " " + str(tool_style)
	color_slider.value = hair_hue
	_update_preview()
	
func _on_anim_idle() -> void:
	current_agent_data.state = AgentResource.AgentState.IDLE
	agent_view.apply_agent_data(current_agent_data)

func _on_anim_work() -> void:
	current_agent_data.state = AgentResource.AgentState.WORKING
	agent_view.apply_agent_data(current_agent_data)

func _on_anim_rest() -> void:
	current_agent_data.state = AgentResource.AgentState.RESTING
	agent_view.apply_agent_data(current_agent_data)

func _update_preview() -> void:
	if not agent_view: return
	current_agent_data.gender = gender
	current_agent_data.hair_style = hair_style
	current_agent_data.hair_color = Color.from_hsv(hair_hue / 360.0, 1.0, 1.0)
	current_agent_data.outfit_style = outfit_style
	current_agent_data.tool_style = tool_style
	agent_view.apply_agent_data(current_agent_data)

func _run_bake(name_val: String, output_res_path: String) -> int:
	var global_out_path = ProjectSettings.globalize_path(output_res_path)
	var script_path = ProjectSettings.globalize_path("res://tools/bake_spritesheet.py")
	DirAccess.make_dir_recursive_absolute(global_out_path.get_base_dir())
	var args = ["--role", name_val, "--output", global_out_path]
	for i in range(7):
		args.append("--slot" + str(i+1))
		args.append(ProjectSettings.globalize_path(slot_paths[i]))
	var output = []
	var exit_code = OS.execute("uv", ["run", "python", script_path] + args, output, true)
	if exit_code != 0:
		exit_code = OS.execute("python", [script_path] + args, output, true)
	if exit_code != 0:
		exit_code = OS.execute("python", [script_path] + args, output, true)
	return exit_code

func _on_recruit_pressed() -> void:
	var name_val = name_edit.text.strip_edges()
	if name_val == "":
		name_val = character_name if character_name != "" else "Agent " + str(randi() % 1000)
	current_agent_data.agent_name = name_val
	current_agent_data.role = role_option.get_selected_id()
	if is_spritesheet_mode:
		var output_res_path = "res://Assets/Characters/" + name_val.to_lower().replace(" ", "_") + "/spritesheet.png"
		_run_bake(name_val, output_res_path)
		current_agent_data.spritesheet_path = output_res_path
	character_created.emit(current_agent_data)
	closed.emit()
	if is_inside_tree(): queue_free()

func _on_cancel_pressed() -> void:
	closed.emit()
	if is_inside_tree(): queue_free()



func _setup_ai_prompt_manager_ui() -> void:
	var ai_manager = preload("res://Scripts/UI/AIPromptManager.gd").new()
	ai_manager.setup()
	ai_area = ai_manager
	
	var actions_node = get_node_or_null("HBox/ControlArea/Actions")
	$HBox/ControlArea.size_flags_vertical = Control.SIZE_EXPAND_FILL
	$HBox/ControlArea.add_child(ai_area)
	if actions_node:
		$HBox/ControlArea.move_child(ai_area, actions_node.get_index())
		
	ai_area.visible = false
	ai_manager.copy_prompt_requested.connect(_on_copy_prompt_pressed_for_step)
	ai_manager.browse_requested.connect(_on_browse_pressed_for_step)
	
	path_edits = ai_manager.path_edits
	lock_label = ai_manager.lock_label
	
	_refresh_ai_prompts()

func _refresh_ai_prompts() -> void:
	var prompts = []
	for i in range(7):
		prompts.append(_get_prompt_text_for_step(i))
	if ai_area and ai_area.has_method("update_prompts"):
		ai_area.update_prompts(prompts)

func _get_prompt_text_for_step(idx: int) -> String:
	var role_name = "DEV"
	if role_option:
		role_name = role_option.get_item_text(role_option.get_selected_id())
	var agent_name = name_edit.text if name_edit and name_edit.text != "" else "New Employee"
	if prompt_builder:
		return prompt_builder.get_prompt_text_for_step(idx, role_name, agent_name)
	return ""

func _update_ai_ui() -> void:
	if not is_spritesheet_mode: return
			
	var all_filled = true
	var current_index = -1
	for i in range(len(slot_paths)):
		if slot_paths[i] != "":
			path_edits[i].text = slot_paths[i]
		else:
			path_edits[i].text = ""
			all_filled = false
			if current_index == -1:
				current_index = i
				
	if current_index == -1: current_index = 6
	
	if lock_label:
		if all_filled:
			lock_label.text = "All assets ready. You can now Bake & Recruit!"
			lock_label.modulate = Color(0, 1, 0, 1)
			recruit_btn.disabled = false
		else:
			lock_label.text = "Please upload Step 0" + str(current_index+1) + " image."
			lock_label.modulate = Color(1, 0.4, 0.4)
			recruit_btn.disabled = true

func _on_browse_pressed_for_step(idx: int) -> void:
	current_step_select = idx
	file_dialog.popup_centered(Vector2(600, 400))

func _on_file_selected(path: String) -> void:
	slot_paths[current_step_select] = path
	_update_ai_ui()
	var all_filled = true
	for p in slot_paths:
		if p == "": all_filled = false
	if all_filled:
		_bake_preview()

func _on_copy_prompt_pressed_for_step(idx: int) -> void:
	var text = _get_prompt_text_for_step(idx)
	var regex = RegEx.new()
	regex.compile("\\[.*?\\]")
	text = regex.sub(text, "", true)
	DisplayServer.clipboard_set(text)
	
func _bake_preview() -> void:
	var name_val = name_edit.text.strip_edges()
	if name_val == "": name_val = "PreviewAgent"
	var output_res_path = "res://Assets/Characters/preview_bake/spritesheet.png"
	_run_bake(name_val, output_res_path)
	current_agent_data.spritesheet_path = output_res_path
	_update_preview()
	agent_view.visible = true

func _on_role_selected(index: int) -> void:
	current_agent_data.role = role_option.get_selected_id()
	_update_translations()
	_update_preview()
	_update_ai_ui()

func _on_mode_toggle_pressed() -> void:
	is_spritesheet_mode = not is_spritesheet_mode
	
	var paperdoll_nodes = ["GenderHBox", "HairHBox", "OutfitHBox", "ToolHBox", "ColorHBox", "Actions/RandomizeBtn"]
	for n in paperdoll_nodes:
		var node = get_node_or_null("HBox/ControlArea/" + n)
		if node: node.visible = not is_spritesheet_mode
		
	if ai_area:
		ai_area.visible = is_spritesheet_mode
		
	var title = get_node_or_null("HBox/ControlArea/Title")
	if title:
		title.text = "AI Spritesheet Mode" if is_spritesheet_mode else "UI_CHARACTER_CREATOR"
		
	var mode_btn_node = get_node_or_null("HBox/ControlArea/ModeToggle")
	if mode_btn_node:
		mode_btn_node.text = "Switch to Paperdoll" if is_spritesheet_mode else "Switch to AI Mode"
		
	if agent_view:
		if is_spritesheet_mode and current_agent_data.spritesheet_path == "":
			agent_view.visible = false
		else:
			agent_view.visible = true
			
	if not is_spritesheet_mode:
		recruit_btn.disabled = false
	recruit_btn.text = "Bake & Recruit" if is_spritesheet_mode else tr("UI_RECRUIT")
