extends Resource
class_name TycoonConfig

# Economic Settings
@export var recruit_cost: int = 500
@export var expand_cost: int = 500
@export var initial_funds: int = 500
@export var initial_reputation: int = 100

# Energy & Work Settings
@export var min_assign_energy: int = 10
@export var work_energy_drain: int = 10
@export var rest_energy_recovery: int = 20
@export var crisis_energy_drain: int = 5

# Rush & Crisis Settings
@export var rush_base_chance: float = 0.5
@export var rush_luck_modifier: float = 0.03
@export var rush_fail_energy_penalty: int = 30
@export var rush_fail_rep_penalty: int = 10
@export var crisis_spread_duration: int = 3
@export var crisis_spread_chance: float = 0.2

# Sales Loop Settings
@export var sales_task_ticks_needed: int = 3
@export var generated_task_ticks: int = 3
@export var generated_task_reward: int = 300

# Character Creation Styles
@export var max_hair_styles: int = 3
@export var max_outfit_styles: int = 2
@export var max_tool_styles: int = 3

# Calculation Divisors
@export var stat_divisor: int = 5
