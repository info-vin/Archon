extends Resource
class_name AgentResource

enum AgentRole { SALES, DEV, QA }
enum AgentState { IDLE, WORKING, RESTING, EXHAUSTED }

@export var agent_name: String = "New Agent"
@export var role: AgentRole = AgentRole.DEV
@export var state: AgentState = AgentState.IDLE
@export var energy: int = 100

# SPECIAL Attributes
@export var code_speed: int = 0
@export var charisma: int = 0
@export var debug_logic: int = 0
@export var luck: int = 0

# Appearance settings (Option A / Pixel Customizer)
@export var gender: int = 0          # 0: Female, 1: Male
@export var hair_style: int = 1      # 1: Long hair, 2: Short hair, 3: Medium/Pigtails
@export var hair_color: Color = Color.WHITE
@export var outfit_style: int = 1    # 1: Mage Robe, 2: Formal Vest
@export var tool_style: int = 1      # 1: DEV Wand, 2: SALES Cards, 3: QA Spell

# Appearance settings (Option B / Legacy SVG fallback)
@export var equipped_hair: String = ""
@export var equipped_outfit: String = ""
@export var equipped_tool: String = ""

func _init(p_name: String = "New Agent", p_role: AgentRole = AgentRole.DEV, p_code: int = 0, p_char: int = 0, p_debug: int = 0, p_luck: int = 0, p_hair: String = "", p_outfit: String = "", p_tool: String = ""):
    agent_name = p_name
    role = p_role
    state = AgentState.IDLE
    energy = 100
    code_speed = p_code
    charisma = p_char
    debug_logic = p_debug
    luck = p_luck
    equipped_hair = p_hair
    equipped_outfit = p_outfit
    equipped_tool = p_tool
    gender = 0
    hair_style = 1
    hair_color = Color.WHITE
    outfit_style = 1
    tool_style = 1
