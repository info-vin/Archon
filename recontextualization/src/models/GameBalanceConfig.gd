class_name GameBalanceConfig

# --- Game State Constants ---
const MAX_SLA_TIME = 300.0
const HALLUCINATION_DAMAGE_PER_NOISE = 20.0
const SLA_PENALTY_PER_DELIVERY = 2.0
const BASE_FIREPOWER = 1000.0
const SAFE_PURITY_THRESHOLD = 0.5
const DELIVERY_AP_COST = 1
const SEARCH_AP_COST = 2

# --- Battle Rule Engine Constants ---
const RANK_S_SLA_RATIO = 0.5
const RANK_A_SLA_RATIO = 0.2
const RANK_S_DELIVERY_LIMIT = 2
const RANK_A_HP_RATIO = 0.5
const MULTIPLIER_BASE = 1.0
const MULTIPLIER_CHAIN = 1.5

# --- Mechanic Constants ---
const MAX_POISON_RATIO_LIMIT = 0.8
const POISON_TIME_SCALE = 0.5
const SEARCH_SIMILARITY_THRESHOLD = 0.5
const SEARCH_TOP_K = 5
const RATE_LIMIT_COMPRESSION_BASE = 1.0
const RATE_LIMIT_COMPRESSION_STEP = 0.1
const RATE_LIMIT_COMPRESSION_MIN = 0.5

# --- Sector Difficulty Constants ---
const SECTOR_1_BASE_HP = 10000.0
const SECTOR_2_BASE_HP = 15000.0
const SECTOR_3_BASE_HP = 20000.0

const SECTOR_1_POISON = 0.0
const SECTOR_2_POISON = 0.2
const SECTOR_3_POISON = 0.4

const SECTOR_2_CR_THRESHOLD = 500
const SECTOR_3_CR_THRESHOLD = 1000

# --- Progression & Rewards Constants ---
const BASE_XP_PER_LEVEL = 100.0

const REWARD_S_CR = 40
const REWARD_A_CR = 30
const REWARD_B_CR = 20

const REWARD_S_XP = 100.0
const REWARD_A_XP = 50.0
const REWARD_B_XP = 25.0

const LOSS_CR_PENALTY = 15

# --- Card Identifiers ---
const CARD_KEYWORD = "action_keyword"
const CARD_DENSE = "dense_search"
const CARD_RERANKER = "reranker"
const CARD_GRAPH_RAG = "graph_rag"

static func get_sector_base_hp(sector: int) -> float:
	if sector == 3: return SECTOR_3_BASE_HP
	if sector == 2: return SECTOR_2_BASE_HP
	return SECTOR_1_BASE_HP

static func get_sector_poison(sector: int) -> float:
	if sector == 3: return SECTOR_3_POISON
	if sector == 2: return SECTOR_2_POISON
	return SECTOR_1_POISON
