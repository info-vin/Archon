extends MarginContainer

signal card_clicked(card_id: String)

@export var card_id: String = ""
@export var is_equipped: bool = false

@onready var btn: TextureButton = $TextureButton

func _ready() -> void:
    btn.pressed.connect(func(): card_clicked.emit(card_id))

func setup(id: String, equipped: bool) -> void:
    card_id = id
    is_equipped = equipped
    var name_label: Label = $TextureButton/VBoxContainer/CardName
    var type_label: Label = $TextureButton/VBoxContainer/CardType
    var indicator: Label = $TextureButton/VBoxContainer/ActionIndicator
    
    name_label.text = "【" + id.to_upper() + "】"
    type_label.text = "Type: Action\nCost: 1 AP"
    
    if is_equipped:
        indicator.text = "[-]"
        indicator.add_theme_color_override("font_color", Color(1.0, 0.4, 0.4))
    else:
        indicator.text = "[+]"
        indicator.add_theme_color_override("font_color", Color(0.4, 1.0, 0.4))

func play_fly_anim(target_pos: Vector2) -> void:
    var tween = get_tree().create_tween()
    tween.set_parallel(true)
    tween.tween_property(self, "global_position", target_pos, 0.3).set_trans(Tween.TRANS_QUAD).set_ease(Tween.EASE_IN_OUT)
    tween.tween_property(self, "scale", Vector2(0.1, 0.1), 0.3).set_trans(Tween.TRANS_QUAD).set_ease(Tween.EASE_IN)
    tween.chain().tween_callback(queue_free)
