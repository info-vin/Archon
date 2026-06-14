extends PanelContainer
class_name TaskCard

var task_id: int = -1
var task_name: String = ""
var required_ticks: int = 0
var reward_funds: int = 0

@onready var title_label: Label = $VBox/TitleLabel
@onready var details_label: Label = $VBox/DetailsLabel

func setup(id: int, t_name: String, ticks: int, reward: int) -> void:
    task_id = id
    task_name = t_name
    required_ticks = ticks
    reward_funds = reward
    
func _ready() -> void:
    _update_text()

func _update_text() -> void:
    if title_label:
        title_label.text = task_name
    if details_label:
        details_label.text = "🕒 %d %s\n💰 $%d" % [required_ticks, tr("UI_TICK"), reward_funds]

# --- Drag and Drop Logic ---

func _get_drag_data(at_position: Vector2) -> Variant:
    # Use another control as drag preview
    var preview = Label.new()
    preview.text = task_name
    preview.add_theme_color_override("font_color", Color(1, 0.8, 0)) # Yellowish text
    set_drag_preview(preview)
    
    # The data we are dragging is just the task_id
    return { "type": "task", "task_id": task_id }
