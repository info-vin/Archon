extends Resource
class_name CardData

enum CardType { NONE, ACTION, DATA_CHIP, NOISE_CHIP }
enum MatchType { NONE, HYBRID, VECTOR, KEYWORD }

# --- Topology Talent Constants ---
const TALENT_WIDE_NET = "wide_net"
const TALENT_STRICT_PURITY = "strict_purity"
const TALENT_HYBRID_MASTERY = "hybrid_mastery"

const WIDE_NET_BONUS = 3
const STRICT_PURITY_BONUS = 0.1
const HYBRID_MASTERY_REQ = 3
# -------------------------------

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

@export var base_card_id: String = ""
@export var level: int = 1

func get_rag_parameters() -> Dictionary:
	var params = {
		"match_count": min(10, 1 + (level - 1)),
		"min_score": min(0.9, 0.0 + (level - 1) * 0.1),
		"use_hybrid": (level >= 5),
		"use_reranking": (level >= 8)
	}
	
	var tree = Engine.get_main_loop() as SceneTree
	if tree:
		var sm = tree.root.get_node_or_null("SaveManager")
		if sm:
			if TALENT_WIDE_NET in sm.unlocked_talents:
				params["match_count"] += WIDE_NET_BONUS
			if TALENT_STRICT_PURITY in sm.unlocked_talents:
				params["min_score"] = min(0.99, params["min_score"] + STRICT_PURITY_BONUS)
			if TALENT_HYBRID_MASTERY in sm.unlocked_talents:
				params["use_hybrid"] = (level >= HYBRID_MASTERY_REQ)
	
	if id == "dense_search":
		params["use_hybrid"] = false
	elif id == "reranker":
		params["use_reranking"] = true
		
	return params

func is_noise(safe_threshold: float = 0.5) -> bool:
	if type == CardType.NOISE_CHIP:
		return true
	if type != CardType.DATA_CHIP:
		return false
	return similarity < safe_threshold

func _to_string():
	if get_instance_id() > 0:
		return "%s:%d (Sim: %.2f)" % [title, get_instance_id(), similarity]
	return title
