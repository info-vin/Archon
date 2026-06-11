extends Control

var deck_manager: DeckManager
var hand: Array[CardStats] = []

@onready var deck_label = $VBoxContainer/DeckLabel
@onready var hand_label = $VBoxContainer/HandLabel
@onready var draw_button = $VBoxContainer/DrawButton

func _ready() -> void:
	# 遊戲啟動時，初始化我們的邏輯層 (Model)
	deck_manager = DeckManager.new()
	
	# 塞入 5 張假卡牌到牌庫中
	for i in range(5):
		var card = CardStats.new()
		var card_names = ["🐛 Quick Fix", "🛡️ Code Review", "☕ Coffee Break", "🚀 Deep Refactor", "🔥 Hotfix"]
		card.card_name = card_names[i]
		deck_manager.add_card(card)
	
	update_ui()
	
	# 綁定按鈕點擊事件到控制器邏輯 (Controller)
	draw_button.pressed.connect(_on_draw_button_pressed)

func _on_draw_button_pressed() -> void:
	var drawn_card = deck_manager.draw_card()
	if drawn_card != null:
		hand.append(drawn_card)
	else:
		draw_button.text = "Deck is Empty!"
		draw_button.disabled = true
		
	update_ui()

# 更新視圖 (View)
func update_ui() -> void:
	deck_label.text = "Deck Size: " + str(deck_manager.get_deck_size())
	
	if hand.is_empty():
		hand_label.text = "Hand: (Empty)"
	else:
		var hand_text = "Hand:\n"
		for card in hand:
			hand_text += "[ " + card.card_name + " ]  "
		hand_label.text = hand_text
