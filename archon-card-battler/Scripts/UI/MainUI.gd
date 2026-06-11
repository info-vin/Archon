extends Control

var deck_manager: DeckManager
var hand: Array[CardStats] = []

# Game State
var player_hp: int = 30
var player_mana: int = 3
var player_block: int = 0
var enemy_hp: int = 50
var enemy_damage: int = 8

@onready var stats_label = $VBoxContainer/StatsLabel
@onready var enemy_label = $VBoxContainer/EnemyLabel
@onready var action_log = $VBoxContainer/ActionLog
@onready var card_buttons_container = $VBoxContainer/CardButtons
@onready var end_turn_button = $VBoxContainer/EndTurnButton

func _ready() -> void:
	deck_manager = DeckManager.new()
	_init_deck()
	
	end_turn_button.pressed.connect(_on_end_turn_pressed)
	
	start_player_turn()

func _init_deck() -> void:
	for i in range(15):
		var card = CardStats.new()
		var r = randi() % 4
		if r == 0:
			card.card_name = "🐛 Quick Fix"
			card.cost = 1
			card.damage = 6
		elif r == 1:
			card.card_name = "🛡️ Code Review"
			card.cost = 1
			card.block = 5
		elif r == 2:
			card.card_name = "☕ Coffee Break"
			card.cost = 0
		else:
			card.card_name = "🚀 Deep Refactor"
			card.cost = 2
			card.damage = 14
		deck_manager.add_card(card)

func start_player_turn() -> void:
	player_mana = 3
	player_block = 0
	
	# Draw 4 cards
	hand.clear()
	for i in range(4):
		var c = deck_manager.draw_card()
		if c != null:
			hand.append(c)
		else:
			log_action("Deck is empty!")
			break
	
	log_action("--- Player Turn Started. Drew cards. ---")
	update_ui()

func play_card(index: int) -> void:
	if index >= hand.size(): return
	var card = hand[index]
	
	if player_mana < card.cost:
		log_action("❌ Not enough Tokens to play " + card.card_name)
		return
		
	# Pay cost
	player_mana -= card.cost
	
	# Apply effects
	enemy_hp -= card.damage
	player_block += card.block
	
	var msg = "Played " + card.card_name + " (Cost: " + str(card.cost) + ")."
	if card.damage > 0: msg += " Dealt " + str(card.damage) + " DMG."
	if card.block > 0: msg += " Gained " + str(card.block) + " Block."
	log_action(msg)
	
	# Remove card from hand
	hand.remove_at(index)
	
	update_ui()
	check_win_condition()

func _on_end_turn_pressed() -> void:
	log_action("Player ended turn.")
	enemy_turn()

func enemy_turn() -> void:
	log_action("👾 Enemy attacks for " + str(enemy_damage) + " DMG!")
	
	var actual_damage = max(0, enemy_damage - player_block)
	player_hp -= actual_damage
	
	log_action("🛡️ Block absorbed " + str(player_block) + " DMG. Player took " + str(actual_damage) + " DMG.")
	
	update_ui()
	if !check_win_condition():
		start_player_turn()

func check_win_condition() -> bool:
	if enemy_hp <= 0:
		log_action("🎉 VICTORY! Memory Leak Resolved!")
		disable_input()
		return true
	if player_hp <= 0:
		log_action("💀 GAME OVER! Server Crashed.")
		disable_input()
		return true
	return false

func disable_input() -> void:
	end_turn_button.disabled = true
	for child in card_buttons_container.get_children():
		child.queue_free()

func log_action(msg: String) -> void:
	action_log.text = msg + "\n" + action_log.text

func update_ui() -> void:
	stats_label.text = "👨‍💻 Tech Lead | HP: %d | 🛡️ Block: %d | 💎 Tokens: %d\nDeck Size: %d" % [player_hp, player_block, player_mana, deck_manager.get_deck_size()]
	enemy_label.text = "👾 Memory Leak | HP: %d | Intent: ⚔️ %d DMG" % [enemy_hp, enemy_damage]
	
	# Rebuild card buttons dynamically
	for child in card_buttons_container.get_children():
		child.queue_free()
		
	var card_scene = preload("res://Scenes/UI/CardUI.tscn")
	for i in range(hand.size()):
		var card = hand[i]
		var card_ui = card_scene.instantiate()
		card_buttons_container.add_child(card_ui)
		
		# Setup visual data
		card_ui.setup(card, i)
		
		# Bind the index so the button knows which card to play
		card_ui.pressed.connect(func(): play_card(card_ui.card_index))
