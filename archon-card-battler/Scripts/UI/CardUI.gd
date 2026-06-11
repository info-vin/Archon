extends Button

@onready var cost_label = $VBox/TopRow/CostLabel
@onready var name_label = $VBox/NameLabel
@onready var desc_label = $VBox/DescLabel
@onready var type_label = $VBox/TopRow/TypeLabel

var card_index: int = -1

func setup(card_stats: CardStats, index: int) -> void:
	card_index = index
	cost_label.text = "💎 " + str(card_stats.cost)
	name_label.text = card_stats.card_name
	
	if card_stats.damage > 0 and card_stats.block > 0:
		desc_label.text = "Deal %d DMG.\nGain %d Block." % [card_stats.damage, card_stats.block]
		type_label.text = "Skill"
	elif card_stats.damage > 0:
		desc_label.text = "Deal %d DMG." % card_stats.damage
		type_label.text = "Attack"
	elif card_stats.block > 0:
		desc_label.text = "Gain %d Block." % card_stats.block
		type_label.text = "Defend"
	else:
		desc_label.text = "Draw cards or heal."
		type_label.text = "Power"

# 增加一點懸停動畫，讓卡牌更有手感
func _ready():
	mouse_entered.connect(_on_hover)
	mouse_exited.connect(_on_unhover)

func _on_hover():
	var tween = create_tween()
	tween.tween_property(self, "position:y", position.y - 15, 0.1)

func _on_unhover():
	var tween = create_tween()
	tween.tween_property(self, "position:y", position.y + 15, 0.1)
