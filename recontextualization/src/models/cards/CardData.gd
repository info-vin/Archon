extends Resource
class_name CardData

enum CardType { NONE, ACTION, DATA_CHIP, NOISE_CHIP }
enum MatchType { NONE, HYBRID, VECTOR, KEYWORD }

@export var id: String = ""
@export var title: String = "CardData"
@export_multiline var description: String = ""
@export_range(0, 9) var ap_cost: int = 1
@export var icon: Texture2D
@export var base_color: Color = Color.WHITE

@export var type: CardType = CardType.NONE

# --- RAG Specific Properties ---
@export var match_type: MatchType = MatchType.NONE
@export var similarity: float = 0.0
@export var chunk_metadata: Dictionary = {}

func is_noise(safe_threshold: float = 0.5) -> bool:
	if type != CardType.DATA_CHIP:
		return false
	return similarity < safe_threshold

func _to_string():
	if get_instance_id() > 0:
		return "%s:%d (Sim: %.2f)" % [title, get_instance_id(), similarity]
	return title
