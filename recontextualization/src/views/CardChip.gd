extends Control

@onready var title_label: Label = $Title
@onready var icon_rect: TextureRect = $Icon
@onready var background: ColorRect = $Background

var card_data: Resource

func set_card_data(card: Resource):
	if card == null:
		return
	
	card_data = card
	
	if card.get("title") != null:
		title_label.text = card.get("title")
	
	# Load maaack placeholder icons based on card type
	# CardType: ACTION = 1, DATA_CHIP = 2, NOISE_CHIP = 3
	var type_val = card.get("type") if card.get("type") != null else 0
	var icon_path = "res://assets/maaack/Sourced/Icons/Game-Icons.net/person.png"
	
	if type_val == 2:
		icon_path = "res://assets/maaack/Sourced/Icons/Game-Icons.net/achievement.png" # Golden chip
		background.color = Color(0.1, 0.4, 0.1, 1.0)
	elif type_val == 3:
		icon_path = "res://assets/maaack/Sourced/Icons/Game-Icons.net/evil-minion.png" # Noise/virus
		background.color = Color(0.4, 0.1, 0.1, 1.0)
	elif type_val == 1:
		icon_path = "res://assets/maaack/Sourced/Icons/Game-Icons.net/brute.png" # Action
		background.color = Color(0.1, 0.1, 0.4, 1.0)
	
	if ResourceLoader.exists(icon_path):
		icon_rect.texture = load(icon_path)

func _get_drag_data(_at_position: Vector2):
	# Create a visual preview of the card being dragged
	var preview = duplicate()
	preview.modulate.a = 0.7 # Make it slightly transparent
	
	# The preview needs a Control node to hold it so it centers on the mouse
	var control = Control.new()
	control.add_child(preview)
	
	# Offset the preview so the mouse is roughly in the center
	preview.position = -size / 2.0
	
	set_drag_preview(control)
	
	# Return self so the PlayArea can extract data and reparent this exact node
	return self
