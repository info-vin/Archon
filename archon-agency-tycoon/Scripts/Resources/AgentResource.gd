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
@export var gender: int = 0		  # 0: Female, 1: Male
@export var hair_style: int = 1	  # 1: Long hair, 2: Short hair, 3: Medium/Pigtails
@export var hair_color: Color = Color.WHITE
@export var outfit_style: int = 1	# 1: Mage Robe, 2: Formal Vest
@export var tool_style: int = 1	  # 1: DEV Wand, 2: SALES Cards, 3: QA Spell

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

func to_dict() -> Dictionary:
	return {
		"agent_name": agent_name,
		"role": role,
		"state": state,
		"energy": energy,
		"code_speed": code_speed,
		"charisma": charisma,
		"debug_logic": debug_logic,
		"luck": luck,
		"gender": gender,
		"hair_style": hair_style,
		"hair_color": hair_color.to_html(),
		"outfit_style": outfit_style,
		"tool_style": tool_style,
		"equipped_hair": equipped_hair,
		"equipped_outfit": equipped_outfit,
		"equipped_tool": equipped_tool
	}

static func from_dict(data: Dictionary) -> AgentResource:
	var a = AgentResource.new()
	if data.has("agent_name"): a.agent_name = data["agent_name"]
	if data.has("role"): a.role = data["role"]
	if data.has("state"): a.state = data["state"]
	if data.has("energy"): a.energy = data["energy"]
	if data.has("code_speed"): a.code_speed = data["code_speed"]
	if data.has("charisma"): a.charisma = data["charisma"]
	if data.has("debug_logic"): a.debug_logic = data["debug_logic"]
	if data.has("luck"): a.luck = data["luck"]
	if data.has("gender"): a.gender = data["gender"]
	if data.has("hair_style"): a.hair_style = data["hair_style"]
	if data.has("hair_color"): a.hair_color = Color(data["hair_color"])
	if data.has("outfit_style"): a.outfit_style = data["outfit_style"]
	if data.has("tool_style"): a.tool_style = data["tool_style"]
	if data.has("equipped_hair"): a.equipped_hair = data["equipped_hair"]
	if data.has("equipped_outfit"): a.equipped_outfit = data["equipped_outfit"]
	if data.has("equipped_tool"): a.equipped_tool = data["equipped_tool"]
	return a
