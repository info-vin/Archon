extends PanelContainer

signal character_created(agent_data)
signal closed

@onready var preview_body: TextureRect = $HBox/PreviewArea/DollContainer/Body
@onready var preview_eyes: TextureRect = $HBox/PreviewArea/DollContainer/Eyes
@onready var preview_hair: TextureRect = $HBox/PreviewArea/DollContainer/Hair
@onready var preview_outfit: TextureRect = $HBox/PreviewArea/DollContainer/Outfit
@onready var preview_tool: TextureRect = $HBox/PreviewArea/DollContainer/Tool

@onready var name_edit: LineEdit = $HBox/ControlArea/NameEdit
@onready var role_option: OptionButton = $HBox/ControlArea/RoleHBox/RoleOption
@onready var gender_btn: Button = $HBox/ControlArea/GenderHBox/GenderBtn
@onready var hair_style_btn: Button = $HBox/ControlArea/HairHBox/HairStyleBtn
@onready var outfit_btn: Button = $HBox/ControlArea/OutfitHBox/OutfitBtn
@onready var tool_btn: Button = $HBox/ControlArea/ToolHBox/ToolBtn
@onready var color_slider: HSlider = $HBox/ControlArea/ColorHBox/ColorSlider
@onready var recruit_btn: Button = $HBox/ControlArea/Actions/RecruitBtn
@onready var cancel_btn: Button = $HBox/ControlArea/Actions/CancelBtn

# Current selected states
var gender: int = 0
var hair_style: int = 1
var outfit_style: int = 1
var tool_style: int = 1
var hair_hue: float = 0.0 # 0-360 range
var character_name: String = ""

func _ready() -> void:
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
    if recruit_btn: recruit_btn.pressed.connect(_on_recruit_pressed)
    if cancel_btn: cancel_btn.pressed.connect(_on_cancel_pressed)
    
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
    hair_style = (hair_style % 3) + 1
    hair_style_btn.text = tr("UI_STYLE") + " " + str(hair_style)
    _update_preview()

func _on_outfit_pressed() -> void:
    outfit_style = (outfit_style % 2) + 1
    outfit_btn.text = tr("UI_OUTFIT") + " " + str(outfit_style)
    _update_preview()

func _on_tool_pressed() -> void:
    tool_style = (tool_style % 3) + 1
    tool_btn.text = tr("UI_TOOL") + " " + str(tool_style)
    _update_preview()

func _on_color_changed(value: float) -> void:
    hair_hue = value
    _update_preview()

func _update_preview() -> void:
    # 1. Base Skeleton Gender
    if preview_body:
        if gender == 0:
            preview_body.texture = preload("res://Assets/Characters/Alice_Parts/part_006.png")
        else:
            preview_body.texture = preload("res://Assets/Characters/Alice_Parts/part_010.png")
        
    if preview_eyes:
        preview_eyes.texture = preload("res://Assets/Characters/Alice_Parts/part_016.png")
    
    # 2. Hair Style
    if preview_hair:
        match hair_style:
            1:
                preview_hair.texture = preload("res://Assets/Characters/Alice_Parts/part_001.png")
            2:
                preview_hair.texture = preload("res://Assets/Characters/Alice_Parts/part_015.png")
            3:
                preview_hair.texture = preload("res://Assets/Characters/Alice_Parts/part_017.png")
            
        # Apply Hue Modulation to Hair
        var hair_color = Color.from_hsv(hair_hue / 360.0, 0.8, 1.0)
        preview_hair.modulate = hair_color
    
    # 3. Outfit Style
    if preview_outfit:
        match outfit_style:
            1:
                preview_outfit.texture = preload("res://Assets/Characters/Alice_Parts/part_021.png")
            2:
                preview_outfit.texture = preload("res://Assets/Characters/Alice_Parts/part_020.png")
            
    # 4. Tool Style
    if preview_tool:
        match tool_style:
            1:
                preview_tool.texture = preload("res://Assets/Characters/Alice_Parts/part_033.png")
            2:
                preview_tool.texture = preload("res://Assets/Characters/Alice_Parts/part_031.png")
            3:
                preview_tool.texture = preload("res://Assets/Characters/Alice_Parts/part_026.png")

func _on_recruit_pressed() -> void:
    var name_val = "New Agent"
    if character_name != "":
        name_val = character_name
    elif name_edit:
        var text_strip = name_edit.text.strip_edges()
        if text_strip != "":
            name_val = text_strip
        
    var selected_role = 1
    if role_option and role_option.get_item_count() > 0:
        selected_role = role_option.get_selected_id()
    
    # Create the AgentResource using customization properties
    var agent = preload("res://Scripts/Resources/AgentResource.gd").new(name_val, selected_role)
    agent.gender = gender
    agent.hair_style = hair_style
    agent.hair_color = Color.from_hsv(hair_hue / 360.0, 0.8, 1.0)
    agent.outfit_style = outfit_style
    agent.tool_style = tool_style
    
    # Emit first so handlers can read the resource before this node gets queue_free'd
    character_created.emit(agent)
    closed.emit()
    
    # Check if we are inside the scene tree before freeing
    if is_inside_tree():
        queue_free()

func _on_cancel_pressed() -> void:
    closed.emit()
    queue_free()
