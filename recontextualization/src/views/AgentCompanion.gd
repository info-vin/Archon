extends Control

class_name AgentCompanion

@onready var rich_text_label: RichTextLabel = RichTextLabel.new()
@onready var typewriter_timer: Timer = Timer.new()

var _typing_queue: Array = []
var _is_typing: bool = false
var _current_text: String = ""
var _char_index: int = 0

func _ready() -> void:
    _setup_ui()
    
    # Typewriter timer setup
    typewriter_timer.wait_time = 0.05
    typewriter_timer.timeout.connect(_on_typewriter_step)
    add_child(typewriter_timer)
    
    # Listen to game state events
    var gs = get_node_or_null("/root/GameState")
    if gs:
        gs.chaos_event_triggered.connect(_on_chaos_event)

func _setup_ui() -> void:
    custom_minimum_size = Vector2(300, 400)
    
    var panel = Panel.new()
    panel.set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT)
    add_child(panel)
    
    var vbox = VBoxContainer.new()
    vbox.set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT)
    panel.add_child(vbox)
    
    var header = Label.new()
    header.text = "=== AI 終端連線 (Terminal) ==="
    header.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
    vbox.add_child(header)
    
    rich_text_label.bbcode_enabled = true
    rich_text_label.size_flags_vertical = Control.SIZE_EXPAND_FILL
    vbox.add_child(rich_text_label)
    
    # Initial greeting
    push_message("[color=green]Agentic RAG Core initialized. Waiting for uplink...[/color]")

func push_message(msg: String) -> void:
    _typing_queue.append(msg)
    if not _is_typing:
        _start_next_message()

func _start_next_message() -> void:
    if _typing_queue.is_empty():
        _is_typing = false
        return
        
    _is_typing = true
    _current_text = _typing_queue.pop_front()
    _char_index = 0
    rich_text_label.text += "\n> "
    typewriter_timer.start()

func _on_typewriter_step() -> void:
    if _char_index < _current_text.length():
        rich_text_label.text += _current_text[_char_index]
        _char_index += 1
    else:
        typewriter_timer.stop()
        _start_next_message()

func _on_chaos_event(event_id: String) -> void:
    # We dynamically load ChaosEventPool without relying on Autoload just in case
    var pool_script = load("res://src/models/events/ChaosEventPool.gd")
    if pool_script:
        var ev = pool_script.get_event(event_id)
        if ev:
            push_message("[color=red]" + ev["dialogue"] + "[/color]")
            
            var juice = load("res://src/views/components/CombatJuice.gd")
            if juice: juice.glitch_effect(self)
