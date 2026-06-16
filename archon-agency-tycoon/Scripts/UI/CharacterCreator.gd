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

func set_config(p_config: Resource) -> void:
    config = p_config

func _ready() -> void:
    current_agent_data = preload("res://Scripts/Resources/AgentResource.gd").new("New Employee", 1)
    
    # Try to load GameConfig automatically if not set
    if config == null:
        var config_path = "res://GameConfig.tres"
        if ResourceLoader.exists(config_path):
            config = load(config_path)
    
    # 1. Setup role options
    if role_option:
        role_option.add_item("DEV", 1)
        role_option.add_item("SALES", 0)
        role_option.add_item("QA", 2)
        
    # 2. Localize text
    _update_translations()
    
    # 3. Connect signals
    if gender_btn: gender_btn.pressed.connect(_on_gender_pressed)
    if hair_style_btn: hair_style_btn.pressed.connect(_on_hair_style_pressed)
    if outfit_btn: outfit_btn.pressed.connect(_on_outfit_pressed)
    if tool_btn: tool_btn.pressed.connect(_on_tool_pressed)
    if color_slider: color_slider.value_changed.connect(_on_color_changed)
    if randomize_btn: randomize_btn.pressed.connect(_on_randomize_pressed)
    if recruit_btn: recruit_btn.pressed.connect(_on_recruit_pressed)
    if cancel_btn: cancel_btn.pressed.connect(_on_cancel_pressed)
    
    if btn_idle: btn_idle.pressed.connect(_on_anim_idle)
    if btn_work: btn_work.pressed.connect(_on_anim_work)
    if btn_rest: btn_rest.pressed.connect(_on_anim_rest)
    
    # Initial Update
    _update_preview()

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
    # In Alice_Parts, hair often includes skin outline. Modulating it turns skin red.
    # We will pass white to prevent the red face issue until we swap to full modular assets.
    current_agent_data.hair_color = Color.WHITE
    current_agent_data.outfit_style = outfit_style
    current_agent_data.tool_style = tool_style
    
    agent_view.apply_agent_data(current_agent_data)

func _on_recruit_pressed() -> void:
    var name_val = name_edit.text.strip_edges()
    if name_val == "":
        name_val = "Agent " + str(randi() % 1000)
    current_agent_data.agent_name = name_val
    current_agent_data.role = role_option.get_selected_id()
    
    character_created.emit(current_agent_data)
    closed.emit()
    if is_inside_tree(): queue_free()

func _on_cancel_pressed() -> void:
    closed.emit()
    if is_inside_tree(): queue_free()

