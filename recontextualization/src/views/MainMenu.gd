extends Control

@onready var lang_button: OptionButton = $VBoxContainer/SettingsBox/LangBox/LangButton
@onready var vol_slider: HSlider = $VBoxContainer/SettingsBox/VolBox/VolSlider

func _ready() -> void:
    $VBoxContainer/NewCareerButton.pressed.connect(_on_new_career_pressed)
    $VBoxContainer/ContinueButton.pressed.connect(_on_continue_pressed)
    $VBoxContainer/CardManagementButton.pressed.connect(_on_card_management_pressed)
    $VBoxContainer/QuitButton.pressed.connect(_on_quit_pressed)
    
    lang_button.item_selected.connect(_on_lang_selected)
    vol_slider.value_changed.connect(_on_vol_changed)
    
    var sm = get_node_or_null("/root/SaveManager")
    if sm != null:
        if sm.language == "en":
            lang_button.selected = 0
        else:
            lang_button.selected = 1
        vol_slider.value = sm.bgm_volume

func _on_new_career_pressed() -> void:
    var sm = get_node_or_null("/root/SaveManager")
    if sm != null:
        # Wipe run progress but maybe keep career level? For "New Career", maybe we reset career level too?
        # Actually, let's keep career level and just start the GameBoard
        sm.max_player_hp = 100.0
        sm.has_completed_tutorial = false
        sm.save_progress()
    get_tree().change_scene_to_file("res://src/views/TransitionVideo.tscn")

func _on_continue_pressed() -> void:
    get_tree().change_scene_to_file("res://src/views/TransitionVideo.tscn")

func _on_card_management_pressed() -> void:
    get_tree().change_scene_to_file("res://src/views/CardManagementMenu.tscn")

func _on_quit_pressed() -> void:
    get_tree().quit()

func _on_lang_selected(index: int) -> void:
    var sm = get_node_or_null("/root/SaveManager")
    if sm != null:
        if index == 0:
            sm.language = "en"
        else:
            sm.language = "zh_TW"
        sm.save_progress()
        sm._apply_settings()

func _on_vol_changed(value: float) -> void:
    var sm = get_node_or_null("/root/SaveManager")
    if sm != null:
        sm.bgm_volume = value
        sm.save_progress()
        sm._apply_settings()
