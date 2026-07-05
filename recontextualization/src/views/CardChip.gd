extends Control

@export var tex_target: Texture2D
@export var tex_noise: Texture2D
@export var tex_keyword: Texture2D
@export var tex_dense: Texture2D
@export var tex_reranker: Texture2D

@onready var title_label: Label = $Title
@onready var icon_rect: TextureRect = $Icon
@onready var background: TextureRect = $Background

var card_data: Resource

func set_card_data(card: Resource):
	if card == null:
		return
	
	card_data = card
	
	if card.get("title") != null:
		title_label.text = card.get("title")
	
	var type_val = card.get("type") if card.get("type") != null else 0
	
	if type_val == 2:
		if tex_target: icon_rect.texture = tex_target
		tooltip_text = "資料晶片：提供給 LLM 的安全上下文"
		background.modulate = Color(1.0, 1.0, 1.0, 1.0)
	elif type_val == 3:
		if tex_noise: icon_rect.texture = tex_noise
		tooltip_text = "雜訊晶片：包含錯誤資訊，會引發幻覺！"
		background.modulate = Color(1.0, 0.7, 0.7, 1.0) # Tint frame red for noise
	elif type_val == 1:
		var action_id = card.get("id") if card.get("id") != null else ""
		if action_id == "keyword_search" and tex_keyword:
			icon_rect.texture = tex_keyword
		elif action_id == "dense_search" and tex_dense:
			icon_rect.texture = tex_dense
		elif action_id == "reranker" and tex_reranker:
			icon_rect.texture = tex_reranker
		elif tex_keyword:
			icon_rect.texture = tex_keyword
		
		tooltip_text = "行動卡：消耗 AP 執行交付或過濾"
		background.modulate = Color(0.8, 0.9, 1.0, 1.0) # Tint frame blue for action

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
