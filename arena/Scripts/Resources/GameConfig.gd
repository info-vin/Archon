extends Resource
class_name GameConfig

# --- Game Settings ---
@export var turn_timer_seconds: float = 30.0

# --- Default Difficulty Settings ---
@export var easy_mana: int = 5
@export var easy_hp: int = 60
@export var easy_dmg: int = 5

@export var normal_mana: int = 5
@export var normal_hp: int = 200
@export var normal_dmg: int = 10

@export var hard_mana: int = 5
@export var hard_hp: int = 400
@export var hard_dmg: int = 12

@export var expert_mana: int = 4
@export var expert_hp: int = 600
@export var expert_dmg: int = 15

# --- Card UI & Effects ---
@export var card_base_size: Vector2 = Vector2(216, 324)

# --- Avatar & UI ---
@export var avatar_size: Vector2 = Vector2(216, 324)
@export var timer_font_size_normal: int = 64
@export var timer_font_size_alert: int = 88
@export var combat_text_font_size: int = 48

# --- Paths ---
@export var cjk_font_path: String = "res://Assets/Fonts/arial_unicode.ttf"
@export var hit_sound_path: String = "res://Assets/Sounds/hit.wav"
@export var error_sound_path: String = "res://Assets/Sounds/error.wav"
@export var hover_sound_path: String = "res://Assets/Sounds/hover.wav"
@export var play_sound_path: String = "res://Assets/Sounds/play.wav"

@export var player_avatar_path: String = "res://Assets/Images/player_lead.png"

@export var bug_easy_path: String = "res://Assets/Images/bug_easy.png"
@export var bug_normal_path: String = "res://Assets/Images/bug_normal.png"
@export var bug_hard_path: String = "res://Assets/Images/bug_hard.png"
@export var bug_expert_path: String = "res://Assets/Images/bug_expert.png"

@export var bg_easy_path: String = "res://Assets/Background/easy_bg.jpg"
@export var bg_normal_path: String = "res://Assets/Background/landscape.jpg"
@export var bg_hard_path: String = "res://Assets/Background/hard_bg.jpg"
@export var bg_expert_path: String = "res://Assets/Background/expert_bg.jpg"

@export var card_scene_path: String = "res://Scenes/UI/CardUI.tscn"
