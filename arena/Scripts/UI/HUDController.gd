extends RefCounted
class_name HUDController

var player_hp_bar: ProgressBar
var enemy_hp_bar: ProgressBar
var player_hp_text: Label
var enemy_hp_text: Label
var turn_label: Label
var enemy_intent: Label
var hud_container: TokenHud

func setup(
	p_player_hp: ProgressBar, p_enemy_hp: ProgressBar, 
	p_player_hp_text: Label, p_enemy_hp_text: Label,
	p_turn_label: Label, p_enemy_intent: Label, 
	p_hud_container: TokenHud
) -> void:
	player_hp_bar = p_player_hp
	enemy_hp_bar = p_enemy_hp
	player_hp_text = p_player_hp_text
	enemy_hp_text = p_enemy_hp_text
	turn_label = p_turn_label
	enemy_intent = p_enemy_intent
	hud_container = p_hud_container
func update_hp(is_player: bool, current: int, max_hp: int) -> void:
	var bar = player_hp_bar if is_player else enemy_hp_bar
	var text = player_hp_text if is_player else enemy_hp_text
	MainUIHelpers.update_hp_bar(bar, bar, text, current, max_hp)

func update_turn(turn: int) -> void:
	if turn_label:
		turn_label.text = "第 %d 回合 (Turn %d)" % [turn, turn]

func update_intent(dmg: int, block: int, strength: int) -> void:
	var intent_text = "Intent: [Attack] %d DMG" % dmg
	if block > 0:
		intent_text += " | [Block] %d" % block
	if strength > 0:
		intent_text += " (+%d [Str])" % strength
	enemy_intent.text = intent_text

func update_mana(current: int, max_mana: int) -> void:
	if hud_container and hud_container.token_label:
		hud_container.token_label.text = "%d/%d" % [current, max_mana]

func update_block(is_player: bool, block: int) -> void:
	if is_player and hud_container and hud_container.block_label:
		hud_container.block_label.text = str(block)
